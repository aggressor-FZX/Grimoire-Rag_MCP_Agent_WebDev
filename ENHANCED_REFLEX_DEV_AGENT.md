OBSOLETE: moved to obsoleate/ folder.
# Enhanced Reflex Development Agent with Composio Integration

## 🚀 Overview

This enhanced development agent provides **live web inspection capabilities** for Reflex development using Composio-powered tools. It combines Playwright for DOM inspection with Reflex API integration, allowing you to see your website in its true hydrated form for faster iteration.

## ✨ Key Features

### **🔍 Hydrated DOM Inspection**
- **Playwright Integration**: Full browser automation for real DOM access
- **React Hydration Detection**: Waits for React/Reflex hydration to complete
- **Component Analysis**: Extracts Reflex component hierarchy and state
- **Visual State Inspection**: See exactly what users see in the browser

### **🌐 Reflex API Integration**
- **State Monitoring**: Direct access to Reflex application state via API
- **Event Triggering**: Programmatically trigger Reflex events and state changes
- **Structured Data Access**: Reliable API-based state inspection

### **🤖 Intelligent Agent Coordination**
- **Context-Aware Tool Selection**: Agent automatically chooses between DOM inspection and API calls
- **Workflow Suggestions**: Intelligent recommendations based on development goals
- **Debugging Assistance**: Automated comparison between DOM state and API state

## 🛠️ Available Tools

### **MCP Tools (VS Code Integration)**

1. **`reflex_dev_inspect_page`**
   - Inspect live Reflex pages with full DOM access
   - Parameters: `url`, `selector`, `use_current_context`
   - Returns: Hydrated DOM structure, components, and state

2. **`reflex_dev_get_state`**
   - Fetch current application state via Reflex API
   - Parameters: `endpoint`
   - Returns: Structured state data

3. **`reflex_dev_compare_state`**
   - Compare DOM representation vs API state
   - Parameters: `page_path`, `selector`
   - Returns: Comparison analysis and potential sync issues

4. **`reflex_dev_configure`**
   - Configure development environment URLs
   - Parameters: `frontend_url`, `api_url`, `current_page`
   - Returns: Configuration confirmation

5. **`reflex_dev_agent_suggest`**
   - Get intelligent workflow suggestions
   - Parameters: `development_goal`
   - Returns: Recommended tools and workflow steps

### **Composio Tools (Optional - requires API key)**

- **`inspect_hydrated_page`**: Advanced Playwright-powered inspection
- **`get_reflex_state`**: API state fetching with retry logic
- **`trigger_reflex_event`**: Event triggering and response monitoring
- **`compare_dom_vs_state`**: Automated state synchronization analysis
- **`set_app_context`**: Development environment configuration

## 🚦 Quick Start

### **1. Installation**
```bash
# Install required packages
pip install composio-core playwright fastmcp

# Install Playwright browsers
playwright install
```

### **2. Basic Usage**
```python
from reflex_dev_agent_enhanced import ReflexWebInspector, ReflexAPIClient

# Initialize inspector
inspector = ReflexWebInspector()

# Inspect your live Reflex app
result = await inspector.inspect_page("http://localhost:3000/dashboard")

# Check API state
api_client = ReflexAPIClient("http://localhost:8000")
state = api_client.get_state("/api/get_state")
```

### **3. VS Code MCP Integration**
The agent is automatically available in VS Code through the MCP configuration. Use the tools directly in your development workflow.

## 🔧 Development Workflows

### **Component Development**
1. **`reflex_dev_configure`** - Set up your app URLs
2. **`reflex_dev_inspect_page`** - Examine component rendering
3. **`reflex_dev_get_state`** - Check internal state
4. **`reflex_dev_compare_state`** - Verify state-UI synchronization

### **Debugging Issues**
1. **`reflex_dev_compare_state`** - Identify DOM vs state discrepancies
2. **`reflex_dev_inspect_page`** - Analyze specific elements
3. **`reflex_dev_get_state`** - Examine state variables

