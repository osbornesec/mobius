# Phase 1: LLM Connections Specification
## Mobius Context Engineering Platform

### Document Version: 1.0
### Date: 2025-01-07
### Component: LLM Provider Integration

---

## Executive Summary

This document provides comprehensive specifications for integrating Large Language Model (LLM) providers in Phase 1 of the Mobius platform. The implementation focuses on OpenAI and Anthropic integrations with a robust abstraction layer that enables future provider additions and ensures reliability through proper error handling, rate limiting, and fallback mechanisms.

### Key Features
1. Unified provider abstraction layer
2. Async-first implementation with streaming support
3. Comprehensive error handling and retry logic
4. Cost tracking and monitoring
5. Performance optimization through caching and pooling

---

## 1. LLM Provider Architecture

### 1.1 System Overview

```python
# Architecture diagram in code
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional
from pydantic import BaseModel

# Core abstraction layer
class LLMProvider(ABC):
    """Base interface for all LLM providers"""

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        model: str,
        **kwargs
    ) -> CompletionResponse:
        """Generate completion from messages"""
        pass

    @abstractmethod
    async def stream_complete(
        self,
        messages: List[Message],
        model: str,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion chunks"""
        pass

    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings for texts"""
        pass

### 1.2 Configuration Management

```python
# config/llm_config.py
from pydantic import BaseModel, SecretStr, Field
from typing import Dict, Optional, Literal
from enum import Enum

class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class RetryConfig(BaseModel):
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

class ProviderConfig(BaseModel):
    provider_type: ProviderType
    api_key: SecretStr
    base_url: Optional[str] = None
    timeout: float = 30.0
    max_concurrent_requests: int = 10
    retry_config: RetryConfig = Field(default_factory=RetryConfig)

class LLMConfig(BaseModel):
    """Global LLM configuration"""
    providers: Dict[str, ProviderConfig]
    default_provider: str
    fallback_providers: List[str] = []
    cache_ttl: int = 3600  # seconds
    enable_cost_tracking: bool = True
    enable_request_logging: bool = True
```

### 1.3 Provider Factory Pattern

```python
# providers/factory.py
from typing import Dict, Type
import asyncio
from contextlib import asynccontextmanager

class LLMProviderFactory:
    """Factory for creating and managing LLM provider instances"""

    _providers: Dict[ProviderType, Type[LLMProvider]] = {}
    _instances: Dict[str, LLMProvider] = {}
    _locks: Dict[str, asyncio.Lock] = {}

    @classmethod
    def register_provider(
        cls,
        provider_type: ProviderType,
        provider_class: Type[LLMProvider]
    ) -> None:
        """Register a new provider implementation"""
        cls._providers[provider_type] = provider_class

    @classmethod
    async def get_provider(
        cls,
        provider_name: str,
        config: LLMConfig
    ) -> LLMProvider:
        """Get or create a provider instance"""
        if provider_name not in cls._instances:
            if provider_name not in cls._locks:
                cls._locks[provider_name] = asyncio.Lock()

            async with cls._locks[provider_name]:
                if provider_name not in cls._instances:
                    provider_config = config.providers[provider_name]
                    provider_class = cls._providers[provider_config.provider_type]
                    cls._instances[provider_name] = await provider_class.create(
                        provider_config
                    )

        return cls._instances[provider_name]
