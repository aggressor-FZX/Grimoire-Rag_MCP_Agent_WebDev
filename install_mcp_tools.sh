#!/bin/bash
# MCP Tools Installation Script
# Usage: ./install_mcp_tools.sh [target_directory]

set -e

TARGET_DIR="${1:-$(pwd)}"
SOURCE_DIR="j:/Desktop/ConnectAI/Grimoire3"

echo "🚀 Installing MCP Tools to: $TARGET_DIR"

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

echo "📁 Creating VS Code configuration..."
mkdir -p .vscode

# Copy MCP servers
echo "📋 Copying MCP server files..."
cp "$SOURCE_DIR/composio_docs_server_enhanced.py" .
cp "$SOURCE_DIR/reflex_docs_server_enhanced.py" .
cp "$SOURCE_DIR/reflex_dev_agent.py" .

# Copy databases (optional, for faster startup)
if [ -d "$SOURCE_DIR/chroma_db" ]; then
    echo "💾 Copying Composio documentation database..."
    cp -r "$SOURCE_DIR/chroma_db" .
fi

if [ -d "$SOURCE_DIR/reflex_chroma_db" ]; then
    echo "💾 Copying Reflex documentation database..."
    cp -r "$SOURCE_DIR/reflex_chroma_db" .
fi

# Set up Python environment
echo "🐍 Setting up Python environment..."
python -m venv venv

# Activate virtual environment (Windows Git Bash)
if [[ "$OSTYPE" == "msys" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --quiet fastmcp playwright requests beautifulsoup4
pip install --quiet sentence-transformers chromadb tiktoken

# Install Playwright browser
echo "🌐 Installing Playwright Chromium..."
playwright install chromium

# Create MCP configuration
echo "⚙️ Creating MCP configuration..."
cat > .vscode/mcp.json << 'EOF'
{
  "servers": {
    "composio-docs": {
      "command": "./venv/Scripts/python.exe",
      "args": ["composio_docs_server_enhanced.py"],
      "type": "stdio",
      "cwd": "${workspaceFolder}",
      "env": {}
    },
    "reflex-docs": {
      "command": "./venv/Scripts/python.exe",
      "args": ["reflex_docs_server_enhanced.py"],
      "type": "stdio",
      "cwd": "${workspaceFolder}",
      "env": {}
    },
    "reflex-dev-agent": {
      "command": "./venv/Scripts/python.exe",
      "args": ["reflex_dev_agent.py"],
      "type": "stdio",
      "cwd": "${workspaceFolder}",
      "env": {}
    }
  },
  "inputs": []
}
EOF

echo "✅ MCP Tools installation complete!"
echo ""
echo "🔄 Next steps:"
echo "1. Restart VS Code to load MCP configuration"
echo "2. Test tools with: mcp_reflex-dev-ag_reflex_dev_test()"
echo "3. Search docs with: mcp_reflex-docs-e_search_reflex_docs('your query')"
echo ""
echo "📋 Available tools:"
echo "  - Reflex development agent (web inspection)"
echo "  - Reflex documentation search"
echo "  - Composio documentation search"
echo ""
echo "📚 See MCP_SETUP_GUIDE.md for detailed usage instructions"
