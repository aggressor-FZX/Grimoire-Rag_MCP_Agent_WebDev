"""
Enhanced Reflex Development Agent with Composio Integration

This module provides dynamic web inspection capabilities for Reflex development
using Composio tools for both Playwright DOM access and Reflex API integration.
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from playwright.async_api import async_playwright, Page, Browser
from composio import ComposioToolSet, action
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize MCP and Composio (conditionally)
mcp = FastMCP("reflex-dev-agent")

# Try to initialize Composio with the API key from environment
try:
    composio_api_key = os.getenv('COMPOSIO_API_KEY')
    if composio_api_key:
        # Set the API key in the environment if it's not already there
        os.environ['COMPOSIO_API_KEY'] = composio_api_key
        toolset = ComposioToolSet()
        COMPOSIO_AVAILABLE = True
        print("✓ Composio initialized successfully with API key from .env")
    else:
        raise ValueError("COMPOSIO_API_KEY not found in environment variables")
        
except Exception as e:
    toolset = None
    COMPOSIO_AVAILABLE = False
    print(f"! Composio not available: {e}")
    print("   Make sure COMPOSIO_API_KEY is set in your .env file")
    print("   Continuing with basic functionality...")


@dataclass
class ReflexAppContext:
    """Context about the current Reflex application being developed."""
    base_url: str = "http://localhost:3000"
    api_base: str = "http://localhost:8000"
    current_page: str = "/"
    state_endpoint: str = "/api/get_state"
    components_endpoint: str = "/api/get_components"


class ReflexWebInspector:
    """
    Playwright-powered web inspector for hydrated Reflex applications.
    This class manages a persistent browser instance but creates a new page
    for each inspection to ensure thread safety and avoid state conflicts.
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self._lock = asyncio.Lock()

    async def initialize_browser(self, headless: bool = True):
        """Initialize Playwright and the browser if not already running."""
        async with self._lock:
            if not self.playwright:
                self.playwright = await async_playwright().start()
            if not self.browser or not self.browser.is_connected():
                try:
                    self.browser = await self.playwright.chromium.launch(headless=headless)
                except Exception as e:
                    print(f"Failed to launch browser: {e}")
                    # Attempt to install browsers as a fallback
                    print("Attempting to install Playwright browsers...")
                    # Using os.system is a simple approach for this script
                    import subprocess
                    subprocess.run(["playwright", "install"], check=True)
                    self.browser = await self.playwright.chromium.launch(headless=headless)

    async def cleanup(self):
        """Clean up Playwright resources."""
        async with self._lock:
            if self.browser and self.browser.is_connected():
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
    async def inspect_page(self, url: str, selector: Optional[str] = None) -> Dict[str, Any]:
        """Inspect a Reflex page and return hydrated DOM information."""
        await self.initialize_browser()
        if not self.browser:
            return {'error': 'Browser could not be initialized.', 'url': url}

        page = None
        console_logs = []
        try:
            page = await self.browser.new_page()
            page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

            await page.goto(url, wait_until='networkidle', timeout=20000)
            await page.wait_for_function("window.React !== undefined", timeout=20000)
            
            result = {
                'url': url,
                'title': await page.title(),
                'viewport': await page.viewport_size(),
                'timestamp': time.time(),
                'console_logs': console_logs,
            }
            
            if selector:
                element = await page.query_selector(selector)
                if element:
                    result['element'] = {
                        'text': await element.text_content(),
                        'html': await element.inner_html(),
                        'attributes': await element.evaluate('el => Object.fromEntries(Array.from(el.attributes).map(attr => [attr.name, attr.value]))'),
                    }
            else:
                result['body_html'] = await page.inner_html('body')
                result['components'] = await self._extract_reflex_components(page)
                result['state_data'] = await self._extract_state_data(page)
                
            return result
            
        except Exception as e:
            error_report = {'error': str(e), 'url': url}
            if console_logs:
                error_report['console_logs'] = console_logs
            return error_report
        finally:
            if page:
                await page.close()
    
    async def _extract_reflex_components(self, page: Page) -> List[Dict[str, Any]]:
        """Extract Reflex component information from the DOM."""
        try:
            return await page.evaluate("""
                () => {
                    const components = [];
                    const elements = document.querySelectorAll('[data-reflex], [data-component], .reflex-component');
                    elements.forEach(el => {
                        components.push({
                            tagName: el.tagName.toLowerCase(),
                            className: el.className,
                            id: el.id,
                            dataset: {...el.dataset},
                            textContent: el.textContent?.substring(0, 100),
                            children: el.children.length
                        });
                    });
                    return components;
                }
            """)
        except Exception:
            return []
    
    async def _extract_state_data(self, page: Page) -> Dict[str, Any]:
        """Extract React/Reflex state information from the page."""
        try:
            return await page.evaluate("""
                () => {
                    const reactRoot = document.querySelector('#root');
                    if (reactRoot && reactRoot._reactInternalFiber) {
                        return { type: 'react_state', available: true };
                    }
                    const globalState = {};
                    if (window.reflexState) globalState.reflexState = window.reflexState;
                    if (window.appState) globalState.appState = window.appState;
                    return globalState;
                }
            """)
        except Exception:
            return {}


