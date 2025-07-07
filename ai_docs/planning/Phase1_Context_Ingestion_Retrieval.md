# Phase 1: Context Ingestion and Retrieval Specifications
## Mobius Context Engineering Platform

### Document Version: 1.0
### Date: 2025-01-07
### Component: Core Context Processing System

---

## Executive Summary

This document provides detailed specifications for the context ingestion and retrieval system in Phase 1 of the Mobius platform. The system implements a simplified but robust pipeline for processing, storing, and retrieving code context using modern vector search technologies.

### Key Components
1. File ingestion with real-time monitoring
2. AST-based code parsing and analysis
3. Intelligent chunking strategies
4. Efficient embedding generation
5. Vector storage with Qdrant
6. High-performance retrieval system

---

## 1. File Ingestion System

### 1.1 Supported File Types

```python
# config/file_types.py
from enum import Enum
from typing import Dict, List

class FileType(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    MARKDOWN = "markdown"
    JSON = "json"

FILE_EXTENSIONS: Dict[FileType, List[str]] = {
    FileType.PYTHON: [".py", ".pyi"],
    FileType.JAVASCRIPT: [".js", ".jsx", ".mjs"],
    FileType.TYPESCRIPT: [".ts", ".tsx"],
    FileType.MARKDOWN: [".md", ".mdx"],
    FileType.JSON: [".json", ".jsonc"],
}

# Maximum file size for processing (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024
```

### 1.2 File Watcher Implementation

```python
# ingestion/file_watcher.py
import asyncio
from pathlib import Path
from typing import Set, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import logging

logger = logging.getLogger(__name__)

class CodeFileHandler(FileSystemEventHandler):
    """Handles file system events for code files"""
    
    def __init__(
        self,
        file_queue: asyncio.Queue,
        supported_extensions: Set[str]
    ):
        self.file_queue = file_queue
        self.supported_extensions = supported_extensions
        self._seen_files: Set[Path] = set()
        
    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._process_file(event.src_path)
            
    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._process_file(event.src_path)
            
    def _process_file(self, file_path: str) -> None:
        path = Path(file_path)
        
        # Check if file is supported
        if path.suffix not in self.supported_extensions:
            return
            
        # Check file size
        try:
            if path.stat().st_size > MAX_FILE_SIZE:
                logger.warning(f"File too large: {path}")
                return
        except OSError:
            return
            
        # Add to queue for processing
        asyncio.create_task(self.file_queue.put({
            'path': path,
            'action': 'index'
        }))

class FileWatcher:
    """Watches directories for file changes"""
    
    def __init__(self, ingestion_service: 'IngestionService'):
        self.ingestion_service = ingestion_service
        self.observer = Observer()
        self.file_queue = asyncio.Queue(maxsize=1000)
        
    async def start(self, watch_paths: List[Path]) -> None:
        """Start watching specified paths"""
        handler = CodeFileHandler(
            self.file_queue,
            self._get_supported_extensions()
        )
        
        for path in watch_paths:
            self.observer.schedule(
                handler,
                str(path),
                recursive=True
            )
            
        self.observer.start()
        
        # Start queue processor
        asyncio.create_task(self._process_queue())
        
    async def _process_queue(self) -> None:
        """Process files from the queue"""
        while True:
            try:
                file_info = await self.file_queue.get()
                await self.ingestion_service.ingest_file(
                    file_info['path']
                )
            except Exception as e:
                logger.error(f"Error processing file: {e}")
                
    def _get_supported_extensions(self) -> Set[str]:
        """Get all supported file extensions"""
        extensions = set()
        for ext_list in FILE_EXTENSIONS.values():
            extensions.update(ext_list)
        return extensions
```

### 1.3 Batch Processing Strategy

