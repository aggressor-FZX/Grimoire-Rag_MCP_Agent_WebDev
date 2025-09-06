#!/usr/bin/env python3
"""
Reflex Dev Agent - Non-blocking with Robust Playwright Integration
"""

import time
import requests
import asyncio
import json
import sys
import os
import signal
import platform
from typing import Dict, Any, Optional
from fastmcp import FastMCP

# Initialize MCP server
import asyncio
import sys
import json
import time
import platform
from typing import Dict, Any
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("reflex-dev-agent")

# Optional: cap concurrent Playwright jobs so you don't spawn 20 chromiums at once
_PLAYWRIGHT_SEMAPHORE = asyncio.Semaphore(2)

async def _run_playwright_child(url: str, timeout_s: int = 15) -> dict:
    """Pass URL as argv (no string injection), not by embedding in Python code."""
    child_code = r"""
import sys, json, tempfile
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

def main(url: str):
    # If you're in CI/Linux containers, add Chrome flags:
    # args = ["--disable-dev-shm-usage", "--no-sandbox"]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # , args=args
        # Ephemeral profile/context to avoid cross-run state
        ctx = browser.new_context(ignore_https_errors=True)
        page = ctx.new_page()
        try:
            # Prefer networkidle, fall back to domcontentloaded
            try:
                page.goto(url, wait_until="networkidle", timeout=10_000)
            except PWTimeout:
                page.goto(url, wait_until="domcontentloaded", timeout=7_000)
            result = {
                "status": "ok",
                "title": page.title(),
                "url": page.url,
                "metrics": page.evaluate("({domReady: document.readyState})")
            }
        except Exception as e:
            result = {"status": "error", "error": str(e)}
        finally:
            try:
                ctx.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass
        print(json.dumps(result))

if __name__ == "__main__":
    main(sys.argv[1])
"""
    # Build command safely; use the same interpreter running your MCP server
    cmd = [sys.executable, "-c", child_code, url]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        # On POSIX you could add: preexec_fn=os.setsid for PG killing
        # On Windows: creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError:
        # Kill child; if zombies are a problem, consider psutil to kill the tree
        proc.kill()
        try:
            await proc.wait()
        finally:
            return {"status": "error", "error": f"timeout after {timeout_s}s"}

    # Keep stderr for logs if you need it
    if proc.returncode != 0 and not stdout:
        return {"status": "error", "error": f"child exit {proc.returncode}", "stderr": stderr.decode(errors="ignore")}

    try:
        return json.loads(stdout.decode())
    except Exception as e:
        return {"status": "error", "error": f"bad JSON from child: {e}", "raw": stdout.decode(errors="ignore")}

@mcp.tool()
async def playwright_tool(url: str) -> dict:
    """Non-blocking Playwright tool with semaphore control."""
    async with _PLAYWRIGHT_SEMAPHORE:
        return await _run_playwright_child(url)

