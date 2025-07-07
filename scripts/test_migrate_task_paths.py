#!/usr/bin/env python3
"""
Test suite for the task path migration script.
"""

import unittest
from migrate_task_paths import PathMigrator, TaskMigrator
from pathlib import Path
import tempfile
import shutil


class TestPathMigrator(unittest.TestCase):
    """Test path transformation logic."""
    
    def setUp(self):
        self.migrator = PathMigrator()
    
    def test_remove_backend_prefix(self):
        """Test removal of backend/ prefix."""
        cases = [
            ("backend/app/main.py", "app/main.py"),
            ("backend/tests/test_main.py", "tests/backend/unit/test_main.py"),  # Also gets test migration
            ("backend/alembic/versions/001.py", "alembic/versions/001.py"),
        ]
        
        for original, expected in cases:
            result, reason = self.migrator.transform_path(original)
            self.assertEqual(result, expected)
            self.assertIn("Removed 'backend/' prefix", reason)
    
    def test_python_test_migration(self):
        """Test Python test file migrations."""
        cases = [
            ("tests/test_main.py", "tests/backend/unit/test_main.py"),
            ("tests/test_integration_api.py", "tests/backend/integration/test_integration_api.py"),
            ("tests/test_e2e_workflow.py", "tests/backend/e2e/test_e2e_workflow.py"),
        ]
        
        for original, expected in cases:
            result, reason = self.migrator.transform_path(original)
            self.assertEqual(result, expected)
            self.assertIn("Moved Python test to", reason)
    
    def test_frontend_test_migration(self):
        """Test frontend test file migrations."""
        cases = [
            ("src/__tests__/App.test.tsx", "tests/frontend/unit/App.test.tsx"),
            ("tests/component.test.js", "tests/frontend/unit/component.test.js"),
        ]
        
        for original, expected in cases:
            result, reason = self.migrator.transform_path(original)
            self.assertEqual(result, expected)
    
    def test_src_to_app_migration(self):
        """Test src/ to app/ migration for Python files."""
        cases = [
            ("src/main.py", "app/main.py"),
            ("src/services/auth.py", "app/services/auth.py"),
            # Should not transform non-Python files
            ("src/App.tsx", "src/App.tsx"),
            ("src/index.js", "src/index.js"),
        ]
        
        for original, expected in cases:
            result, _ = self.migrator.transform_path(original)
            self.assertEqual(result, expected)
    
    def test_combined_transformations(self):
        """Test paths that need multiple transformations."""
        cases = [
            ("backend/tests/test_api.py", "tests/backend/unit/test_api.py"),
            ("backend/src/core.py", "app/core.py"),
        ]
        
        for original, expected in cases:
            result, _ = self.migrator.transform_path(original)
            self.assertEqual(result, expected)
    
    def test_process_file_content(self):
        """Test processing of file content with various path formats."""
        content = '''# Test Task

## Files to create:
- `backend/app/main.py` - Main application file
- `backend/tests/test_main.py` - Test file
- "src/__tests__/App.test.tsx" - Frontend test
- Create (backend/app/config.py) for configuration

### Import statements:
```python
from backend.app.core import setup
import backend.utils.helpers
```

### Test locations:
- Tests in `tests/test_integration_db.py`
- Frontend tests in 'src/__tests__/components/Button.test.tsx'
'''
        
        new_content, changes = self.migrator.process_file_content(content)
        
        # Verify transformations
        self.assertIn("`app/main.py`", new_content)
        self.assertIn("`tests/backend/unit/test_main.py`", new_content)
        self.assertIn('"tests/frontend/unit/App.test.tsx"', new_content)
        self.assertIn("(app/config.py)", new_content)
        self.assertIn("`tests/backend/integration/test_integration_db.py`", new_content)
        
        # Verify change tracking
        self.assertTrue(len(changes) > 0)
        self.assertEqual(changes[0]['original'], 'backend/app/main.py')
        self.assertEqual(changes[0]['transformed'], 'app/main.py')


class TestTaskMigrator(unittest.TestCase):
    """Test the full migration process."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.tasks_dir = Path(self.test_dir) / "tasks"
        self.tasks_dir.mkdir()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def create_test_file(self, filename: str, content: str):
        """Helper to create test files."""
        file_path = self.tasks_dir / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def test_migration_process(self):
        """Test the complete migration process."""
        # Create test files
        self.create_test_file("task001.md", '''# Task 001
        
Files to create:
- `backend/app/main.py`
- `backend/tests/test_main.py`
- `src/utils.py` (Python utility)
''')
        
        self.create_test_file("task002.md", '''# Task 002
        
No paths to migrate here.
Just some regular content.
''')
        
        # Run migration
        migrator = TaskMigrator(str(self.tasks_dir))
        report = migrator.migrate(dry_run=False)
        
        # Verify report
        self.assertEqual(report['files_processed'], 2)
        self.assertEqual(report['files_modified'], 1)
        self.assertGreater(report['total_changes'], 0)
        self.assertEqual(len(report['errors']), 0)
        
        # Verify file content was modified
        task1_content = (self.tasks_dir / "task001.md").read_text()
        self.assertIn("`app/main.py`", task1_content)
        self.assertIn("`tests/backend/unit/test_main.py`", task1_content)
        self.assertIn("`app/utils.py`", task1_content)
        
        # Verify backup was created
        self.assertTrue(Path(migrator.backup_dir).exists())
    
    def test_dry_run(self):
        """Test dry run mode doesn't modify files."""
        # Create test file
        original_content = '''# Task
- `backend/app/main.py`
'''
        test_file = self.create_test_file("task.md", original_content)
        
        # Run dry run
        migrator = TaskMigrator(str(self.tasks_dir))
        report = migrator.migrate(dry_run=True)
        
        # Verify file wasn't modified
        self.assertEqual(test_file.read_text(), original_content)
        
        # But changes were detected
        self.assertEqual(report['files_modified'], 1)
        self.assertGreater(report['total_changes'], 0)


if __name__ == '__main__':
    unittest.main()