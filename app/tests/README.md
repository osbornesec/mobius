# Mobius Test Suite

## Pinecone Vector Operations Tests

This directory contains comprehensive tests for Pinecone vector database
operations.

### Prerequisites

1. **Environment Variables**: Set your Pinecone API key:

   ```bash
   export PINECONE_API_KEY="your-api-key-here"
   ```

2. **Dependencies**: Install required packages:

   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

### Running Tests

#### Run all Pinecone tests

```bash
pytest app/tests/test_pinecone_operations.py -v
```

#### Run specific test classes

```bash
# Test basic operations
pytest app/tests/test_pinecone_operations.py::TestPineconeOperations -v

# Test error handling
pytest app/tests/test_pinecone_operations.py::TestPineconeWithoutAPIKey -v

# Test async operations (requires pinecone[asyncio])
pytest app/tests/test_pinecone_operations.py::TestPineconeAsyncOperations -v
```

#### Run specific test methods

```bash
pytest app/tests/test_pinecone_operations.py::TestPineconeOperations::test_upsert_operations -v
```

#### Run with coverage

```bash
pytest app/tests/test_pinecone_operations.py --cov=app.storage.vector --cov-report=html
```

### Test Structure

The `test_pinecone_operations.py` file includes tests for:

1. **Index Operations**:
   - Index creation with serverless spec
   - Index description and verification
   - Index cleanup

2. **Vector Operations**:
   - Upsert operations (single and batch)
   - Query operations (basic and with metadata filters)
   - Fetch operations (retrieve by ID)
   - Update operations (values and metadata)
   - Delete operations
   - List operations (with prefix filtering)

3. **Advanced Features**:
   - Namespace isolation
   - Batch processing (100+ vectors)
   - Error handling and validation
   - Async operations support

4. **Edge Cases**:
   - Missing API key handling
   - Invalid API key handling
   - Invalid vector dimensions
   - Invalid query parameters

### Important Notes

- Tests create a temporary index named `mobius-test-index` which is
  automatically cleaned up
- Tests use a 384-dimensional vector space (adjustable via `TEST_DIMENSION`)
- All tests are isolated using namespaces
- Index creation may take 10-15 seconds on first run
- Some operations have built-in delays to allow for eventual consistency

### Troubleshooting

1. **API Key Issues**:
   - Ensure `PINECONE_API_KEY` is set correctly
   - Verify the key has permissions to create/delete indexes

2. **Index Already Exists**:
   - The test suite attempts to clean up existing test indexes
   - If cleanup fails, manually delete `mobius-test-index` from your Pinecone
     console

3. **Timeout Errors**:
   - Increase the sleep times in the test if you experience timing issues
   - Pinecone operations are eventually consistent

4. **Async Tests Skipped**:
   - Install async support: `pip install "pinecone-client[asyncio]"`