async def kill_process_tree(pid: int) -> None:
    """Kill process tree to prevent zombie processes using non-blocking calls."""
    try:
        if platform.system() == "Windows":
            # Use asyncio subprocess for non-blocking kill
            process = await asyncio.create_subprocess_exec(
                "taskkill", "/F", "/T", "/PID", str(pid),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
        else:
            try:
                import psutil
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)
                for child in children:
                    child.kill()
                parent.kill()
            except (ImportError, Exception):
                # Fallback to kill command using asyncio
                process = await asyncio.create_subprocess_exec(
                    "kill", "-9", str(pid),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await process.wait()
    except Exception:
        pass  # Best effort cleanup

@mcp.tool()
def reflex_dev_test() -> Dict[str, Any]:
    """Simple test tool to verify MCP is working."""
    return {
        'status': 'success',
        'message': 'Reflex Dev Agent Non-blocking Version',
        'timestamp': time.time(),
        'playwright_working': True,
        'tools_available': ['test', 'web_check', 'playwright_inspect', 'context_info'],
        'improvements': ['non-blocking', 'process-tree-cleanup', 'fallback-navigation', 'stable-schema']
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
async def playwright_web_inspect(url: str, get_title_only: bool = True) -> Dict[str, Any]:
    """
    Non-blocking web inspection using Playwright via asyncio subprocess.
    Returns a stable schema with predictable error handling.
    """
    # Define stable return schema
    result_schema = {
        'status': 'pending',
        'url': url,
        'title': None,
        'final_url': None,
        'timestamp': time.time(),
        'body_text_length': None,
        'has_forms': None,
        'form_count': None,
        'has_buttons': None,
        'button_count': None,
        'input_count': None,
        'error': None,
        'debug_info': None
    }
    
    try:
        # Create optimized Playwright script with fallback navigation
        script = f'''
import json
import sys
from playwright.sync_api import sync_playwright  # Use sync in subprocess for simplicity

def inspect_website():
    try:
        with sync_playwright() as p:
            # Launch with robust flags
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu"]
            )
            page = browser.new_page(ignore_https_errors=True)
            
            # Multi-strategy navigation with fallbacks
            navigation_success = False
            debug_info = []
            
            # Strategy 1: networkidle (preferred)
            try:
                page.goto("{url}", wait_until="networkidle", timeout=8000)
                navigation_success = True
                debug_info.append("networkidle_success")
            except Exception as e:
                debug_info.append(f"networkidle_failed: {{str(e)[:50]}}")
                
                # Strategy 2: domcontentloaded (fallback)
                try:
                    page.goto("{url}", wait_until="domcontentloaded", timeout=6000)
                    navigation_success = True
                    debug_info.append("domcontentloaded_success")
                except Exception as e2:
                    debug_info.append(f"domcontentloaded_failed: {{str(e2)[:50]}}")
                    
                    # Strategy 3: load (last resort)
                    try:
                        page.goto("{url}", wait_until="load", timeout=4000)
                        navigation_success = True
                        debug_info.append("load_success")
                    except Exception as e3:
                        debug_info.append(f"load_failed: {{str(e3)[:50]}}")
            
            if not navigation_success:
                browser.close()
                return {{
                    "status": "error",
                    "url": "{url}",
                    "error": "All navigation strategies failed",
                    "debug_info": debug_info
                }}
            
            # Check page readiness
            ready_state = page.evaluate("document.readyState")
            debug_info.append(f"ready_state: {{ready_state}}")
            
            # Extract basic information
            result = {{
                "status": "success",
                "url": "{url}",
                "title": page.title(),
                "final_url": page.url,
                "debug_info": debug_info
            }}
            
            # Extract detailed info if requested
            if not {get_title_only}:
                try:
                    body_text = page.inner_text("body") if page.query_selector("body") else ""
                    forms = page.query_selector_all("form")
                    buttons = page.query_selector_all("button")
                    inputs = page.query_selector_all("input")
                    
                    result.update({{
                        "body_text_length": len(body_text),
                        "has_forms": len(forms) > 0,
                        "form_count": len(forms),
                        "has_buttons": len(buttons) > 0,
                        "button_count": len(buttons),
                        "input_count": len(inputs)
                    }})
                except Exception as detail_error:
                    result["detail_error"] = str(detail_error)[:100]
            
            browser.close()
            return result
            
    except Exception as e:
        return {{
            "status": "error",
            "url": "{url}",
            "error": str(e)[:200],
            "debug_info": ["main_exception"]
        }}

# Write result to stdout as JSON
result = inspect_website()
print(json.dumps(result))
'''
        
        # Use non-blocking asyncio subprocess
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-c', script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        try:
            # Wait with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=12.0  # Reduced timeout
            )
            
            if process.returncode == 0 and stdout:
                subprocess_result = json.loads(stdout.decode().strip())
                # Merge with stable schema
                result_schema.update(subprocess_result)
                result_schema['timestamp'] = time.time()
                return result_schema
            else:
                result_schema.update({
                    'status': 'error',
                    'error': f'Process failed (code: {process.returncode})',
                    'debug_info': stderr.decode()[:200] if stderr else None
                })
                return result_schema
                
        except asyncio.TimeoutError:
            # Kill process tree on timeout
            if process.returncode is None:
                kill_process_tree(process.pid)
                try:
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    pass  # Force killed
                    
            result_schema.update({
                'status': 'error',
                'error': 'Inspection timed out after 12 seconds',
                'debug_info': 'timeout_killed'
            })
            return result_schema
            
    except Exception as e:
        result_schema.update({
            'status': 'error',
            'error': str(e)[:200],
            'debug_info': 'subprocess_creation_failed'
        })
        return result_schema

@mcp.tool()
async def verify_playwright_setup() -> Dict[str, Any]:
    """Verify Playwright installation and dependencies."""
    result = {
        'status': 'checking',
        'playwright_installed': False,
        'chromium_available': False,
        'can_launch_browser': False,
        'setup_commands': [],
        'errors': [],
        'timestamp': time.time()
    }
    
    try:
        # Check if playwright is installed
        try:
            from playwright.sync_api import sync_playwright
            result['playwright_installed'] = True
        except ImportError:
            result['errors'].append('Playwright not installed')
            result['setup_commands'].append('pip install playwright')
            result['status'] = 'error'
            return result
        
        # Test browser launch in subprocess
        test_script = '''
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        browser.close()
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
'''
        
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-c', test_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
        
        if b"SUCCESS" in stdout:
            result.update({
                'status': 'success',
                'chromium_available': True,
                'can_launch_browser': True
            })
        else:
            error_msg = stderr.decode() if stderr else stdout.decode()
            result['errors'].append(f'Browser launch failed: {error_msg[:200]}')
            if 'Chromium' in error_msg or 'executable' in error_msg:
                result['setup_commands'].append('python -m playwright install chromium')
            result['status'] = 'error'
            
    except asyncio.TimeoutError:
        result['errors'].append('Browser test timed out')
        result['setup_commands'].append('python -m playwright install --with-deps chromium')
        result['status'] = 'error'
    except Exception as e:
        result['errors'].append(f'Setup check failed: {str(e)[:200]}')
        result['status'] = 'error'
    
    return result

@mcp.tool()
def reflex_context_info() -> Dict[str, Any]:
    """Get information about typical Reflex development context with stable schema."""
    try:
        info = {
            "success": True,
            "data": {
                "framework": "Reflex",
                "purpose": "Python-based full-stack web framework",
                "features": [
                    "React-style components in Python",
                    "Type-safe reactive state management",
                    "Real-time updates with WebSockets",
                    "Built-in routing and authentication",
                    "Automatic CSS generation",
                    "Database integration with SQLAlchemy"
                ],
                "typical_workflow": [
                    "Create State classes for data management",
                    "Define component functions that return Elements",
                    "Use event handlers for user interactions",
                    "Manage state with reactive updates",
                    "Deploy with reflex deploy"
                ],
                "common_patterns": {
                    "state_management": "Class-based state with reactive updates",
                    "styling": "CSS-in-Python with Tailwind support",
                    "routing": "File-based routing with @rx.page decorators",
                    "forms": "Controlled components with validation"
                }
            },
            "error": None,
            "timestamp": time.time()
        }
        return info
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Failed to get Reflex context: {str(e)}",
            "timestamp": time.time()
        }

if __name__ == "__main__":
    mcp.run()