class ReflexAPIClient:
    """Client for interacting with Reflex application APIs."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def get_state(self, endpoint: str = "/api/get_state") -> Dict[str, Any]:
        """Fetch application state from Reflex API."""
        try:
            url = urljoin(self.base_url, endpoint)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return {
                'success': True,
                'state': response.json(),
                'timestamp': time.time()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def trigger_event(self, endpoint: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a Reflex event through the API."""
        try:
            url = urljoin(self.base_url, endpoint)
            response = self.session.post(url, json=event_data, timeout=10)
            response.raise_for_status()
            return {
                'success': True,
                'response': response.json(),
                'timestamp': time.time()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }


# Initialize global instances
web_inspector = ReflexWebInspector()
api_client = ReflexAPIClient()
app_context = ReflexAppContext()


# Composio Tools (conditional)
def composio_action_decorator(toolname):
    """Conditional decorator for Composio actions."""
    def decorator(func):
        if COMPOSIO_AVAILABLE:
            return action(toolname=toolname)(func)
        else:
            # Return the function as-is if Composio is not available
            return func
    return decorator


# Core inspection functions (used by both Composio and MCP tools)
def inspect_hydrated_page_sync(
    url: str,
    selector: Optional[str] = None,
    wait_for_hydration: bool = True
) -> Dict[str, Any]:
    """
    Synchronous wrapper for inspecting a live Reflex application page using Playwright.
    
    Args:
        url: The URL to inspect (e.g., "http://localhost:3000/dashboard")
        selector: Optional CSS selector to focus on specific element
        wait_for_hydration: Whether to wait for React hydration to complete
        
    Returns:
        Detailed information about the page state, components, and DOM structure
    """
    try:
        # Use asyncio.run to handle the async function
        async def _inspect():
            return await web_inspector.inspect_page(url, selector)
        
        return asyncio.run(_inspect())
    except Exception as e:
        return {'error': f'Inspection failed: {str(e)}', 'url': url}


def inspect_hydrated_page(
    url: str,
    selector: Optional[str] = None,
    wait_for_hydration: bool = True
) -> Dict[str, Any]:
    """
    Inspect a live Reflex application page using Playwright for full DOM access.
    
    This tool provides deep inspection of the hydrated React/Reflex application,
    allowing you to see the actual rendered state, component hierarchy, and
    interactive elements as they appear in the browser.
    
    Args:
        url: The URL to inspect (e.g., "http://localhost:3000/dashboard")
        selector: Optional CSS selector to focus on specific element
        wait_for_hydration: Whether to wait for React hydration to complete
        
    Returns:
        Detailed information about the page state, components, and DOM structure
    """
    async def _inspect():
        return await web_inspector.inspect_page(url, selector)
    
    # Run async function in event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, use create_task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _inspect())
                return future.result()
        else:
            return asyncio.run(_inspect())
    except Exception as e:
        return {'error': f'Inspection failed: {str(e)}'}