```

---

## 2. OpenAI Integration

### 2.1 Implementation Details

```python
# providers/openai_provider.py
import openai
from openai import AsyncOpenAI
from typing import AsyncIterator, List, Optional
import tiktoken
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation"""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key.get_secret_value(),
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=0  # We handle retries ourselves
        )
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        self._encoder = tiktoken.get_encoding("cl100k_base")

    @classmethod
    async def create(cls, config: ProviderConfig) -> "OpenAIProvider":
        """Factory method for async initialization"""
        instance = cls(config)
        await instance._verify_connection()
        return instance

    async def _verify_connection(self) -> None:
        """Verify API connection on initialization"""
        try:
            await self.client.models.list()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to OpenAI API: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type(openai.RateLimitError)
    )
    async def complete(
        self,
        messages: List[Message],
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> CompletionResponse:
        """Generate completion with retry logic"""
        async with self._semaphore:
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[m.model_dump() for m in messages],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

                return CompletionResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    usage=Usage(
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        total_tokens=response.usage.total_tokens
                    ),
                    provider="openai",
                    raw_response=response.model_dump()
                )

            except openai.APIError as e:
                raise LLMProviderError(
                    f"OpenAI API error: {e}",
                    provider="openai",
                    error_code=e.code,
                    retry_after=getattr(e, "retry_after", None)
                )

    async def stream_complete(
        self,
        messages: List[Message],
        model: str = "gpt-4",
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion responses"""
        async with self._semaphore:
            try:
                stream = await self.client.chat.completions.create(
                    model=model,
                    messages=[m.model_dump() for m in messages],
                    temperature=temperature,
                    stream=True,
                    **kwargs
                )

                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield StreamChunk(
                            content=chunk.choices[0].delta.content,
                            provider="openai",
                            model=model,
                            finish_reason=chunk.choices[0].finish_reason
                        )

            except openai.APIError as e:
                raise LLMProviderError(
                    f"OpenAI streaming error: {e}",
                    provider="openai"
                )

    async def embed(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        """Generate embeddings with batching"""
        async with self._semaphore:
            try:
                # OpenAI recommends max 2048 embedding inputs per request
                batch_size = 100
                embeddings = []

                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    response = await self.client.embeddings.create(
                        model=model,
                        input=batch
                    )
                    embeddings.extend(
                        [e.embedding for e in response.data]
                    )

                return embeddings

            except openai.APIError as e:
                raise LLMProviderError(
                    f"OpenAI embedding error: {e}",
                    provider="openai"
                )
```

### 2.2 Supported Models and Pricing

```python
# models/openai_models.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class ModelInfo:
    name: str
    context_window: int
    input_cost: float  # per 1M tokens
    output_cost: float  # per 1M tokens
    supports_functions: bool = True
    supports_vision: bool = False

OPENAI_MODELS: Dict[str, ModelInfo] = {
    "gpt-4": ModelInfo(
        name="gpt-4",
        context_window=8192,
        input_cost=30.0,
        output_cost=60.0,
        supports_functions=True
    ),
    "gpt-4-turbo": ModelInfo(
        name="gpt-4-turbo",
        context_window=128000,
        input_cost=10.0,
        output_cost=30.0,
        supports_functions=True
    ),
    "gpt-3.5-turbo": ModelInfo(
        name="gpt-3.5-turbo",
        context_window=16385,
        input_cost=0.5,
        output_cost=1.5,
        supports_functions=True
    ),
    "text-embedding-3-small": ModelInfo(
        name="text-embedding-3-small",
        context_window=8191,
        input_cost=0.02,
        output_cost=0.0,
        supports_functions=False
    )
}
```

---

## 3. Anthropic Integration

### 3.1 Implementation Details

```python
# providers/anthropic_provider.py
import anthropic
from anthropic import AsyncAnthropic
from typing import AsyncIterator, List, Optional
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

class AnthropicProvider(LLMProvider):
    """Anthropic (Claude) LLM provider implementation"""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.client = AsyncAnthropic(
            api_key=config.api_key.get_secret_value(),
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=0  # Handle retries ourselves
        )
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)

    @classmethod
    async def create(cls, config: ProviderConfig) -> "AnthropicProvider":
        """Factory method for async initialization"""
        instance = cls(config)
        await instance._verify_connection()
        return instance

    async def _verify_connection(self) -> None:
        """Verify API connection"""
        try:
            # Simple test to verify API key
            await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
        except anthropic.AuthenticationError:
            raise ConnectionError("Invalid Anthropic API key")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Anthropic API: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type(anthropic.RateLimitError)
    )
    async def complete(
        self,
        messages: List[Message],
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> CompletionResponse:
        """Generate completion with retry logic"""
        async with self._semaphore:
            try:
                # Convert messages to Anthropic format
                anthropic_messages = self._convert_messages(messages)

                response = await self.client.messages.create(
                    model=model,
                    messages=anthropic_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

                return CompletionResponse(
                    content=response.content[0].text,
                    model=response.model,
                    usage=Usage(
                        prompt_tokens=response.usage.input_tokens,
                        completion_tokens=response.usage.output_tokens,
                        total_tokens=(
                            response.usage.input_tokens +
                            response.usage.output_tokens
                        )
                    ),
                    provider="anthropic",
                    raw_response=response.model_dump()
                )

            except anthropic.APIError as e:
                raise LLMProviderError(
                    f"Anthropic API error: {e}",
                    provider="anthropic",
                    error_code=getattr(e, "status_code", None),
                    retry_after=getattr(e, "retry_after", None)
                )

    async def stream_complete(
        self,
        messages: List[Message],
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion responses"""
        async with self._semaphore:
            try:
                anthropic_messages = self._convert_messages(messages)

                async with self.client.messages.stream(
                    model=model,
                    messages=anthropic_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                ) as stream:
                    async for text in stream.text_stream:
                        yield StreamChunk(
                            content=text,
                            provider="anthropic",
                            model=model,
                            finish_reason=None
                        )

                    # Get final message for metadata
                    final_message = await stream.get_final_message()
                    if final_message.stop_reason:
                        yield StreamChunk(
                            content="",
                            provider="anthropic",
                            model=model,
                            finish_reason=final_message.stop_reason
                        )

            except anthropic.APIError as e:
                raise LLMProviderError(
                    f"Anthropic streaming error: {e}",
                    provider="anthropic"
                )

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Anthropic doesn't provide embeddings - raise error"""
        raise NotImplementedError(
            "Anthropic does not provide embedding models. "
            "Use OpenAI or another provider for embeddings."
        )

    def _convert_messages(self, messages: List[Message]) -> List[Dict]:
        """Convert generic messages to Anthropic format"""
        # Anthropic requires alternating user/assistant messages
        anthropic_messages = []

        for msg in messages:
            if msg.role == "system":
                # Anthropic doesn't have system role - prepend to first user message
                if anthropic_messages and anthropic_messages[0]["role"] == "user":
                    anthropic_messages[0]["content"] = (
                        f"{msg.content}\n\n{anthropic_messages[0]['content']}"
                    )
                else:
                    anthropic_messages.insert(0, {
                        "role": "user",
                        "content": msg.content
                    })
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        return anthropic_messages
```

### 3.2 Supported Models and Pricing

```python
# models/anthropic_models.py
ANTHROPIC_MODELS: Dict[str, ModelInfo] = {
    "claude-3-opus-20240229": ModelInfo(
        name="claude-3-opus-20240229",
        context_window=200000,
        input_cost=15.0,
        output_cost=75.0,
        supports_functions=False,
        supports_vision=True
    ),
    "claude-3-sonnet-20240229": ModelInfo(
        name="claude-3-sonnet-20240229",
        context_window=200000,
        input_cost=3.0,
        output_cost=15.0,
        supports_functions=False,
        supports_vision=True
    ),
    "claude-3-haiku-20240307": ModelInfo(
        name="claude-3-haiku-20240307",
        context_window=200000,
        input_cost=0.25,
        output_cost=1.25,
        supports_functions=False,
        supports_vision=True
    )
}
```

---

## 4. Provider Abstraction Layer

### 4.1 Common Data Models

```python
# models/common.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    role: MessageRole
    content: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @property
    def estimated_cost(self) -> float:
        """Calculate estimated cost based on model pricing"""
        # Implementation depends on model tracking
        return 0.0

class CompletionResponse(BaseModel):
    content: str
    model: str
    provider: str
    usage: Usage
    created_at: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: Optional[float] = None
    raw_response: Optional[Dict[str, Any]] = None

class StreamChunk(BaseModel):
    content: str
    provider: str
    model: str
    finish_reason: Optional[str] = None

class LLMProviderError(Exception):
    """Base exception for LLM provider errors"""
    def __init__(
        self,
        message: str,
        provider: str,
        error_code: Optional[str] = None,
        retry_after: Optional[int] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.retry_after = retry_after
```

### 4.2 Provider Manager

```python
# services/llm_manager.py
from typing import Optional, List, AsyncIterator
import asyncio
import time
from contextlib import asynccontextmanager

class LLMManager:
    """Manages LLM providers with fallback and load balancing"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._provider_factory = LLMProviderFactory()
        self._cache = ResponseCache(ttl=config.cache_ttl)
        self._metrics = MetricsCollector()

    async def initialize(self) -> None:
        """Initialize all configured providers"""
        # Register provider implementations
        self._provider_factory.register_provider(
            ProviderType.OPENAI,
            OpenAIProvider
        )
        self._provider_factory.register_provider(
            ProviderType.ANTHROPIC,
            AnthropicProvider
        )

        # Pre-initialize providers
        for provider_name in self.config.providers:
            try:
                await self._provider_factory.get_provider(
                    provider_name,
                    self.config
                )
            except Exception as e:
                logger.error(
                    f"Failed to initialize provider {provider_name}: {e}"
                )

    async def complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> CompletionResponse:
        """Generate completion with automatic fallback"""
        start_time = time.time()

        # Check cache first
        cache_key = self._generate_cache_key(messages, model, provider, kwargs)
        cached_response = await self._cache.get(cache_key)
        if cached_response:
            self._metrics.record_cache_hit()
            return cached_response

        # Determine provider order
        providers = self._get_provider_order(provider)

        last_error = None
        for provider_name in providers:
            try:
                provider_instance = await self._provider_factory.get_provider(
                    provider_name,
                    self.config
                )

                # Use provider-specific model if not specified
                actual_model = model or self._get_default_model(provider_name)

                response = await provider_instance.complete(
                    messages,
                    actual_model,
                    **kwargs
                )

                # Record metrics
                response.response_time_ms = (time.time() - start_time) * 1000
                self._metrics.record_request(
                    provider=provider_name,
                    model=actual_model,
                    response_time=response.response_time_ms,
                    tokens=response.usage.total_tokens
                )

                # Cache successful response
                await self._cache.set(cache_key, response)

                return response

            except LLMProviderError as e:
                last_error = e
                logger.warning(
                    f"Provider {provider_name} failed: {e}. "
                    f"Trying next provider..."
                )

                # Handle rate limits
                if e.retry_after:
                    await asyncio.sleep(e.retry_after)

        # All providers failed
        raise LLMProviderError(
            f"All providers failed. Last error: {last_error}",
            provider="all",
            error_code="all_providers_failed"
        )

    @asynccontextmanager
    async def stream_complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion with automatic fallback"""
        providers = self._get_provider_order(provider)

        for provider_name in providers:
            try:
                provider_instance = await self._provider_factory.get_provider(
                    provider_name,
                    self.config
                )

                actual_model = model or self._get_default_model(provider_name)

                async for chunk in provider_instance.stream_complete(
                    messages,
                    actual_model,
                    **kwargs
                ):
                    yield chunk

                return  # Success

            except LLMProviderError as e:
                logger.warning(
                    f"Streaming provider {provider_name} failed: {e}"
                )
                continue

        raise LLMProviderError(
            "All streaming providers failed",
            provider="all"
        )

    def _get_provider_order(self, preferred: Optional[str]) -> List[str]:
        """Get provider order with fallbacks"""
        if preferred and preferred in self.config.providers:
            # Preferred provider first, then fallbacks
            return [preferred] + [
                p for p in self.config.fallback_providers
                if p != preferred
            ]
        else:
            # Default provider and fallbacks
            return [
                self.config.default_provider
            ] + self.config.fallback_providers

    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider"""
        provider_config = self.config.providers[provider]
        if provider_config.provider_type == ProviderType.OPENAI:
            return "gpt-4"
        elif provider_config.provider_type == ProviderType.ANTHROPIC:
            return "claude-3-opus-20240229"
        else:
            raise ValueError(f"Unknown provider type: {provider_config.provider_type}")
```

---

## 5. Connection Management

### 5.1 Connection Pooling

```python
# connection/pool.py
import httpx
from typing import Dict, Optional
import asyncio
from contextlib import asynccontextmanager

class ConnectionPool:
    """HTTP connection pool for LLM providers"""

    def __init__(self, max_connections: int = 100):
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._max_connections = max_connections

    @asynccontextmanager
    async def get_client(
        self,
        provider: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ) -> httpx.AsyncClient:
        """Get or create HTTP client for provider"""
        if provider not in self._clients:
            if provider not in self._locks:
                self._locks[provider] = asyncio.Lock()

            async with self._locks[provider]:
                if provider not in self._clients:
                    self._clients[provider] = httpx.AsyncClient(
                        base_url=base_url,
                        timeout=httpx.Timeout(timeout),
                        limits=httpx.Limits(
                            max_connections=self._max_connections,
                            max_keepalive_connections=20
                        ),
                        headers={
                            "User-Agent": "Mobius-Context-Engine/1.0"
                        }
                    )

        yield self._clients[provider]

    async def close_all(self) -> None:
        """Close all HTTP clients"""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()
```

### 5.2 Health Checks and Circuit Breaker

```python
# connection/circuit_breaker.py
from enum import Enum
from typing import Dict, Optional
import time
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker for provider resilience"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2
    ):
        self._states: Dict[str, CircuitState] = {}
        self._failure_counts: Dict[str, int] = {}
        self._success_counts: Dict[str, int] = {}
        self._last_failure_time: Dict[str, float] = {}

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

    def is_available(self, provider: str) -> bool:
        """Check if provider is available"""
        state = self._states.get(provider, CircuitState.CLOSED)

        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self._last_failure_time.get(provider, 0) > self.recovery_timeout:
                self._states[provider] = CircuitState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self, provider: str) -> None:
        """Record successful request"""
        state = self._states.get(provider, CircuitState.CLOSED)

        if state == CircuitState.HALF_OPEN:
            self._success_counts[provider] = self._success_counts.get(provider, 0) + 1
            if self._success_counts[provider] >= self.success_threshold:
                # Fully recover
                self._states[provider] = CircuitState.CLOSED
                self._failure_counts[provider] = 0
                self._success_counts[provider] = 0
        elif state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_counts[provider] = 0

    def record_failure(self, provider: str) -> None:
        """Record failed request"""
        state = self._states.get(provider, CircuitState.CLOSED)

        if state == CircuitState.CLOSED:
            self._failure_counts[provider] = self._failure_counts.get(provider, 0) + 1
            if self._failure_counts[provider] >= self.failure_threshold:
                # Open circuit
                self._states[provider] = CircuitState.OPEN
                self._last_failure_time[provider] = time.time()
        elif state == CircuitState.HALF_OPEN:
            # Failed during recovery, reopen
            self._states[provider] = CircuitState.OPEN
            self._last_failure_time[provider] = time.time()
            self._success_counts[provider] = 0
```

---

## 6. Performance Optimization

### 6.1 Response Caching

```python
# caching/response_cache.py
import hashlib
import json
import time
from typing import Optional, Any, Dict
import redis.asyncio as redis
from contextlib import asynccontextmanager

class ResponseCache:
    """LRU cache for LLM responses"""

    def __init__(self, ttl: int = 3600, max_size: int = 10000):
        self.ttl = ttl
        self.max_size = max_size
        self._redis: Optional[redis.Redis] = None

    async def initialize(self, redis_url: str = "redis://localhost:6379") -> None:
        """Initialize Redis connection"""
        self._redis = redis.from_url(redis_url, decode_responses=True)
        await self._redis.ping()

    def _generate_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key from request data"""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        hash_object = hashlib.sha256(sorted_data.encode())
        return f"llm_cache:{hash_object.hexdigest()}"

    async def get(self, key: str) -> Optional[CompletionResponse]:
        """Get cached response"""
        if not self._redis:
            return None

        try:
            cached_data = await self._redis.get(key)
            if cached_data:
                data = json.loads(cached_data)
                return CompletionResponse(**data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")

        return None

    async def set(self, key: str, response: CompletionResponse) -> None:
        """Cache response with TTL"""
        if not self._redis:
            return

        try:
            # Check cache size
            cache_size = await self._redis.dbsize()
            if cache_size >= self.max_size:
                # Implement LRU eviction
                await self._evict_oldest()

            # Store with TTL
            await self._redis.setex(
                key,
                self.ttl,
                response.model_dump_json()
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    async def _evict_oldest(self) -> None:
        """Evict oldest entries when cache is full"""
        # Simple implementation - delete 10% of keys
        keys = await self._redis.keys("llm_cache:*")
        if keys:
            to_delete = keys[:len(keys) // 10]
            if to_delete:
                await self._redis.delete(*to_delete)
```

### 6.2 Batch Processing

```python
# optimization/batch_processor.py
from typing import List, Dict, Any, Tuple
import asyncio
from collections import defaultdict

class BatchProcessor:
    """Batch multiple requests for efficiency"""

    def __init__(
        self,
        batch_size: int = 10,
        batch_timeout: float = 0.1  # 100ms
    ):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self._pending_requests: Dict[str, List[Tuple[Any, asyncio.Future]]] = defaultdict(list)
        self._batch_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def add_request(
        self,
        provider: str,
        request: Any
    ) -> Any:
        """Add request to batch queue"""
        future = asyncio.Future()

        async with self._batch_locks[provider]:
            self._pending_requests[provider].append((request, future))

            # Check if batch is ready
            if len(self._pending_requests[provider]) >= self.batch_size:
                await self._process_batch(provider)
            else:
                # Schedule timeout
                asyncio.create_task(self._schedule_batch(provider))

        return await future

    async def _schedule_batch(self, provider: str) -> None:
        """Process batch after timeout"""
        await asyncio.sleep(self.batch_timeout)
        async with self._batch_locks[provider]:
            if self._pending_requests[provider]:
                await self._process_batch(provider)

    async def _process_batch(self, provider: str) -> None:
        """Process accumulated batch"""
        batch = self._pending_requests[provider]
        self._pending_requests[provider] = []

        if not batch:
            return

        try:
            # Process batch (implementation depends on provider)
            requests = [req for req, _ in batch]
            responses = await self._execute_batch(provider, requests)

            # Resolve futures
            for (_, future), response in zip(batch, responses):
                future.set_result(response)

        except Exception as e:
            # Reject all futures in batch
            for _, future in batch:
                future.set_exception(e)
```

---

## 7. Error Handling and Resilience

### 7.1 Retry Strategies

```python
# resilience/retry_strategy.py
from typing import TypeVar, Callable, Optional, Type
import asyncio
import random
import time
from functools import wraps

T = TypeVar('T')

class RetryStrategy:
    """Configurable retry strategy for LLM requests"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on: Optional[Tuple[Type[Exception], ...]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on or (Exception,)

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = min(
            self.initial_delay * (self.exponential_base ** (attempt - 1)),
            self.max_delay
        )

        if self.jitter:
            # Add random jitter (±25%)
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if should retry based on exception"""
        if attempt >= self.max_attempts:
            return False

        # Check if exception type should be retried
        return isinstance(exception, self.retry_on)

def with_retry(strategy: RetryStrategy):
    """Decorator for adding retry logic to async functions"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, strategy.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if not strategy.should_retry(e, attempt):
                        raise

                    if attempt < strategy.max_attempts:
                        delay = strategy.calculate_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)

            # All attempts failed
            raise last_exception

        return wrapper
    return decorator
```

### 7.2 Error Classification and Handling

```python
# resilience/error_handler.py
from enum import Enum
from typing import Optional, Dict, Any

class ErrorCategory(Enum):
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    INVALID_REQUEST = "invalid_request"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

class ErrorClassifier:
    """Classify and handle LLM provider errors"""

    @staticmethod
    def classify_error(exception: Exception) -> ErrorCategory:
        """Classify exception into error category"""
        error_msg = str(exception).lower()

        if any(term in error_msg for term in ['rate limit', '429', 'too many requests']):
            return ErrorCategory.RATE_LIMIT
        elif any(term in error_msg for term in ['unauthorized', '401', 'invalid api key']):
            return ErrorCategory.AUTHENTICATION
        elif any(term in error_msg for term in ['bad request', '400', 'invalid']):
            return ErrorCategory.INVALID_REQUEST
        elif any(term in error_msg for term in ['500', '502', '503', 'server error']):
            return ErrorCategory.SERVER_ERROR
        elif any(term in error_msg for term in ['timeout', 'timed out']):
            return ErrorCategory.TIMEOUT
        elif any(term in error_msg for term in ['connection', 'network']):
            return ErrorCategory.NETWORK_ERROR
        else:
            return ErrorCategory.UNKNOWN

    @staticmethod
    def get_retry_strategy(category: ErrorCategory) -> Optional[RetryStrategy]:
        """Get appropriate retry strategy for error category"""
        strategies = {
            ErrorCategory.RATE_LIMIT: RetryStrategy(
                max_attempts=5,
                initial_delay=5.0,
                exponential_base=2.0
            ),
            ErrorCategory.SERVER_ERROR: RetryStrategy(
                max_attempts=3,
                initial_delay=1.0
            ),
            ErrorCategory.NETWORK_ERROR: RetryStrategy(
                max_attempts=3,
                initial_delay=0.5
            ),
            ErrorCategory.TIMEOUT: RetryStrategy(
                max_attempts=2,
                initial_delay=0.1
            )
        }

        return strategies.get(category)
```

---

## 8. Security Considerations

### 8.1 API Key Management

```python
# security/key_manager.py
import os
from typing import Dict, Optional
from cryptography.fernet import Fernet
import base64
import json

class SecureKeyManager:
    """Secure storage and retrieval of API keys"""

    def __init__(self, master_key: Optional[str] = None):
        # Use environment variable or provided key
        key = master_key or os.environ.get("MOBIUS_MASTER_KEY")
        if not key:
            raise ValueError("Master key not provided")

        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        self._keys: Dict[str, str] = {}

    def load_from_env(self) -> None:
        """Load API keys from environment variables"""
        # OpenAI
        if openai_key := os.environ.get("OPENAI_API_KEY"):
            self.set_key("openai", openai_key)

        # Anthropic
        if anthropic_key := os.environ.get("ANTHROPIC_API_KEY"):
            self.set_key("anthropic", anthropic_key)

    def set_key(self, provider: str, api_key: str) -> None:
        """Securely store an API key"""
        encrypted = self._fernet.encrypt(api_key.encode())
        self._keys[provider] = base64.b64encode(encrypted).decode()

    def get_key(self, provider: str) -> Optional[str]:
        """Retrieve and decrypt an API key"""
        if provider not in self._keys:
            return None

        try:
            encrypted = base64.b64decode(self._keys[provider])
            decrypted = self._fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt key for {provider}: {e}")
            return None
```

### 8.2 Request/Response Sanitization

```python
# security/sanitizer.py
import re
from typing import Dict, Any, List

class RequestSanitizer:
    """Sanitize requests and responses for security"""

    # Patterns for sensitive data
    PATTERNS = {
        'api_key': re.compile(r'(api[_-]?key|apikey)[\s:=]*(\S+)', re.IGNORECASE),
        'token': re.compile(r'(token|auth|bearer)[\s:=]*(\S+)', re.IGNORECASE),
        'password': re.compile(r'(password|passwd|pwd)[\s:=]*(\S+)', re.IGNORECASE),
        'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    }

    @classmethod
    def sanitize_text(cls, text: str, mask: str = "[REDACTED]") -> str:
        """Sanitize sensitive data in text"""
        sanitized = text

        for pattern_name, pattern in cls.PATTERNS.items():
            if pattern_name == 'email':
                # Partial masking for emails
                sanitized = pattern.sub(
                    lambda m: m.group(0).split('@')[0][:3] + '***@' + m.group(0).split('@')[1],
                    sanitized
                )
            else:
                sanitized = pattern.sub(mask, sanitized)

        return sanitized

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary"""
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_text(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                sanitized[key] = value

        return sanitized
```

---

## 9. Monitoring and Observability

### 9.1 Metrics Collection

```python
# monitoring/metrics.py
from typing import Dict, Optional
import time
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio
from datetime import datetime, timedelta

@dataclass
class ProviderMetrics:
    """Metrics for a single provider"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    response_times: List[float] = field(default_factory=list)
    error_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def average_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx]

class MetricsCollector:
    """Collect and aggregate LLM metrics"""

    def __init__(self, window_size: int = 3600):  # 1 hour window
        self.window_size = window_size
        self._metrics: Dict[str, ProviderMetrics] = defaultdict(ProviderMetrics)
        self._time_series: Dict[str, List[Tuple[float, Dict]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def record_request(
        self,
        provider: str,
        model: str,
        response_time: float,
        tokens: int,
        success: bool = True,
        error: Optional[str] = None,
        cost: float = 0.0
    ) -> None:
        """Record request metrics"""
        async with self._lock:
            metrics = self._metrics[provider]
            metrics.total_requests += 1

            if success:
                metrics.successful_requests += 1
                metrics.response_times.append(response_time)
                metrics.total_tokens += tokens
                metrics.total_cost += cost
            else:
                metrics.failed_requests += 1
                if error:
                    metrics.error_counts[error] += 1

            # Add to time series
            timestamp = time.time()
            self._time_series[provider].append((
                timestamp,
                {
                    "model": model,
                    "response_time": response_time,
                    "tokens": tokens,
                    "success": success,
                    "error": error,
                    "cost": cost
                }
            ))

            # Clean old data
            await self._cleanup_old_data(provider)

    async def get_metrics(self, provider: Optional[str] = None) -> Dict[str, ProviderMetrics]:
        """Get current metrics"""
        async with self._lock:
            if provider:
                return {provider: self._metrics[provider]}
            return dict(self._metrics)

    async def _cleanup_old_data(self, provider: str) -> None:
        """Remove data outside time window"""
        cutoff = time.time() - self.window_size

        # Clean time series
        self._time_series[provider] = [
            (ts, data) for ts, data in self._time_series[provider]
            if ts > cutoff
        ]

        # Limit response times list
        metrics = self._metrics[provider]
        if len(metrics.response_times) > 1000:
            metrics.response_times = metrics.response_times[-1000:]
```

### 9.2 Request/Response Logging

```python
# monitoring/logging.py
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from pathlib import Path

class LLMRequestLogger:
    """Structured logging for LLM requests/responses"""

    def __init__(
        self,
        log_dir: str = "logs/llm",
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        retention_days: int = 7
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size
        self.retention_days = retention_days

        # Setup structured logger
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup JSON structured logger"""
        logger = logging.getLogger("llm_requests")
        logger.setLevel(logging.INFO)

        # JSON formatter
        formatter = logging.Formatter(
            '%(message)s'
        )

        # Rotating file handler
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            self.log_dir / "requests.jsonl",
            maxBytes=self.max_file_size,
            backupCount=5
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        return logger

    async def log_request(
        self,
        request_id: str,
        provider: str,
        model: str,
        messages: List[Message],
        parameters: Dict[str, Any]
    ) -> None:
        """Log LLM request"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "type": "request",
            "provider": provider,
            "model": model,
            "message_count": len(messages),
            "parameters": parameters,
            "messages": [
                {
                    "role": msg.role,
                    "content_length": len(msg.content)
                }
                for msg in messages
            ]
        }

        self.logger.info(json.dumps(log_entry))

    async def log_response(
        self,
        request_id: str,
        provider: str,
        model: str,
        response: CompletionResponse,
        error: Optional[Exception] = None
    ) -> None:
        """Log LLM response"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "type": "response",
            "provider": provider,
            "model": model,
            "success": error is None,
            "response_time_ms": response.response_time_ms if response else None,
            "usage": response.usage.model_dump() if response else None,
            "error": str(error) if error else None,
            "error_type": type(error).__name__ if error else None
        }

        self.logger.info(json.dumps(log_entry))
```

---

## 10. Testing Strategy

### 10.1 Mock Providers

```python
# testing/mock_provider.py
from typing import AsyncIterator, List, Dict, Any
import asyncio
import random

class MockLLMProvider(LLMProvider):
    """Mock provider for testing"""

    def __init__(
        self,
        response_delay: float = 0.1,
        error_rate: float = 0.0,
        model_responses: Optional[Dict[str, str]] = None
    ):
        self.response_delay = response_delay
        self.error_rate = error_rate
        self.model_responses = model_responses or {
            "default": "This is a mock response."
        }
        self.request_count = 0

    @classmethod
    async def create(cls, config: ProviderConfig) -> "MockLLMProvider":
        return cls()

    async def complete(
        self,
        messages: List[Message],
        model: str = "mock-model",
        **kwargs
    ) -> CompletionResponse:
        """Generate mock completion"""
        self.request_count += 1

        # Simulate delay
        await asyncio.sleep(self.response_delay)

        # Simulate errors
        if random.random() < self.error_rate:
            raise LLMProviderError(
                "Mock error",
                provider="mock",
                error_code="mock_error"
            )

        # Generate response
        content = self.model_responses.get(
            model,
            self.model_responses["default"]
        )

        # Calculate mock tokens
        prompt_tokens = sum(len(msg.content.split()) * 1.3 for msg in messages)
        completion_tokens = len(content.split()) * 1.3

        return CompletionResponse(
            content=content,
            model=model,
            provider="mock",
            usage=Usage(
                prompt_tokens=int(prompt_tokens),
                completion_tokens=int(completion_tokens),
                total_tokens=int(prompt_tokens + completion_tokens)
            ),
            response_time_ms=self.response_delay * 1000
        )

    async def stream_complete(
        self,
        messages: List[Message],
        model: str = "mock-model",
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream mock completion"""
        await asyncio.sleep(self.response_delay)

        content = self.model_responses.get(
            model,
            self.model_responses["default"]
        )

        # Stream word by word
        words = content.split()
        for i, word in enumerate(words):
            yield StreamChunk(
                content=word + (" " if i < len(words) - 1 else ""),
                provider="mock",
                model=model,
                finish_reason="stop" if i == len(words) - 1 else None
            )
            await asyncio.sleep(0.01)  # Small delay between chunks

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate mock embeddings"""
        await asyncio.sleep(self.response_delay)

        # Generate random embeddings
        return [
            [random.random() for _ in range(1536)]
            for _ in texts
        ]
```

### 10.2 Integration Tests

```python
# tests/test_llm_integration.py
import pytest
import asyncio
from unittest.mock import Mock, patch

@pytest.fixture
async def llm_manager():
    """Create LLM manager with mock providers"""
    config = LLMConfig(
        providers={
            "mock_openai": ProviderConfig(
                provider_type=ProviderType.OPENAI,
                api_key=SecretStr("mock-key")
            ),
            "mock_anthropic": ProviderConfig(
                provider_type=ProviderType.ANTHROPIC,
                api_key=SecretStr("mock-key")
            )
        },
        default_provider="mock_openai",
        fallback_providers=["mock_anthropic"]
    )

    manager = LLMManager(config)

    # Register mock providers
    manager._provider_factory.register_provider(
        ProviderType.OPENAI,
        MockLLMProvider
    )
    manager._provider_factory.register_provider(
        ProviderType.ANTHROPIC,
        MockLLMProvider
    )

    await manager.initialize()
    return manager

@pytest.mark.asyncio
async def test_basic_completion(llm_manager):
    """Test basic completion request"""
    messages = [
        Message(role=MessageRole.USER, content="Hello, world!")
    ]

    response = await llm_manager.complete(messages)

    assert response.content
    assert response.provider == "mock_openai"
    assert response.usage.total_tokens > 0

@pytest.mark.asyncio
async def test_fallback_on_error(llm_manager):
    """Test fallback to secondary provider"""
    # Make primary provider fail
    primary = await llm_manager._provider_factory.get_provider(
        "mock_openai",
        llm_manager.config
    )
    primary.error_rate = 1.0  # Always fail

    messages = [
        Message(role=MessageRole.USER, content="Test fallback")
    ]

    response = await llm_manager.complete(messages)

    assert response.provider == "mock_anthropic"  # Fallback provider

@pytest.mark.asyncio
async def test_streaming(llm_manager):
    """Test streaming completion"""
    messages = [
        Message(role=MessageRole.USER, content="Stream test")
    ]

    chunks = []
    async with llm_manager.stream_complete(messages) as stream:
        async for chunk in stream:
            chunks.append(chunk)

    assert len(chunks) > 0
    assert any(chunk.finish_reason == "stop" for chunk in chunks)

@pytest.mark.asyncio
async def test_rate_limiting(llm_manager):
    """Test concurrent request handling"""
    messages = [
        Message(role=MessageRole.USER, content=f"Request {i}")
        for i in range(20)
    ]

    # Send concurrent requests
    tasks = [
        llm_manager.complete([msg])
        for msg in messages
    ]

    responses = await asyncio.gather(*tasks)

    assert len(responses) == 20
    assert all(r.content for r in responses)

@pytest.mark.asyncio
async def test_caching(llm_manager):
    """Test response caching"""
    messages = [
        Message(role=MessageRole.USER, content="Cached request")
    ]

    # First request
    response1 = await llm_manager.complete(messages)

    # Second request (should be cached)
    response2 = await llm_manager.complete(messages)

    assert response1.content == response2.content
    assert response2.response_time_ms < response1.response_time_ms  # Cached is faster
```

---

## 11. API Endpoints

### 11.1 FastAPI Integration

```python
# api/v1/llm_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List, Optional
import uuid

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])

@router.post("/complete")
async def complete(
    request: CompletionRequest,
    llm_manager: LLMManager = Depends(get_llm_manager)
) -> CompletionResponse:
    """Generate LLM completion"""
    try:
        messages = [
            Message(role=msg.role, content=msg.content)
            for msg in request.messages
        ]

        response = await llm_manager.complete(
            messages=messages,
            model=request.model,
            provider=request.provider,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        return response

    except LLMProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM provider error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Completion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/stream")
async def stream_complete(
    request: CompletionRequest,
    llm_manager: LLMManager = Depends(get_llm_manager)
) -> StreamingResponse:
    """Stream LLM completion"""
    async def generate():
        try:
            messages = [
                Message(role=msg.role, content=msg.content)
                for msg in request.messages
            ]

            async with llm_manager.stream_complete(
                messages=messages,
                model=request.model,
                provider=request.provider,
                temperature=request.temperature
            ) as stream:
                async for chunk in stream:
                    yield f"data: {chunk.model_dump_json()}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            error_chunk = StreamChunk(
                content="",
                provider="error",
                model="error",
                finish_reason="error"
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@router.post("/embed")
async def create_embeddings(
    request: EmbeddingRequest,
    llm_manager: LLMManager = Depends(get_llm_manager)
) -> EmbeddingResponse:
    """Generate embeddings"""
    try:
        # Use OpenAI for embeddings
        provider = await llm_manager._provider_factory.get_provider(
            "openai",
            llm_manager.config
        )

        embeddings = await provider.embed(
            texts=request.texts,
            model=request.model or "text-embedding-3-small"
        )

        return EmbeddingResponse(
            embeddings=embeddings,
            model=request.model or "text-embedding-3-small",
            usage=Usage(
                prompt_tokens=sum(len(text.split()) for text in request.texts),
                completion_tokens=0,
                total_tokens=sum(len(text.split()) for text in request.texts)
            )
        )

    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate embeddings"
        )

@router.get("/metrics")
async def get_metrics(
    provider: Optional[str] = None,
    llm_manager: LLMManager = Depends(get_llm_manager)
) -> Dict[str, ProviderMetrics]:
    """Get LLM provider metrics"""
    return await llm_manager._metrics.get_metrics(provider)
```

---

## Conclusion

This specification provides a comprehensive foundation for integrating LLM providers in Phase 1 of the Mobius platform. The architecture supports:

1. **Multiple Providers**: Easy integration of OpenAI and Anthropic with room for expansion
2. **Reliability**: Automatic fallbacks, retry logic, and circuit breakers
3. **Performance**: Response caching, connection pooling, and batch processing
4. **Security**: Secure API key management and request sanitization
5. **Observability**: Comprehensive metrics and logging
6. **Testing**: Mock providers and integration test patterns

The implementation prioritizes async-first design, proper error handling, and production-ready patterns while maintaining flexibility for future enhancements.
```
