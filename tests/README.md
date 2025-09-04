# Tests

This folder contains test scripts for the Composio Documentation MCP Server.

## test_intelligent_agent.py

Comprehensive test suite for the intelligent agent functionality including:

- **Database Status**: Verifies the ChromaDB database is populated with documentation chunks
- **Intent Detection**: Tests automatic detection of Composio-related queries
- **Search Functionality**: Tests semantic search across documentation
- **Intelligent Agent Workflow**: End-to-end test of the coordination system

### Running Tests

```bash
# From project root
source venv/Scripts/activate
python tests/test_intelligent_agent.py
```

### Expected Output

- ✅ Database with 365+ documentation chunks
- ✅ Intent detection with high confidence scores
- ✅ Semantic search with relevant results  
- ✅ Full agent coordination workflow

This validates that the intelligent retrieval system is working correctly before deploying to VS Code.