def simple_web_inspect(url: str) -> Dict[str, Any]:
    """
    Simple web inspection using requests (fallback when Playwright fails).
    
    Args:
        url: The URL to inspect
        
    Returns:
        Basic information about the page
    """
    try:
        import requests
        response = requests.get(url, timeout=10)
        return {
            'status': 'success',
            'url': url,
            'status_code': response.status_code,
            'content_length': len(response.text),
            'title_found': '<title>' in response.text,
            'has_react': 'React' in response.text or 'react' in response.text,
            'timestamp': time.time()
        }
    except Exception as e:
        return {
            'status': 'error',
            'url': url,
            'error': str(e),
            'timestamp': time.time()
        }


def get_reflex_state(
    endpoint: str = "/api/get_state",
    api_base: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch structured state data from a Reflex application API.
    
    This tool provides reliable access to the application's internal state
    through dedicated API endpoints, giving you programmatic access to
    variables, component states, and business logic data.
    
    Args:
        endpoint: API endpoint to fetch state from (default: "/api/get_state")
        api_base: Base API URL (defaults to app_context.api_base)
        
    Returns:
        Current application state data
    """
    if api_base:
        api_client.base_url = api_base
    elif app_context.api_base:
        api_client.base_url = app_context.api_base
        
    return api_client.get_state(endpoint)


def trigger_reflex_event(
    endpoint: str,
    event_data: Dict[str, Any],
    api_base: Optional[str] = None
) -> Dict[str, Any]:
    """
    Trigger a Reflex application event through the API.
    
    This tool allows you to programmatically trigger events in the Reflex
    application, such as button clicks, form submissions, or state changes.
    
    Args:
        endpoint: API endpoint for the event (e.g., "/api/trigger/button_click")
        event_data: Data to send with the event
        api_base: Base API URL (defaults to app_context.api_base)
        
    Returns:
        Event execution result and any state changes
    """
    if api_base:
        api_client.base_url = api_base
    elif app_context.api_base:
        api_client.base_url = app_context.api_base
        
    return api_client.trigger_event(endpoint, event_data)


def compare_dom_vs_state(
    page_url: str,
    state_endpoint: str = "/api/get_state",
    selector: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare the hydrated DOM representation with the API state data.
    
    This tool helps identify discrepancies between what's displayed in the
    browser and what the application state indicates should be displayed.
    
    Args:
        page_url: URL of the page to inspect
        state_endpoint: API endpoint to fetch state from
        selector: Optional selector to focus comparison on specific elements
        
    Returns:
        Comparison analysis between DOM and state
    """
    # Get DOM data
    dom_data = inspect_hydrated_page(page_url, selector)
    
    # Get state data
    state_data = get_reflex_state(state_endpoint)
    
    comparison = {
        'timestamp': time.time(),
        'page_url': page_url,
        'dom_inspection': dom_data,
        'api_state': state_data,
        'analysis': {
            'dom_success': 'error' not in dom_data,
            'api_success': state_data.get('success', False),
            'hydration_complete': 'components' in dom_data
        }
    }
    
    # Add simple comparison logic
    if comparison['analysis']['dom_success'] and comparison['analysis']['api_success']:
        # Compare component counts, state values, etc.
        dom_components = len(dom_data.get('components', []))
        api_state_keys = len(state_data.get('state', {}))
        
        comparison['analysis']['metrics'] = {
            'dom_components_found': dom_components,
            'api_state_variables': api_state_keys,
            'potential_sync_issues': dom_components == 0 and api_state_keys > 0
        }
    
    return comparison


def set_app_context(
    base_url: str = "http://localhost:3000",
    api_base: str = "http://localhost:8000",
    current_page: str = "/",
    state_endpoint: str = "/api/get_state"
) -> Dict[str, Any]:
    """
    Configure the context for the Reflex application being developed.
    
    This tool sets up the URLs and endpoints for the current development session.
    
    Args:
        base_url: Base URL of the Reflex frontend (default: "http://localhost:3000")
        api_base: Base URL of the Reflex API (default: "http://localhost:8000")
        current_page: Current page being developed (default: "/")
        state_endpoint: State API endpoint (default: "/api/get_state")
        
    Returns:
        Updated application context
    """
    global app_context, api_client
    
    app_context.base_url = base_url
    app_context.api_base = api_base
    app_context.current_page = current_page
    app_context.state_endpoint = state_endpoint
    
    # Update API client
    api_client.base_url = api_base
    
    return {
        'success': True,
        'context': {
            'base_url': app_context.base_url,
            'api_base': app_context.api_base,
            'current_page': app_context.current_page,
            'state_endpoint': app_context.state_endpoint
        },
        'message': 'Application context updated successfully'
    }


# MCP Tools for the agent
@mcp.tool()
def reflex_dev_test() -> dict:
    """
    Simple test tool to verify MCP is working.
    
    Returns:
        Test response
    """
    return {
        'status': 'success',
        'message': 'MCP tools are working correctly',
        'timestamp': time.time(),
        'playwright_available': True,
        'composio_available': COMPOSIO_AVAILABLE
    }


@mcp.tool()
def reflex_dev_simple_web_check(url: str = "https://www.google.com") -> dict:
    """
    Simple web check using requests (no Playwright).
    
    Args:
        url: URL to check
        
    Returns:
        Basic web response information
    """
    return simple_web_inspect(url)


@mcp.tool()
def reflex_dev_inspect_page(
    url: str,
    selector: str = None,
    use_current_context: bool = True
) -> dict:
    """
    Inspect a live Reflex page for development and debugging.
    
    Args:
        url: Full URL or relative path (if using current context)
        selector: Optional CSS selector to focus on specific element
        use_current_context: Whether to prepend app_context.base_url to relative URLs
        
    Returns:
        Detailed page inspection results including hydrated DOM and components
    """
    if use_current_context and not url.startswith('http'):
        full_url = urljoin(app_context.base_url, url)
    else:
        full_url = url
    
    # Try Playwright first, fall back to simple inspection
    try:
        return inspect_hydrated_page_sync(full_url, selector)
    except Exception as e:
        return {
            'error': f'Playwright inspection failed: {str(e)}',
            'fallback_result': simple_web_inspect(full_url),
            'url': full_url
        }


@mcp.tool()
def reflex_dev_get_state(endpoint: str = None) -> dict:
    """
    Fetch current Reflex application state via API.
    
    Args:
        endpoint: Optional custom endpoint (defaults to app_context.state_endpoint)
        
    Returns:
        Current application state data
    """
    endpoint = endpoint or app_context.state_endpoint
    return get_reflex_state(endpoint)


@mcp.tool()
def reflex_dev_compare_state(
    page_path: str = None,
    selector: str = None
) -> dict:
    """
    Compare DOM state vs API state for development debugging.
    
    Args:
        page_path: Page path to inspect (defaults to app_context.current_page)
        selector: Optional CSS selector to focus comparison
        
    Returns:
        Comparison analysis between what's rendered and what the API reports
    """
    page_path = page_path or app_context.current_page
    page_url = urljoin(app_context.base_url, page_path)
    
    return compare_dom_vs_state(page_url, app_context.state_endpoint, selector)


@mcp.tool()
def reflex_dev_configure(
    frontend_url: str = "http://localhost:3000",
    api_url: str = "http://localhost:8000",
    current_page: str = "/"
) -> dict:
    """
    Configure the Reflex development environment settings.
    
    Args:
        frontend_url: URL where the Reflex frontend is running
        api_url: URL where the Reflex API/backend is running
        current_page: Current page being developed
        
    Returns:
        Configuration confirmation
    """
    return set_app_context(frontend_url, api_url, current_page)


class ReflexDevAgent:
    """Intelligent agent that chooses between DOM inspection and API calls."""
    
    def __init__(self):
        self.tools = {
            'inspect_page': inspect_hydrated_page,
            'get_state': get_reflex_state,
            'trigger_event': trigger_reflex_event,
            'compare_state': compare_dom_vs_state,
            'set_context': set_app_context
        }
    
    def analyze_request(self, request: str) -> str:
        """Analyze a development request and suggest the best approach."""
        request_lower = request.lower()
        
        # DOM inspection indicators
        dom_keywords = ['visual', 'render', 'display', 'css', 'style', 'layout', 'component', 'element', 'click', 'interact']
        
        # API state indicators  
        api_keywords = ['state', 'data', 'variable', 'value', 'update', 'change', 'logic', 'function']
        
        # Debugging indicators
        debug_keywords = ['debug', 'error', 'issue', 'problem', 'not working', 'broken', 'compare']
        
        dom_score = sum(1 for kw in dom_keywords if kw in request_lower)
        api_score = sum(1 for kw in api_keywords if kw in request_lower)
        debug_score = sum(1 for kw in debug_keywords if kw in request_lower)
        
        if debug_score > 0:
            return "Use compare_dom_vs_state to identify discrepancies between what's displayed and the internal state."
        elif dom_score > api_score:
            return "Use inspect_hydrated_page to analyze the rendered DOM, component hierarchy, and visual state."
        elif api_score > dom_score:
            return "Use get_reflex_state to examine the internal application state and data."
        else:
            return "Consider using both inspect_hydrated_page and get_reflex_state for comprehensive analysis."
    
    def suggest_workflow(self, development_goal: str) -> Dict[str, Any]:
        """Suggest a development workflow based on the goal."""
        workflows = {
            'component_development': [
                'set_app_context',
                'inspect_hydrated_page',
                'get_reflex_state', 
                'compare_dom_vs_state'
            ],
            'debugging': [
                'compare_dom_vs_state',
                'inspect_hydrated_page',
                'get_reflex_state'
            ],
            'state_management': [
                'get_reflex_state',
                'trigger_reflex_event',
                'compare_dom_vs_state'
            ],
            'ui_development': [
                'inspect_hydrated_page',
                'get_reflex_state'
            ]
        }
        
        # Simple keyword matching for workflow suggestion
        goal_lower = development_goal.lower()
        
        if any(kw in goal_lower for kw in ['debug', 'error', 'issue', 'problem']):
            workflow = workflows['debugging']
        elif any(kw in goal_lower for kw in ['state', 'data', 'variable']):
            workflow = workflows['state_management'] 
        elif any(kw in goal_lower for kw in ['ui', 'component', 'visual', 'style']):
            workflow = workflows['ui_development']
        else:
            workflow = workflows['component_development']
            
        return {
            'suggested_workflow': workflow,
            'tools_available': list(self.tools.keys()),
            'analysis': self.analyze_request(development_goal)
        }


# Initialize the agent
dev_agent = ReflexDevAgent()


@mcp.tool()
def reflex_dev_agent_suggest(development_goal: str) -> dict:
    """
    Get intelligent suggestions for Reflex development workflow.
    
    Args:
        development_goal: Description of what you're trying to accomplish
        
    Returns:
        Suggested workflow and tool recommendations
    """
    return dev_agent.suggest_workflow(development_goal)


if __name__ == "__main__":
    # Only run the MCP server if this script is executed directly
    print("Starting Reflex Dev Agent MCP Server...")
    mcp.run()
else:
    # If imported, just print that it's available
    print("Reflex Dev Agent module loaded successfully")
