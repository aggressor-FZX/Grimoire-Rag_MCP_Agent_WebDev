# Grimoire3 MCP Tools - Clean Setup Guide

## 📁 **Cleaned Directory Structure**

```
j:\Desktop\ConnectAI\Grimoire3\
├── .vscode/
│   └── mcp.json                           # MCP server configuration
├── venv/                                  # Python virtual environment
├── chroma_db/                            # Composio documentation database
├── reflex_chroma_db/                     # Reflex documentation database
├── 🔧 MCP SERVERS (3 active):
│   ├── composio_docs_server_enhanced.py  # Composio documentation search
│   ├── reflex_docs_server_enhanced.py    # Reflex documentation search  
│   └── reflex_dev_agent.py              # Web inspection & dev tools
├── 📋 EXAMPLES:
│   ├── reflex_form_example.py           # Complex Reflex form with validation
│   └── simple_reflex_form.py            # Basic Reflex form
├── 📚 DOCUMENTATION:
│   ├── README.md
│   ├── IMPLEMENTATION_STATUS.md
│   └── ENHANCED_*.md files
└── ⚙️ SETUP:
    ├── setup.sh / setup.bat
    ├── .env.template
    └── requirements files in setup scripts
```

## 🚀 **Active MCP Servers & Ports**

### **1. Composio Documentation Server**
- **File**: `composio_docs_server_enhanced.py`
- **Purpose**: Search Composio documentation and examples
- **Port**: N/A (STDIO communication)
- **Tools Available**: 
  - `mcp_composio-docs_search_composio_docs`
  - `mcp_composio-docs_validate_composio_code`
  - `mcp_composio-docs_composio_intelligent_agent`

### **2. Reflex Documentation Server**
- **File**: `reflex_docs_server_enhanced.py` 
- **Purpose**: Search Reflex documentation and validate code
- **Port**: N/A (STDIO communication)
- **Tools Available**:
  - `mcp_reflex-docs-e_search_reflex_docs`
  - `mcp_reflex-docs-e_validate_reflex_code`
  - `mcp_reflex-docs-e_reflex_intelligent_agent`

### **3. Reflex Development Agent**
- **File**: `reflex_dev_agent.py`
- **Purpose**: Web inspection and Reflex development assistance
- **Port**: N/A (STDIO communication)
- **Reflex Default Ports**: 
  - Frontend: `http://localhost:3000`
  - Backend API: `http://localhost:8000`
- **Tools Available**:
  - `mcp_reflex-dev-ag_reflex_dev_test`
  - `mcp_reflex-dev-ag_simple_web_check`  
  - `mcp_reflex-dev-ag_playwright_web_inspect`
  - `mcp_reflex-dev-ag_reflex_context_info`

## 🔧 **How to Use These MCP Tools in Another VS Code Project**

### **Method 1: Copy the Entire Setup (Recommended)**

1. **Copy the MCP Files**:
   ```bash
   # Copy to your new project folder
   cp j:/Desktop/ConnectAI/Grimoire3/{composio_docs_server_enhanced.py,reflex_docs_server_enhanced.py,reflex_dev_agent.py} /path/to/your/project/
   cp -r j:/Desktop/ConnectAI/Grimoire3/venv /path/to/your/project/
   cp -r j:/Desktop/ConnectAI/Grimoire3/{chroma_db,reflex_chroma_db} /path/to/your/project/
   ```

2. **Create MCP Configuration**:
   Create `.vscode/mcp.json` in your new project:
   ```json
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
   ```

### **Method 2: Install Dependencies Separately**

1. **Set up Python Environment**:
   ```bash
   cd /path/to/your/project
   python -m venv venv
   source venv/Scripts/activate  # Windows
   # source venv/bin/activate    # Linux/Mac
   
   pip install fastmcp playwright requests beautifulsoup4 
   pip install sentence-transformers chromadb tiktoken
   playwright install chromium
   ```

2. **Copy Just the MCP Servers**:
   ```bash
   cp j:/Desktop/ConnectAI/Grimoire3/{composio_docs_server_enhanced.py,reflex_docs_server_enhanced.py,reflex_dev_agent.py} .
   ```

3. **Copy Documentation Databases** (optional for faster startup):
   ```bash
   cp -r j:/Desktop/ConnectAI/Grimoire3/{chroma_db,reflex_chroma_db} .
   ```

### **Method 3: Global MCP Setup**

1. **Create a Global MCP Tools Directory**:
   ```bash
   mkdir ~/mcp-tools
   cp j:/Desktop/ConnectAI/Grimoire3/*.py ~/mcp-tools/
   cp -r j:/Desktop/ConnectAI/Grimoire3/venv ~/mcp-tools/
   ```

2. **Reference in Any Project's `.vscode/mcp.json`**:
   ```json
   {
     "servers": {
       "reflex-dev-agent": {
         "command": "~/mcp-tools/venv/Scripts/python.exe",
         "args": ["~/mcp-tools/reflex_dev_agent.py"],
         "type": "stdio",
         "cwd": "~/mcp-tools",
         "env": {}
       }
     }
   }
   ```

## 🛠️ **Available Tools & Usage**

### **Reflex Development Tools**
```python
# Test if tools are working
mcp_reflex-dev-ag_reflex_dev_test()

# Check if a website is accessible
mcp_reflex-dev-ag_simple_web_check("https://example.com")

# Inspect website with Playwright (full DOM analysis)
mcp_reflex-dev-ag_playwright_web_inspect("https://example.com", get_title_only=False)

# Get Reflex development context
mcp_reflex-dev-ag_reflex_context_info()
```

### **Documentation Search Tools**
```python
# Search Reflex documentation
mcp_reflex-docs-e_search_reflex_docs("how to create forms")

# Validate Reflex code
mcp_reflex-docs-e_validate_reflex_code("rx.form(...)")

# Get intelligent Reflex assistance
mcp_reflex-docs-e_reflex_intelligent_agent("create a login form")

# Search Composio documentation
mcp_composio-docs_search_composio_docs("authentication")
```

## 🔄 **Restarting VS Code**

After copying MCP files to a new project:
1. **Restart VS Code** to load the new MCP configuration
2. **Verify tools are available** by checking for `mcp_` prefixed functions
3. **Test connectivity** with the test functions

## 📝 **Notes**

- **MCP servers use STDIO communication** (not HTTP ports)
- **Databases will rebuild automatically** if missing (takes 1-2 minutes)
- **Playwright requires Chromium** to be installed (`playwright install chromium`)
- **Virtual environment paths** may need adjustment for different OS
- **All tools are prefixed** with `mcp_server-name_` for identification

## 🚨 **Troubleshooting**

1. **Tools not appearing**: Restart VS Code completely
2. **Import errors**: Check virtual environment activation and dependencies
3. **Playwright errors**: Run `playwright install chromium`
4. **Database errors**: Delete and let them rebuild automatically
5. **Path issues**: Ensure all file paths in `mcp.json` are correct for your system