```python
# ingestion/batch_processor.py
from typing import List, Dict, Any
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Processes files in batches for efficiency"""
    
    def __init__(
        self,
        batch_size: int = 50,
        batch_timeout: float = 5.0
    ):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.current_batch: List[Path] = []
        self.batch_lock = asyncio.Lock()
        
    async def add_file(self, file_path: Path) -> None:
        """Add file to current batch"""
        async with self.batch_lock:
            self.current_batch.append(file_path)
            
            if len(self.current_batch) >= self.batch_size:
                await self._process_batch()
                
    async def _process_batch(self) -> None:
        """Process current batch of files"""
        if not self.current_batch:
            return
            
        batch = self.current_batch[:]
        self.current_batch = []
        
        try:
            # Process files in parallel
            tasks = [
                self._process_single_file(file_path)
                for file_path in batch
            ]
            
            results = await asyncio.gather(
                *tasks,
                return_exceptions=True
            )
            
            # Log results
            successful = sum(
                1 for r in results 
                if not isinstance(r, Exception)
            )
            logger.info(
                f"Batch processed: {successful}/{len(batch)} files"
            )
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            
    async def _process_single_file(self, file_path: Path) -> Dict:
        """Process a single file"""
        # Implementation in next sections
        pass
```

### 1.4 Error Handling and Retry Logic

```python
# ingestion/retry_handler.py
from typing import TypeVar, Callable, Any
import asyncio
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

def with_retry(config: RetryConfig = RetryConfig()):
    """Decorator for adding retry logic to async functions"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts - 1:
                        delay = min(
                            config.initial_delay * (
                                config.exponential_base ** attempt
                            ),
                            config.max_delay
                        )
                        
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/"
                            f"{config.max_attempts}): {e}. Retrying in {delay}s"
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after "
                            f"{config.max_attempts} attempts: {e}"
                        )
                        
            raise last_exception
            
        return wrapper
    return decorator
```

---

## 2. Code Parsing and Analysis

### 2.1 AST-Based Python Parsing

```python
# parsing/python_parser.py
import ast
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class FunctionInfo:
    name: str
    start_line: int
    end_line: int
    docstring: Optional[str]
    arguments: List[str]
    decorators: List[str]
    complexity: int

@dataclass
class ClassInfo:
    name: str
    start_line: int
    end_line: int
    docstring: Optional[str]
    methods: List[FunctionInfo]
    base_classes: List[str]

class PythonParser:
    """Parser for Python source code using AST"""
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse Python file and extract structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content, filename=str(file_path))
            
            return {
                'functions': self._extract_functions(tree),
                'classes': self._extract_classes(tree),
                'imports': self._extract_imports(tree),
                'globals': self._extract_globals(tree),
                'complexity': self._calculate_complexity(tree)
            }
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            raise
            
    def _extract_functions(self, tree: ast.AST) -> List[FunctionInfo]:
        """Extract function definitions"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(FunctionInfo(
                    name=node.name,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    docstring=ast.get_docstring(node),
                    arguments=[arg.arg for arg in node.args.args],
                    decorators=[
                        self._get_decorator_name(d) 
                        for d in node.decorator_list
                    ],
                    complexity=self._calculate_complexity(node)
                ))
                
        return functions
        
    def _extract_classes(self, tree: ast.AST) -> List[ClassInfo]:
        """Extract class definitions"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(FunctionInfo(
                            name=item.name,
                            start_line=item.lineno,
                            end_line=item.end_lineno or item.lineno,
                            docstring=ast.get_docstring(item),
                            arguments=[arg.arg for arg in item.args.args],
                            decorators=[
                                self._get_decorator_name(d)
                                for d in item.decorator_list
                            ],
                            complexity=self._calculate_complexity(item)
                        ))
                        
                classes.append(ClassInfo(
                    name=node.name,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    docstring=ast.get_docstring(node),
                    methods=methods,
                    base_classes=[
                        self._get_base_name(base)
                        for base in node.bases
                    ]
                ))
                
        return classes
        
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
                
        return complexity
```

### 2.2 TypeScript/JavaScript Parsing

