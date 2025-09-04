# Composio Documentation MCP Server with Intelligent Agent

An advanced **Model Context Protocol (MCP)** server that provides intelligent, semantic access to Composio documentation with automatic intent detection and context injection.

## 🌟 Features

### 🧠 Intelligent Agent Coordination
- **Automatic Intent Detection**: Detects Composio-related queries with high accuracy
- **Invisible Retrieval**: Seamlessly injects relevant documentation context
- **Smart Query Extraction**: Generates optimal search queries from user requests
- **Code Validation**: Validates generated code against latest documentation

### 🔍 Advanced Semantic Search
- **365+ Documentation Chunks**: Comprehensive coverage of Composio docs
- **Vector Similarity Search**: Uses Sentence Transformers for semantic understanding
- **Persistent Storage**: ChromaDB for fast, reliable retrieval
- **Smart Chunking**: Intelligent text segmentation with overlap

### 🛠️ MCP Integration
- **VS Code Compatible**: Works seamlessly with VS Code MCP extension
- **FastMCP Framework**: Built on FastMCP 2.12.2 for reliability
- **Multiple Tools**: 6 specialized tools for different use cases
- **STDIO Transport**: Standard MCP communication protocol

## 📁 Project Structure

```
Grimoire3/
├── composio_docs_server_enhanced.py   # Main MCP server with intelligent agent
├── .vscode/mcp.json                   # VS Code MCP configuration
├── tests/                             # Test suite
│   ├── test_intelligent_agent.py      # Comprehensive functionality tests
│   └── README.md                      # Test documentation
├── venv/                              # Python virtual environment
├── chroma_db/                         # ChromaDB vector database (gitignored)
├── .gitignore                         # Git ignore rules
└── README.md                          # This file
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone and navigate to project
git clone <repository-url>
cd Grimoire3

# Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install fastmcp sentence-transformers chromadb beautifulsoup4 tiktoken requests
```

### 2. Initialize Documentation Database
```bash
# Run the server once to build the database (will take a few minutes)
python composio_docs_server_enhanced.py
# Press Ctrl+C after "Starting MCP server" message appears
```

### 3. Configure VS Code MCP
The `.vscode/mcp.json` is already configured. Just ensure the Python path matches your environment:

```json
{
  "mcp": {
    "servers": {
      "composio-docs-server": {
        "command": "./venv/Scripts/python.exe",
        "args": ["composio_docs_server_enhanced.py"],
        "cwd": "."
      }
    }
  }
}
```

### 4. Test the System
```bash
# Run comprehensive tests
python tests/test_intelligent_agent.py
```

Expected output:
- ✅ Database with 365+ chunks
- ✅ Intent detection working  
- ✅ Semantic search functional
- ✅ Intelligent agent coordination active

## 🎯 Available MCP Tools

### Core Intelligence
- **`composio_intelligent_agent`**: Main coordination tool (invisible to user)
- **`validate_composio_code`**: Code validation against documentation
- **`detect_composio_intent`**: Intent detection (for debugging)

### Search & Data
- **`search_composio_docs`**: Manual semantic search
- **`get_database_status`**: Check system health
- **`refresh_composio_docs`**: Update documentation database

## 🧪 How It Works

### Intent Detection
The system automatically detects Composio-related queries using:
- Keyword matching (`composio`, `authentication`, `tools`, etc.)
- Confidence scoring (0.0 - 1.0)
- Context analysis

### Semantic Retrieval
When Composio intent is detected:
1. **Query Extraction**: Generates optimal search terms
2. **Vector Search**: Finds relevant documentation chunks
3. **Context Formatting**: Prepares information for AI injection
4. **Invisible Integration**: Provides context without user awareness

### Documentation Coverage
Automatically indexes 90+ pages including:
- 🚀 Getting Started guides
- 🔐 Authentication methods  
- 🛠️ Tool integrations
- 📡 MCP server development
- 🔧 SDK references
- 📖 API documentation

## 🎮 Usage Examples

Once configured, simply ask Composio questions in VS Code:

```
"How do I authenticate with Composio?"
→ System detects intent, retrieves auth docs, provides contextual answer

"Show me how to integrate GitHub tools"  
→ Finds GitHub tool docs, provides integration examples

"What's the proper way to set up an MCP server?"
→ Retrieves MCP development guides, shows best practices
```

The retrieval happens automatically and invisibly - you just get better, more accurate answers!

## 🔧 Technical Details

### Dependencies
- **FastMCP 2.12.2**: MCP server framework
- **ChromaDB**: Vector database for semantic search
- **Sentence Transformers**: Embeddings (all-MiniLM-L6-v2)
- **BeautifulSoup4**: Web scraping for documentation
- **Tiktoken**: Smart text chunking

### Performance
- **Index Time**: ~5 minutes for full documentation
- **Search Speed**: <100ms for semantic queries
- **Memory Usage**: ~200MB for loaded embeddings
- **Database Size**: ~50MB for 365 chunks

### Architecture
```
User Query → Intent Detection → Search Query Generation → 
Vector Retrieval → Context Formatting → AI Response
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `python tests/test_intelligent_agent.py`
4. Submit a pull request

## 📄 License

This project is open source. Please ensure compliance with Composio's documentation usage terms.

## 🆘 Troubleshooting

### Common Issues
- **"Database empty"**: Run the server once to build the database
- **"Module not found"**: Ensure virtual environment is activated
- **"MCP not detected"**: Check VS Code MCP extension is installed
- **"No results found"**: Try broader search terms or refresh database

### Debug Commands
```bash
# Check database status
python -c "from composio_docs_server_enhanced import retriever; print(f'Chunks: {retriever.collection.count()}')"

# Test intent detection
python -c "from composio_docs_server_enhanced import coordinator; print(coordinator.detect_composio_intent('How to use Composio?'))"
```

---

**Built with ❤️ for the Composio community**