### **UI Development**
1. **`reflex_dev_inspect_page`** - Visual component analysis
2. **`reflex_dev_get_state`** - State-driven UI validation

### **State Management**
1. **`reflex_dev_get_state`** - Monitor state changes
2. **`trigger_reflex_event`** - Test event handling
3. **`reflex_dev_compare_state`** - Verify updates

## 📊 Agent Intelligence

The development agent analyzes your requests and suggests optimal tools:

```python
# Example intelligent suggestions
agent_suggest("I need to debug why my button isn't showing up")
# → Suggests: compare_dom_vs_state for DOM vs state analysis

agent_suggest("How do I check if state is updating correctly?")
# → Suggests: get_reflex_state for internal state examination

agent_suggest("The component styling looks wrong")
# → Suggests: inspect_hydrated_page for visual analysis
```

## 🔄 Live Development Loop

1. **Code Changes** → Make changes to your Reflex app
2. **Live Inspection** → Use `reflex_dev_inspect_page` to see hydrated DOM
3. **State Verification** → Use `reflex_dev_get_state` to check internal state
4. **Issue Detection** → Use `reflex_dev_compare_state` to find discrepancies
5. **Iteration** → Fix issues and repeat

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VS Code MCP Interface                    │
├─────────────────────────────────────────────────────────────┤
│                  Enhanced Reflex Agent                     │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Playwright    │   Reflex API    │   Intelligent Agent     │
│   Web Inspector │   Client        │   Coordinator           │
├─────────────────┼─────────────────┼─────────────────────────┤
│ • DOM Analysis  │ • State Fetch   │ • Tool Selection        │
│ • Component     │ • Event Trigger │ • Workflow Suggestions  │
│   Extraction    │ • API Calls     │ • Context Analysis      │
│ • Visual State  │ • Structured    │ • Debugging Assistance  │
│   Inspection    │   Data Access   │                         │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
                           ▼
                  Live Reflex Application
                  Frontend + Backend APIs
```

## 🧪 Testing

```bash
# Run the test suite
python test_reflex_dev_agent.py

# Test individual components
python -c "
from reflex_dev_agent_enhanced import ReflexDevAgent
agent = ReflexDevAgent()
print(agent.analyze_request('Debug button rendering'))
"
```

## 📝 Configuration

### **Environment Setup**
```python
# Set development context
reflex_dev_configure(
    frontend_url="http://localhost:3000",
    api_url="http://localhost:8000", 
    current_page="/dashboard"
)
```

### **Composio Setup (Optional)**
```bash
# For enhanced Composio features
export COMPOSIO_API_KEY="your-api-key"
# or
composio login
```

## 🔍 Example: Debugging a Dashboard

```python
# 1. Configure your app
reflex_dev_configure(
    frontend_url="http://localhost:3000",
    current_page="/dashboard"
)

# 2. Inspect the live page
page_state = reflex_dev_inspect_page("/dashboard")
print(f"Found {len(page_state['components'])} components")

# 3. Check API state
api_state = reflex_dev_get_state()
print(f"State variables: {api_state['state'].keys()}")

# 4. Compare for inconsistencies
comparison = reflex_dev_compare_state("/dashboard")
if comparison['analysis']['potential_sync_issues']:
    print("⚠️ Potential state synchronization issues detected!")
```

## 🚀 Benefits

- **🔄 Faster Iteration**: See changes in real-time with live inspection
- **🐛 Better Debugging**: Compare DOM state vs internal state automatically
- **🎯 Targeted Development**: AI suggests the right tools for your task
- **📊 Complete Visibility**: Full access to hydrated React/Reflex state
- **⚡ Seamless Integration**: Works directly in VS Code through MCP

## 📚 Integration with Existing Servers

This enhanced agent works alongside your existing documentation servers:
- **Composio Docs Server**: For Composio development guidance
- **Reflex Docs Server**: For Reflex framework documentation
- **Enhanced Dev Agent**: For live application inspection and debugging

Together, they provide a comprehensive development environment for modern web applications! 🎉