```python
# parsing/typescript_parser.py
import tree_sitter
from tree_sitter import Language, Parser
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TypeScriptParser:
    """Parser for TypeScript/JavaScript using tree-sitter"""
    
    def __init__(self):
        # Initialize tree-sitter languages
        self.typescript_language = Language('build/languages.so', 'typescript')
        self.javascript_language = Language('build/languages.so', 'javascript')
        
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse TypeScript/JavaScript file"""
        parser = Parser()
        
        # Determine language
        if file_path.suffix in ['.ts', '.tsx']:
            parser.set_language(self.typescript_language)
        else:
            parser.set_language(self.javascript_language)
            
        with open(file_path, 'rb') as f:
            content = f.read()
            
        tree = parser.parse(content)
        
        return {
            'functions': self._extract_functions(tree, content),
            'classes': self._extract_classes(tree, content),
            'imports': self._extract_imports(tree, content),
            'exports': self._extract_exports(tree, content)
        }
        
    def _extract_functions(
        self, 
        tree: tree_sitter.Tree, 
        content: bytes
    ) -> List[Dict]:
        """Extract function declarations"""
        functions = []
        
        # Query for function declarations
        query = self.typescript_language.query("""
            (function_declaration
                name: (identifier) @name
                parameters: (formal_parameters) @params
                body: (statement_block) @body
            ) @function
            
            (arrow_function
                parameters: (formal_parameters) @params
                body: (_) @body
            ) @arrow
        """)
        
        captures = query.captures(tree.root_node)
        
        for capture in captures:
            node = capture[0]
            if capture[1] == 'function':
                functions.append({
                    'name': self._get_node_text(node.child_by_field_name('name'), content),
                    'start_line': node.start_point[0] + 1,
                    'end_line': node.end_point[0] + 1,
                    'type': 'function'
                })
                
        return functions
        
    def _get_node_text(self, node: tree_sitter.Node, content: bytes) -> str:
        """Extract text from a node"""
        if node:
            return content[node.start_byte:node.end_byte].decode('utf-8')
        return ""
```

---

## 3. Chunking Strategies

### 3.1 Code Chunking

```python
# chunking/code_chunker.py
from typing import List, Dict, Any
from dataclasses import dataclass
import tiktoken

@dataclass
class CodeChunk:
    content: str
    start_line: int
    end_line: int
    chunk_type: str  # 'function', 'class', 'module'
    metadata: Dict[str, Any]
    token_count: int

class CodeChunker:
    """Intelligent code chunking based on AST"""
    
    def __init__(
        self,
        max_chunk_size: int = 512,
        overlap_size: int = 50,
        min_chunk_size: int = 100
    ):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        self.encoder = tiktoken.get_encoding("cl100k_base")
        
    def chunk_code(
        self,
        content: str,
        parse_result: Dict[str, Any],
        file_path: Path
    ) -> List[CodeChunk]:
        """Create chunks from parsed code"""
        chunks = []
        lines = content.split('\n')
        
        # Process functions
        for func in parse_result.get('functions', []):
            chunk = self._create_function_chunk(
                lines, 
                func, 
                file_path
            )
            if chunk:
                chunks.append(chunk)
                
        # Process classes
        for cls in parse_result.get('classes', []):
            chunk = self._create_class_chunk(
                lines,
                cls,
                file_path
            )
            if chunk:
                chunks.append(chunk)
                
        # Handle remaining code
        chunks.extend(
            self._create_module_chunks(
                lines,
                chunks,
                file_path
            )
        )
        
        return chunks
        
    def _create_function_chunk(
        self,
        lines: List[str],
        func_info: FunctionInfo,
        file_path: Path
    ) -> Optional[CodeChunk]:
        """Create chunk for a function"""
        # Extract function lines
        start = func_info.start_line - 1
        end = func_info.end_line
        
        function_lines = lines[start:end]
        content = '\n'.join(function_lines)
        
        # Check token count
        tokens = self.encoder.encode(content)
        
        if len(tokens) <= self.max_chunk_size:
            return CodeChunk(
                content=content,
                start_line=func_info.start_line,
                end_line=func_info.end_line,
                chunk_type='function',
                metadata={
                    'name': func_info.name,
                    'file': str(file_path),
                    'language': 'python',
                    'docstring': func_info.docstring,
                    'complexity': func_info.complexity
                },
                token_count=len(tokens)
            )
        else:
            # Split large functions
            return self._split_large_function(
                function_lines,
                func_info,
                file_path
            )
            
    def _split_large_function(
        self,
        lines: List[str],
        func_info: FunctionInfo,
        file_path: Path
    ) -> List[CodeChunk]:
        """Split large functions into smaller chunks"""
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for i, line in enumerate(lines):
            line_tokens = len(self.encoder.encode(line))
            
            if current_tokens + line_tokens > self.max_chunk_size:
                # Create chunk
                if current_chunk:
                    chunks.append(self._finalize_chunk(
                        current_chunk,
                        func_info.start_line + i - len(current_chunk),
                        func_info.start_line + i - 1,
                        'function_part',
                        {
                            'name': func_info.name,
                            'file': str(file_path),
                            'part': len(chunks) + 1
                        }
                    ))
                    
                # Add overlap
                overlap_start = max(0, len(current_chunk) - self.overlap_size)
                current_chunk = current_chunk[overlap_start:]
                current_tokens = sum(
                    len(self.encoder.encode(l)) 
                    for l in current_chunk
                )
                
            current_chunk.append(line)
            current_tokens += line_tokens
            
        # Final chunk
        if current_chunk:
            chunks.append(self._finalize_chunk(
                current_chunk,
                func_info.end_line - len(current_chunk) + 1,
                func_info.end_line,
                'function_part',
                {
                    'name': func_info.name,
                    'file': str(file_path),
                    'part': len(chunks) + 1
                }
            ))
            
        return chunks
```

