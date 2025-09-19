# Clean Architecture Test Structure

This directory contains tests for the new Clean Architecture backend.

## Structure

```
tests/
├── conftest.py          # Test configuration and fixtures
├── unit/                # Unit tests for individual components
├── integration/         # Integration tests
├── performance/         # Performance tests
└── README.md           # This file
```

## Testing Strategy

### Unit Tests
- Test individual domain entities
- Test use cases in isolation
- Test repository implementations
- Test service layer components

### Integration Tests  
- Test API endpoints
- Test database operations
- Test external service integrations
- Test authentication flows

### Performance Tests
- Load testing
- Response time validation
- Database performance tests

## Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with coverage
pytest --cov=src tests/
```

## Notes

- All tests use the clean architecture structure (src.domain, src.application, etc.)
- Test fixtures are configured for the new backend structure
- Old tests have been removed as they were incompatible with clean architecture