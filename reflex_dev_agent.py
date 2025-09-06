#!/usr/bin/env python3
"""
Reflex Dev Agent - Working Version with Subprocess Playwright
"""

import time
import requests
import subprocess
import json
import sys
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("reflex-dev-agent-working")

@mcp.tool()
def reflex_dev_test() -> dict:
    """Simple test tool to verify MCP is working."""
    return {
        'status': 'success',
        'message': 'Reflex Dev Agent Working Version',
        'timestamp': time.time(),
        'playwright_working': True,
        'tools_available': ['test', 'web_check', 'playwright_inspect', 'context_info']
    }

@mcp.tool()
def simple_web_check(url: str = "https://www.google.com") -> dict:
    """Simple web check using requests."""
    try:
        response = requests.get(url, timeout=10)
        return {
            'status': 'success',
            'url': url,
            'status_code': response.status_code,
            'content_length': len(response.content),
            'title_found': '<title>' in response.text,
            'has_react': 'react' in response.text.lower(),
            'timestamp': time.time()
        }
    except Exception as e:
        return {
            'status': 'error',
            'url': url,
            'error': str(e),
            'timestamp': time.time()
        }

@mcp.tool()
def playwright_web_inspect(url: str, get_title_only: bool = True) -> dict:
    """Web inspection using Playwright via subprocess to avoid async conflicts."""
    try:
        # Create a Python script to run Playwright in a separate process
        script = f'''
import asyncio
import json
from playwright.async_api import async_playwright

async def inspect_website():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("{url}", wait_until="domcontentloaded", timeout=15000)
            
            result = {{
                "status": "success",
                "url": "{url}",
                "title": await page.title(),
                "final_url": page.url
            }}
            
            if not {get_title_only}:
                viewport = page.viewport_size
                body_text = await page.inner_text("body") if await page.query_selector("body") else ""
                forms = await page.query_selector_all("form")
                buttons = await page.query_selector_all("button")
                inputs = await page.query_selector_all("input")
                
                meta_desc_elem = await page.query_selector("meta[name=description]")
                meta_description = await meta_desc_elem.get_attribute("content") if meta_desc_elem else None
                
                result.update({{
                    "viewport": viewport,
                    "body_text_length": len(body_text),
                    "has_forms": len(forms) > 0,
                    "form_count": len(forms),
                    "has_buttons": len(buttons) > 0,
                    "button_count": len(buttons),
                    "input_count": len(inputs),
                    "meta_description": meta_description
                }})
            
            await browser.close()
            return result
            
    except Exception as e:
        return {{
            "status": "error",
            "url": "{url}",
            "error": str(e)
        }}

result = asyncio.run(inspect_website())
print(json.dumps(result))
'''
        
        # Run the script in a subprocess
        process = subprocess.run(
            [sys.executable, '-c', script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if process.returncode == 0:
            result = json.loads(process.stdout.strip())
            result['timestamp'] = time.time()
            return result
        else:
            return {
                'status': 'error',
                'url': url,
                'error': f'Subprocess failed: {process.stderr}',
                'timestamp': time.time()
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'url': url,
            'error': str(e),
            'timestamp': time.time()
        }

@mcp.tool()
def reflex_context_info() -> dict:
    """Get information about typical Reflex development context."""
    return {
        'status': 'info',
        'message': 'Reflex development context information',
        'typical_urls': {
            'frontend': 'http://localhost:3000',
            'backend_api': 'http://localhost:8000',
            'state_endpoint': '/api/get_state'
        },
        'common_commands': {
            'start_dev': 'reflex run',
            'build': 'reflex build', 
            'deploy': 'reflex deploy'
        },
        'development_patterns': {
            'state_class': 'class MyState(rx.State): ...',
            'event_handler': '@rx.event\\ndef handle_event(self): ...',
            'form_submit': 'on_submit=MyState.handle_submit',
            'conditional_render': 'rx.cond(condition, true_component, false_component)'
        },
        'timestamp': time.time()
    }

if __name__ == "__main__":
    print("Starting Reflex Dev Agent Working Version...")
    print("Available tools:")
    print("- reflex_dev_test: Test if MCP tools are working")
    print("- simple_web_check: Basic web connectivity test")
    print("- playwright_web_inspect: Full web page inspection (subprocess)")
    print("- reflex_context_info: Reflex development context")
    print()
    
    mcp.run()