### 3.2 Documentation Chunking

```python
# chunking/doc_chunker.py
import re
from typing import List
from dataclasses import dataclass

@dataclass
class DocChunk:
    content: str
    start_pos: int
    end_pos: int
    chunk_type: str  # 'heading', 'paragraph', 'code_block'
    metadata: Dict[str, Any]
    token_count: int

class DocumentationChunker:
    """Chunker for markdown documentation"""
    
    def __init__(
        self,
        max_chunk_size: int = 512,
        overlap_size: int = 50
    ):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.encoder = tiktoken.get_encoding("cl100k_base")
        
    def chunk_markdown(
        self,
        content: str,
        file_path: Path
    ) -> List[DocChunk]:
        """Chunk markdown content"""
        chunks = []
        
        # Parse markdown structure
        sections = self._parse_markdown_sections(content)
        
        for section in sections:
            # Check if section fits in one chunk
            tokens = self.encoder.encode(section['content'])
            
            if len(tokens) <= self.max_chunk_size:
                chunks.append(DocChunk(
                    content=section['content'],
                    start_pos=section['start'],
                    end_pos=section['end'],
                    chunk_type=section['type'],
                    metadata={
                        'file': str(file_path),
                        'heading': section.get('heading', ''),
                        'level': section.get('level', 0)
                    },
                    token_count=len(tokens)
                ))
            else:
                # Split large sections
                chunks.extend(
                    self._split_large_section(section, file_path)
                )
                
        return chunks
        
    def _parse_markdown_sections(
        self, 
        content: str
    ) -> List[Dict[str, Any]]:
        """Parse markdown into sections"""
        sections = []
        
        # Regex patterns
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        code_block_pattern = re.compile(r'```[\s\S]*?```', re.MULTILINE)
        
        # Find all headings
        headings = list(heading_pattern.finditer(content))
        
        # Process sections between headings
        for i, match in enumerate(headings):
            start = match.start()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(content)
            
            section_content = content[start:end].strip()
            
            sections.append({
                'content': section_content,
                'start': start,
                'end': end,
                'type': 'heading',
                'heading': match.group(2),
                'level': len(match.group(1))
            })
            
        return sections
```

---

## 4. Embedding Generation

### 4.1 OpenAI Integration

```python
# embeddings/openai_embedder.py
from typing import List, Dict, Any
import openai
from openai import AsyncOpenAI
import asyncio
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class OpenAIEmbedder:
    """Generate embeddings using OpenAI API"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        max_retries: int = 3
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                embeddings = [
                    item.embedding 
                    for item in response.data
                ]
                all_embeddings.extend(embeddings)
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                raise
                
        return all_embeddings
        
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]
```

