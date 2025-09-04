@echo off
REM Setup script for Composio Documentation MCP Server (Windows)

echo 🚀 Setting up Composio Documentation MCP Server...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing dependencies...
pip install fastmcp sentence-transformers chromadb beautifulsoup4 tiktoken requests

REM Test the installation
echo 🧪 Testing installation...
python -c "try: from composio_docs_server_enhanced import retriever; print('✅ All imports successful'); except ImportError as e: print(f'❌ Import error: {e}')"

echo.
echo 🎯 Setup complete! Next steps:
echo 1. Run: python composio_docs_server_enhanced.py (let it build database, then Ctrl+C)
echo 2. Test: python tests/test_intelligent_agent.py
echo 3. Configure VS Code MCP extension to use this server
echo.
echo 📖 See README.md for detailed usage instructions
pause
