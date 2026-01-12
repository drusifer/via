# Trin Next Steps

## Immediate
1. **Wait for @Neo** to fix DatabaseStore connection blocker in CLI
2. **Verify fix** with smoke test: `via index /tmp/via_test`

## Phase 1: Unit Tests (After Blocker Fixed)
1. Create `tests/unit/test_cli_parser.py` - 12 test cases for argument parsing
2. Create `tests/unit/test_cli_progress.py` - 3 test cases for progress callback
3. Run unit tests: `pytest tests/unit/test_cli_*.py -v`

## Phase 2: Integration Tests
1. Create `tests/integration/test_cli_index.py` - 7 happy path tests
2. Create `tests/integration/test_cli_index_errors.py` - 6 error handling tests
3. Create `tests/integration/test_cli_database.py` - 3 database connection tests
4. Run integration tests: `pytest tests/integration/test_cli_*.py -v`

## Phase 3: E2E Tests
1. Create `tests/e2e/test_real_indexing.py` - 5 acceptance tests
2. Create `tests/e2e/test_edge_cases.py` - 8 edge case tests
3. Run E2E tests: `pytest tests/e2e/test_*.py -v`

## Coverage Goal
- Achieve 90%+ coverage for `via/__main__.py`
- Verify all 13 acceptance criteria met