### 4.2 Embedding Cache

```python
# embeddings/embedding_cache.py
import hashlib
import json
from typing import Optional, List
import redis.asyncio as redis
import numpy as np

class EmbeddingCache:
    """Cache for embeddings to reduce API calls"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "embedding:"
        self.ttl = 86400 * 7  # 7 days
        
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text"""
        content = f"{model}:{text}"
        hash_digest = hashlib.sha256(
            content.encode()
        ).hexdigest()
        return f"{self.prefix}{hash_digest}"
        
    async def get(
        self, 
        text: str, 
        model: str
    ) -> Optional[List[float]]:
        """Get embedding from cache"""
        key = self._get_cache_key(text, model)
        
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
            
        return None
        
    async def set(
        self,
        text: str,
        model: str,
        embedding: List[float]
    ) -> None:
        """Store embedding in cache"""
        key = self._get_cache_key(text, model)
        
        await self.redis.setex(
            key,
            self.ttl,
            json.dumps(embedding)
        )
        
    async def get_batch(
        self,
        texts: List[str],
        model: str
    ) -> Dict[str, Optional[List[float]]]:
        """Get multiple embeddings from cache"""
        keys = [
            self._get_cache_key(text, model)
            for text in texts
        ]
        
        values = await self.redis.mget(keys)
        
        result = {}
        for text, value in zip(texts, values):
            if value:
                result[text] = json.loads(value)
            else:
                result[text] = None
                
        return result
```

---

## 5. Vector Storage with Qdrant

### 5.1 Collection Schema

```python
# storage/qdrant_schema.py
from qdrant_client import models
from typing import Dict, Any

class QdrantSchema:
    """Schema definitions for Qdrant collections"""
    
    @staticmethod
    def get_code_collection_config() -> Dict[str, Any]:
        """Configuration for code collection"""
        return {
            "vectors_config": models.VectorParams(
                size=1536,  # OpenAI embedding dimension
                distance=models.Distance.COSINE
            ),
            "optimizers_config": models.OptimizersConfigDiff(
                indexing_threshold=20000,
                memmap_threshold=50000
            ),
            "quantization_config": models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8,
                    quantile=0.99,
                    always_ram=True
                )
            )
        }
        
    @staticmethod
    def get_payload_schema() -> Dict[str, Any]:
        """Schema for payload fields"""
        return {
            "file_path": "keyword",
            "chunk_type": "keyword",
            "language": "keyword",
            "start_line": "integer",
            "end_line": "integer",
            "function_name": "keyword",
            "class_name": "keyword",
            "complexity": "integer",
            "token_count": "integer",
            "timestamp": "datetime"
        }
```

### 5.2 Qdrant Client Implementation

```python
# storage/qdrant_client.py
from qdrant_client import AsyncQdrantClient, models
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    """Async Qdrant vector store implementation"""
    
    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: Optional[str] = None,
        collection_name: str = "code_context"
    ):
        self.client = AsyncQdrantClient(
            url=url,
            api_key=api_key
        )
        self.collection_name = collection_name
        
    async def initialize(self) -> None:
        """Initialize collection if not exists"""
        collections = await self.client.get_collections()
        
        if self.collection_name not in [
            c.name for c in collections.collections
        ]:
            await self.create_collection()
            
    async def create_collection(self) -> None:
        """Create collection with schema"""
        schema = QdrantSchema()
        
        await self.client.create_collection(
            collection_name=self.collection_name,
            **schema.get_code_collection_config()
        )
        
        logger.info(f"Created collection: {self.collection_name}")
        
    async def upsert_chunks(
        self,
        chunks: List[CodeChunk],
        embeddings: List[List[float]]
    ) -> None:
        """Upsert chunks with embeddings"""
        points = []
        
        for chunk, embedding in zip(chunks, embeddings):
            point_id = str(uuid.uuid4())
            
            payload = {
                "content": chunk.content,
                "file_path": chunk.metadata.get("file", ""),
                "chunk_type": chunk.chunk_type,
                "language": chunk.metadata.get("language", ""),
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "function_name": chunk.metadata.get("name", ""),
                "complexity": chunk.metadata.get("complexity", 0),
                "token_count": chunk.token_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            points.append(models.PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            ))
            
        # Batch upsert
        await self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )
        
        logger.info(f"Upserted {len(points)} chunks")
        
    async def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        filters: Optional[models.Filter] = None
    ) -> List[models.ScoredPoint]:
        """Search for similar chunks"""
        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=filters
        )
        
        return results
```

