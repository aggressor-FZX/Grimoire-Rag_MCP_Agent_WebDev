"""
Test script for the Enhanced Reflex Development Agent

This script demonstrates the capabilities of the Composio-powered Reflex development tools.
"""

import asyncio
import time
from reflex_dev_agent_enhanced import (
    ReflexWebInspector,
    ReflexAPIClient,
    ReflexDevAgent,
    app_context
)

async def test_web_inspector():
    """Test the Playwright-powered web inspector."""
    print("🔍 Testing Web Inspector...")
    
    inspector = ReflexWebInspector()
    
    try:
        # Test with a simple webpage first
        result = await inspector.inspect_page("https://httpbin.org/html")
        
        if 'error' not in result:
            print("✅ Web inspector working!")
            print(f"  - Page title: {result.get('title', 'N/A')}")
            print(f"  - Components found: {len(result.get('components', []))}")
            print(f"  - State data: {bool(result.get('state_data'))}")
        else:
            print(f"❌ Web inspector error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Web inspector exception: {e}")
    finally:
        await inspector.cleanup()

def test_api_client():
    """Test the Reflex API client."""
    print("🌐 Testing API Client...")
    
    client = ReflexAPIClient("https://httpbin.org")
    
    # Test with a mock endpoint
    result = client.get_state("/json")
    
    if result['success']:
        print("✅ API client working!")
        print(f"  - Response received: {bool(result.get('state'))}")
    else:
        print(f"❌ API client error: {result['error']}")

def test_dev_agent():
    """Test the development agent's suggestion system."""
    print("🤖 Testing Development Agent...")
    
    agent = ReflexDevAgent()
    
    test_requests = [
        "I need to debug why my button isn't showing up",
        "How do I check if the state is updating correctly?",
        "The component styling looks wrong",
        "I want to build a new dashboard component"
    ]
    
    for request in test_requests:
        suggestion = agent.analyze_request(request)
        workflow = agent.suggest_workflow(request)
        
        print(f"\\n📝 Request: {request}")
        print(f"💡 Suggestion: {suggestion}")
        print(f"🔧 Workflow: {workflow['suggested_workflow'][:2]}...")

async def test_full_workflow():
    """Test a complete development workflow."""
    print("\\n🚀 Testing Full Development Workflow...")
    
    # Set up context
    from reflex_dev_agent_enhanced import set_app_context
    
    context_result = set_app_context(
        base_url="http://localhost:3000",
        api_base="http://localhost:8000",
        current_page="/dashboard"
    )
    
    print(f"✅ Context set: {context_result['success']}")
    
    # Test agent suggestions
    agent = ReflexDevAgent()
    workflow_suggestion = agent.suggest_workflow(
        "I'm building a dashboard and need to debug state synchronization"
    )
    
    print(f"🎯 Suggested workflow for dashboard debugging:")
    for i, step in enumerate(workflow_suggestion['suggested_workflow'], 1):
        print(f"  {i}. {step}")

def main():
    """Run all tests."""
    print("🧪 ENHANCED REFLEX DEVELOPMENT AGENT - TEST SUITE")
    print("=" * 60)
    
    # Test individual components
    test_api_client()
    print()
    
    test_dev_agent()
    print()
    
    # Test async components
    print("⚡ Running async tests...")
    asyncio.run(test_web_inspector())
    asyncio.run(test_full_workflow())
    
    print("\\n✅ All tests completed!")
    print("\\n📋 Next Steps:")
    print("  1. Start your Reflex app: `reflex run`")
    print("  2. Use the MCP tools to inspect your live application")
    print("  3. Compare DOM state vs API state for debugging")
    print("  4. Iterate faster with real-time feedback!")

if __name__ == "__main__":
    main()
