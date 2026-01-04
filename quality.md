# Quality Assurance

## Backend Tests

### `backend/test_mongo.py`
- **test_mongo**: Verifies MongoDB connection, pings the server, and lists collections in the `roddle` database.

### `backend/tests/test_llm.py`
- **test_mock_llm_import**: Ensures `mock_llm` module imports correctly and has `LlmChat`/`UserMessage` classes.
- **test_mock_llm_generate**: Verification that Mock LLM returns properly structured riddle responses with "RIDDLE:" and "ANSWER:" markers.
- **test_local_llm_safe_import**: Checks that `llm_local` module imports correctly and exposes expected attributes.
- **test_local_llm_riddle_format**: Tests that Local LLM responses contain riddle content or valid fallback structure.
- **test_server_llm_import**: Confirms that `server.py` can successfully import an LLM implementation.

### `backend/scripts/smoke_test_server.py`
- **smoke_test_server**: Integration script that performs a full flow: User Registration -> Login (Get Token) -> Fetch User Profile (/me).

## Frontend Tests
*No frontend unit tests (Jest/React Testing Library) were found in the `frontend` directory at this time.*