---

## 6. Retrieval System

### 6.1 Query Processing

```python
# retrieval/query_processor.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

@dataclass
class ProcessedQuery:
    text: str
    intent: str  # 'code_search', 'documentation', 'debug'
    filters: Dict[str, Any]
    boost_terms: List[str]

class QueryProcessor:
    """Process and enhance search queries"""
    
    def __init__(self):
        self.intent_patterns = {
            'code_search': [
                r'function\s+(\w+)',
                r'class\s+(\w+)',
                r'method\s+(\w+)',
                r'implement\s+(\w+)'
            ],
            'documentation': [
                r'how\s+to',
                r'what\s+is',
                r'explain',
                r'documentation'
            ],
            'debug': [
                r'error',
                r'bug',
                r'fix',
                r'issue'
            ]
        }
        
    def process_query(self, query: str) -> ProcessedQuery:
        """Process raw query into structured format"""
        # Detect intent
        intent = self._detect_intent(query)
        
        # Extract filters
        filters = self._extract_filters(query)
        
        # Identify boost terms
        boost_terms = self._extract_boost_terms(query)
        
        # Clean query
        cleaned_query = self._clean_query(query)
        
        return ProcessedQuery(
            text=cleaned_query,
            intent=intent,
            filters=filters,
            boost_terms=boost_terms
        )
        
    def _detect_intent(self, query: str) -> str:
        """Detect query intent"""
        query_lower = query.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
                    
        return 'code_search'  # default
        
    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract filter conditions from query"""
        filters = {}
        
        # Language filter
        lang_match = re.search(
            r'lang:(\w+)|language:(\w+)',
            query,
            re.IGNORECASE
        )
        if lang_match:
            filters['language'] = (
                lang_match.group(1) or lang_match.group(2)
            ).lower()
            
        # File filter
        file_match = re.search(
            r'file:([^\s]+)',
            query,
            re.IGNORECASE
        )
        if file_match:
            filters['file_path'] = file_match.group(1)
            
        return filters
```

### 6.2 Semantic Search Implementation

```python
# retrieval/semantic_search.py
from typing import List, Dict, Any, Optional
from qdrant_client import models
import logging

logger = logging.getLogger(__name__)

class SemanticSearch:
    """Semantic search implementation"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedder: OpenAIEmbedder,
        query_processor: QueryProcessor
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.query_processor = query_processor
        
    async def search(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search"""
        # Process query
        processed = self.query_processor.process_query(query)
        
        # Generate query embedding
        query_embedding = await self.embedder.generate_embedding(
            processed.text
        )
        
        # Build filters
        qdrant_filters = self._build_filters(
            processed.filters,
            filters
        )
        
        # Search
        results = await self.vector_store.search(
            query_vector=query_embedding,
            limit=limit * 2,  # Get more for re-ranking
            filters=qdrant_filters
        )
        
        # Re-rank results
        ranked_results = self._rerank_results(
            results,
            processed,
            limit
        )
        
        return self._format_results(ranked_results)
        
    def _build_filters(
        self,
        query_filters: Dict[str, Any],
        additional_filters: Optional[Dict[str, Any]]
    ) -> Optional[models.Filter]:
        """Build Qdrant filters"""
        conditions = []
        
        # Merge filters
        all_filters = {**query_filters}
        if additional_filters:
            all_filters.update(additional_filters)
            
        # Build conditions
        for key, value in all_filters.items():
            if key == 'language':
                conditions.append(
                    models.FieldCondition(
                        key='language',
                        match=models.MatchValue(value=value)
                    )
                )
            elif key == 'file_path':
                conditions.append(
                    models.FieldCondition(
                        key='file_path',
                        match=models.MatchText(text=value)
                    )
                )
                
        if conditions:
            return models.Filter(must=conditions)
            
        return None
        
    def _rerank_results(
        self,
        results: List[models.ScoredPoint],
        query: ProcessedQuery,
        limit: int
    ) -> List[models.ScoredPoint]:
        """Re-rank results based on additional factors"""
        scored_results = []
        
        for result in results:
            score = result.score
            
            # Boost by intent match
            if query.intent == 'code_search':
                if result.payload.get('chunk_type') == 'function':
                    score *= 1.2
            elif query.intent == 'documentation':
                if result.payload.get('chunk_type') == 'heading':
                    score *= 1.1
                    
            # Boost by term matches
            content = result.payload.get('content', '').lower()
            for term in query.boost_terms:
                if term.lower() in content:
                    score *= 1.05
                    
            scored_results.append((score, result))
            
        # Sort by score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return [r[1] for r in scored_results[:limit]]
```

### 6.3 Result Formatting

```python
# retrieval/result_formatter.py
from typing import List, Dict, Any
from qdrant_client import models

class ResultFormatter:
    """Format search results for API response"""
    
    def format_results(
        self,
        results: List[models.ScoredPoint]
    ) -> List[Dict[str, Any]]:
        """Format search results"""
        formatted = []
        
        for result in results:
            formatted.append({
                'id': result.id,
                'score': result.score,
                'content': result.payload.get('content', ''),
                'metadata': {
                    'file_path': result.payload.get('file_path', ''),
                    'chunk_type': result.payload.get('chunk_type', ''),
                    'language': result.payload.get('language', ''),
                    'lines': {
                        'start': result.payload.get('start_line', 0),
                        'end': result.payload.get('end_line', 0)
                    },
                    'function_name': result.payload.get('function_name', ''),
                    'complexity': result.payload.get('complexity', 0)
                },
                'timestamp': result.payload.get('timestamp', '')
            })
            
        return formatted
```

---

## 7. Complete Pipeline Integration

### 7.1 Ingestion Service

```python
# services/ingestion_service.py
from typing import List, Dict, Any
import asyncio
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class IngestionService:
    """Complete ingestion pipeline service"""
    
    def __init__(
        self,
        parser_factory: ParserFactory,
        chunker_factory: ChunkerFactory,
        embedder: OpenAIEmbedder,
        vector_store: VectorStore,
        embedding_cache: EmbeddingCache
    ):
        self.parser_factory = parser_factory
        self.chunker_factory = chunker_factory
        self.embedder = embedder
        self.vector_store = vector_store
        self.embedding_cache = embedding_cache
        
    async def ingest_file(self, file_path: Path) -> Dict[str, Any]:
        """Ingest a single file"""
        try:
            # Parse file
            parser = self.parser_factory.get_parser(file_path)
            parse_result = await parser.parse_file(file_path)
            
            # Read content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Create chunks
            chunker = self.chunker_factory.get_chunker(file_path)
            chunks = chunker.chunk_content(
                content,
                parse_result,
                file_path
            )
            
            # Generate embeddings
            embeddings = await self._generate_embeddings_with_cache(
                chunks
            )
            
            # Store in vector database
            await self.vector_store.upsert_chunks(
                chunks,
                embeddings
            )
            
            return {
                'status': 'success',
                'file': str(file_path),
                'chunks_created': len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error ingesting {file_path}: {e}")
            return {
                'status': 'error',
                'file': str(file_path),
                'error': str(e)
            }
            
    async def _generate_embeddings_with_cache(
        self,
        chunks: List[CodeChunk]
    ) -> List[List[float]]:
        """Generate embeddings with caching"""
        embeddings = []
        uncached_chunks = []
        uncached_indices = []
        
        # Check cache
        for i, chunk in enumerate(chunks):
            cached = await self.embedding_cache.get(
                chunk.content,
                self.embedder.model
            )
            
            if cached:
                embeddings.append(cached)
            else:
                embeddings.append(None)
                uncached_chunks.append(chunk.content)
                uncached_indices.append(i)
                
        # Generate missing embeddings
        if uncached_chunks:
            new_embeddings = await self.embedder.generate_embeddings(
                uncached_chunks
            )
            
            # Update results and cache
            for idx, embedding in zip(uncached_indices, new_embeddings):
                embeddings[idx] = embedding
                
                # Cache embedding
                await self.embedding_cache.set(
                    chunks[idx].content,
                    self.embedder.model,
                    embedding
                )
                
        return embeddings
```

### 7.2 Retrieval Service

```python
# services/retrieval_service.py
class RetrievalService:
    """Complete retrieval pipeline service"""
    
    def __init__(
        self,
        semantic_search: SemanticSearch,
        result_formatter: ResultFormatter
    ):
        self.semantic_search = semantic_search
        self.result_formatter = result_formatter
        
    async def retrieve_context(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Retrieve relevant context"""
        try:
            # Perform search
            results = await self.semantic_search.search(
                query,
                limit,
                filters
            )
            
            # Format results
            formatted = self.result_formatter.format_results(results)
            
            return {
                'status': 'success',
                'query': query,
                'results': formatted,
                'total': len(formatted)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return {
                'status': 'error',
                'query': query,
                'error': str(e)
            }
```

---

## 8. Performance Optimization

### 8.1 Caching Strategy

```python
# optimization/cache_strategy.py
from functools import lru_cache
import hashlib

class CacheStrategy:
    """Multi-level caching strategy"""
    
    def __init__(self):
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0
        }
        
    @lru_cache(maxsize=1000)
    def get_cached_embedding(
        self,
        text_hash: str
    ) -> Optional[List[float]]:
        """Get embedding from memory cache"""
        return self.memory_cache.get(text_hash)
```

### 8.2 Batch Processing Optimization

```python
# optimization/batch_optimizer.py
class BatchOptimizer:
    """Optimize batch processing"""
    
    def __init__(self):
        self.optimal_batch_size = 50
        
    async def optimize_batch_size(
        self,
        total_items: int,
        processing_time: float
    ) -> int:
        """Dynamically adjust batch size"""
        if processing_time > 5.0:
            self.optimal_batch_size = max(
                10,
                self.optimal_batch_size - 10
            )
        elif processing_time < 2.0:
            self.optimal_batch_size = min(
                100,
                self.optimal_batch_size + 10
            )
            
        return self.optimal_batch_size
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/test_ingestion.py
import pytest
from pathlib import Path

@pytest.mark.asyncio
async def test_python_parsing():
    """Test Python file parsing"""
    parser = PythonParser()
    
    test_file = Path("test_data/sample.py")
    result = await parser.parse_file(test_file)
    
    assert 'functions' in result
    assert 'classes' in result
    assert len(result['functions']) > 0

@pytest.mark.asyncio
async def test_embedding_generation():
    """Test embedding generation"""
    embedder = OpenAIEmbedder(api_key="test")
    
    # Mock API call
    with mock.patch('openai.AsyncOpenAI.embeddings.create'):
        embeddings = await embedder.generate_embeddings(
            ["test text"]
        )
        
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 1536
```

### 9.2 Integration Tests

```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_full_ingestion_pipeline():
    """Test complete ingestion pipeline"""
    service = IngestionService(
        parser_factory,
        chunker_factory,
        embedder,
        vector_store,
        cache
    )
    
    result = await service.ingest_file(
        Path("test_data/sample.py")
    )
    
    assert result['status'] == 'success'
    assert result['chunks_created'] > 0
```

---

## Conclusion

This specification provides a comprehensive foundation for the context ingestion and retrieval system in Phase 1. The design emphasizes:

1. **Modularity**: Each component is independently testable and replaceable
2. **Performance**: Async operations, batching, and caching throughout
3. **Reliability**: Comprehensive error handling and retry logic
4. **Scalability**: Designed to handle large codebases efficiently
5. **Extensibility**: Easy to add new file types and parsing strategies

The system meets the Phase 1 requirements while providing a solid foundation for future enhancements in subsequent phases.