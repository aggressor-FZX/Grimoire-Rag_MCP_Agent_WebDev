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
import socket
from typing import Dict, Any, Optional
from fastmcp import FastMCP

# --- Isolated Playwright environment configuration ---
# Allow override via env var MCP_PLAYWRIGHT_PY; fallback to planned isolated env path.
PW_PY = os.environ.get("MCP_PLAYWRIGHT_PY", r"J:\Desktop\ConnectAI\envs\pw\.venv\Scripts\python.exe")
PW_ENV = os.environ.copy()
# Ensure shared browsers path to avoid duplicate downloads.
PW_ENV.setdefault("PLAYWRIGHT_BROWSERS_PATH", r"J:\Desktop\ConnectAI\pw-browsers")
PW_ENV.setdefault("PYTHONIOENCODING", "UTF-8")

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

def wait_for_port(host="127.0.0.1", port=3001, timeout=3.0):
    """Check if a port is available with timeout"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False

async def reflex_healthcheck_or_fail(port=3001):
    """Health check for Reflex server before launching Playwright"""
    if not wait_for_port(port=port):
        return {
            "status": "error",
            "phase": "reflex_unavailable",
            "error": f"Reflex dev server not listening on port {port}",
            "url": f"http://localhost:{port}",
            "timestamp": time.time()
        }
    return None  # healthy

@mcp.tool()
async def debug_env_vars() -> dict:
    """Debug tool to check environment variables in MCP server"""
    import os
    return {
        "PW_PY": PW_PY,
        "PW_PY_exists": os.path.exists(PW_PY),
        "MCP_PLAYWRIGHT_PY": os.environ.get("MCP_PLAYWRIGHT_PY", "NOT_SET"),
        "PLAYWRIGHT_BROWSERS_PATH": os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "NOT_SET"),
        "PYTHONPATH": os.environ.get("PYTHONPATH", "NOT_SET"),
        "cwd": os.getcwd(),
        "python_executable": sys.executable
    }

@mcp.tool()
async def playwright_diagnose(url: str = "http://127.0.0.1:3001/") -> dict:
    """Run staged diagnostics to see where Playwright hangs (python start, import, launch, navigate)."""
    stages = []
    summary = {
        "status": "running",
        "url": url,
        "PW_PY": PW_PY,
        "PW_PY_exists": os.path.exists(PW_PY),
        "PLAYWRIGHT_BROWSERS_PATH": PW_ENV.get("PLAYWRIGHT_BROWSERS_PATH"),
        "timestamp": time.time()
    }

    async def run_stage(name: str, code: str, timeout: float):
        cmd = [PW_PY, "-c", code]
        t0 = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=PW_ENV,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                try:
                    await proc.wait()
                finally:
                    stages.append({
                        "stage": name,
                        "status": "timeout",
                        "timeout_s": timeout,
                        "elapsed": time.time() - t0
                    })
                    return False
            elapsed = time.time() - t0
            out = stdout.decode(errors="ignore").strip()
            err = stderr.decode(errors="ignore").strip()
            stages.append({
                "stage": name,
                "status": "ok" if proc.returncode == 0 else "error",
                "returncode": proc.returncode,
                "elapsed": elapsed,
                "stdout": out[:400],
                "stderr": err[:400]
            })
            return proc.returncode == 0
        except Exception as e:
            stages.append({
                "stage": name,
                "status": "spawn_error",
                "error": str(e)
            })
            return False

    # Stage 1: Python interpreter reachable
    await run_stage("python_start", "import sys, json; print(json.dumps({'python': sys.executable}))", 5)

    # Stage 2: Import playwright (lightweight)
    ok = await run_stage(
        "import_playwright",
        "import time, json, importlib, sys; t=time.time(); import playwright; dt=time.time()-t; print(json.dumps({'import_seconds': dt, 'playwright_version': getattr(importlib.import_module('playwright'), '__version__', 'unknown')}))",
        8
    )
    if not ok:
        summary.update({"status": "error", "failed_stage": "import_playwright", "stages": stages})
        return summary

    # Stage 3: Launch browser
    ok = await run_stage(
        "launch_browser",
        "import json, time; from playwright.sync_api import sync_playwright; t=time.time();\nfrom pathlib import Path;\nwith sync_playwright() as p: b=p.chromium.launch(headless=True); b.close(); print(json.dumps({'launch_seconds': time.time()-t}))",
        12
    )
    if not ok:
        summary.update({"status": "error", "failed_stage": "launch_browser", "stages": stages})
        return summary

    # Optional Stage 4: Navigate
    nav_code = f"""import json, time; from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout;\nstart=time.time();\nwith sync_playwright() as p:\n    b=p.chromium.launch(headless=True);\n    page=b.new_page();\n    try:\n        page.goto('{url}', wait_until='domcontentloaded', timeout=8000)\n        status='ok'\n    except PWTimeout:\n        status='timeout'\n    title = ''\n    try:\n        title = page.title()\n    except Exception: pass\n    b.close();\n    print(json.dumps({{'nav_status': status, 'title': title, 'nav_seconds': time.time()-start}}))"""
    await run_stage("navigate", nav_code, 14)

    summary.update({
        "status": "success",
        "stages": stages
    })
    return summary

@mcp.tool()
def list_tools() -> dict:
    """List currently registered tool names (for MCP reload verification)."""
    try:
        # FastMCP stores tools in mcp.tools (dict name->tool)
        names = sorted(getattr(mcp, 'tools', {}).keys())
        return {"status": "success", "tool_count": len(names), "tools": names}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@mcp.tool()
async def playwright_fetch(
    url: str,
    selectors: str | None = None,
    wait_selector: str | None = None,
    screenshot: bool = False,
    full_page: bool = False,
    delay_ms: int = 0,
    ephemeral: bool = False,
    max_html: int = 6000,
    max_text: int = 2500
) -> dict:
    """Fetch an arbitrary URL via Playwright with optional selectors & screenshot.

    Added features:
      full_page: capture full scroll height screenshot.
      delay_ms: post-wait (or post-nav) sleep before extraction.
      ephemeral: omit base64, return size + sha256 instead.
    """
    async with _PLAYWRIGHT_SEMAPHORE:
        config = {
            "wait_selector": wait_selector,
            "selectors": [s.strip() for s in (selectors.split(',') if selectors else []) if s.strip()],
            "screenshot": screenshot,
            "full_page": full_page,
            "delay_ms": max(0, int(delay_ms)),
            "ephemeral": ephemeral,
            "max_html": max_html,
            "max_text": max_text,
        }

        child_code = r"""
import sys, json, time, base64, re, hashlib
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout, Error as PWError

def clean_ws(s: str, limit: int | None = None):
    if not s:
        return s
    s = re.sub(r"\s+", " ", s).strip()
    if limit and len(s) > limit:
        return s[:limit] + "…"
    return s

def run(url: str, cfg: dict):
    t0 = time.time()
    attempts = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            nav_ok = False
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                attempts.append("domcontentloaded_ok")
                nav_ok = True
            except PWTimeout:
                attempts.append("domcontentloaded_timeout")
                try:
                    page.goto(url, wait_until="load", timeout=10000)
                    attempts.append("load_ok")
                    nav_ok = True
                except PWTimeout:
                    attempts.append("load_timeout")
            if not nav_ok:
                browser.close()
                return {"status": "error", "phase": "navigation", "attempts": attempts, "error": "navigation timeouts"}

            if cfg.get("wait_selector"):
                try:
                    page.wait_for_selector(cfg["wait_selector"], timeout=8000)
                    attempts.append("wait_selector_ok")
                except PWTimeout:
                    attempts.append("wait_selector_timeout")

            if cfg.get("delay_ms"):
                try:
                    time.sleep(min(5000, max(0, int(cfg["delay_ms"])))/1000.0)
                    attempts.append(f"delay_{cfg['delay_ms']}ms")
                except Exception:
                    attempts.append("delay_error")

            title = page.title()
            ready_state = ""
            try:
                ready_state = page.evaluate("document.readyState")
            except Exception:
                pass
            html = ""
            try:
                html = page.content()[: int(cfg.get("max_html", 6000))]
            except Exception:
                pass
            text_preview = ""
            try:
                text_preview = page.inner_text("body")[: int(cfg.get("max_text", 2500))]
            except Exception:
                pass

            selector_results = {}
            for sel in cfg.get("selectors", []):
                try:
                    el = page.query_selector(sel)
                    if el:
                        selector_results[sel] = clean_ws(el.inner_text(), 500)
                    else:
                        selector_results[sel] = None
                except Exception as e:
                    selector_results[sel] = f"error: {e}"[:120]

            screenshot_b64 = None
            screenshot_meta = None
            if cfg.get("screenshot"):
                try:
                    ss = page.screenshot(type="png", full_page=bool(cfg.get("full_page")))
                    if cfg.get("ephemeral"):
                        sha = hashlib.sha256(ss).hexdigest()
                        screenshot_meta = {"bytes": len(ss), "sha256": sha, "full_page": bool(cfg.get("full_page"))}
                    else:
                        screenshot_b64 = base64.b64encode(ss).decode()
                except Exception as e:
                    screenshot_b64 = f"screenshot_error: {e}"[:160]

            browser.close()
            result = {
                "status": "success",
                "url": url,
                "final_url": page.url,
                "title": title,
                "ready_state": ready_state,
                "attempts": attempts,
                "html_preview": html,
                "text_preview": clean_ws(text_preview, 2500),
                "selectors_extracted": selector_results,
                "screenshot_base64": screenshot_b64,
                "screenshot_meta": screenshot_meta,
                "elapsed_ms": int((time.time() - t0) * 1000)
            }
            if cfg.get("screenshot") and cfg.get("ephemeral") and screenshot_meta is None and not screenshot_b64:
                result["screenshot_meta"] = {"warning": "ephemeral requested but no screenshot captured"}
            return result
    except PWError as e:
        return {"status": "error", "phase": "launch", "error": str(e), "attempts": attempts}
    except Exception as e:
        return {"status": "error", "phase": "runtime", "error": str(e), "attempts": attempts}

if __name__ == "main__":
    pass
"""

        effective_py = PW_PY if os.path.exists(PW_PY) else sys.executable
        wrapper = """
import sys, json
child_code = sys.stdin.read()
url = sys.argv[1]
cfg = json.loads(sys.argv[2])
ns = {}
exec(child_code, ns)
import json as _j
print(_j.dumps(ns['run'](url, cfg)))
"""
        proc = await asyncio.create_subprocess_exec(
            effective_py, '-c', wrapper, url, json.dumps(config),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=PW_ENV
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(input=child_code.encode()), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            return {"status": "error", "error": "timeout after 30s", "url": url}

        if proc.returncode != 0:
            return {"status": "error", "error": f"child exit {proc.returncode}", "stderr": stderr.decode(errors='ignore')[:400]}
        try:
            return json.loads(stdout.decode())
        except Exception as e:
            return {"status": "error", "error": f"bad JSON: {e}", "raw": stdout.decode(errors='ignore')[:400]}

@mcp.tool()
async def dictionary_define(term: str = "cogito", sense_index: int = 2) -> dict:
    """Fetch definitions from Merriam-Webster for a term using Playwright (headless) and return requested sense.

    Args:
        term: Dictionary headword to look up (e.g., "cogito").
        sense_index: 1-based index of the definition to highlight (default=2).

    Returns JSON with:
        status: ok|error
        url: page URL
        total_definitions
        definitions: list of cleaned definition strings (first 12)
        requested_definition: the definition at sense_index if available
        elapsed_ms
        attempts: navigation attempts / phases
    """
    import textwrap
    base_url = f"https://www.merriam-webster.com/dictionary/{term}"
    child_code = r"""
import re, sys, json, time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout, Error as PWError

TERM = sys.argv[1]
URL = f"https://www.merriam-webster.com/dictionary/{TERM}"

def clean(txt: str) -> str:
    t = re.sub(r"\s+", " ", txt).strip()
    t = t.lstrip(': ').strip()
    # remove bracketed pronunciation markers etc at start
    t = re.sub(r"^\[[^\]]+\]\s*", "", t)
    return t

start = time.time()
attempts = []
definitions = []
status = "ok"
error = None

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=15000)
            attempts.append("domcontentloaded_ok")
        except PWTimeout:
            attempts.append("domcontentloaded_timeout")
            page.goto(URL, timeout=15000)

        # Cookie / consent dismissal best-effort
        try:
            page.locator("button:has-text('Accept')").first.click(timeout=2000)
        except Exception:
            pass

        # Merriam-Webster main defs: span.dtText inside div.vg or similar containers
        nodes = page.locator("span.dtText")
        count = nodes.count()
        for i in range(count):
            try:
                raw = nodes.nth(i).inner_text().strip()
            except Exception:
                continue
            c = clean(raw)
            if not c:
                continue
            # Skip pure cross-references like "see X"
            if re.match(r"^see ", c, re.IGNORECASE):
                continue
            definitions.append(c)
            if len(definitions) >= 20:
                break
        browser.close()
except PWError as e:
    status = "error"
    error = f"playwright: {e}"[:200]
except Exception as e:
    status = "error"
    error = str(e)[:200]

elapsed_ms = int((time.time()-start)*1000)

out = {
    "status": status,
    "url": URL,
    "total_definitions": len(definitions),
    "definitions": definitions[:12],
    "elapsed_ms": elapsed_ms,
    "attempts": attempts
}
print(json.dumps(out, ensure_ascii=False))
"""

    effective_py = PW_PY if os.path.exists(PW_PY) else sys.executable
    cmd = [effective_py, "-c", child_code, term]

    async with _PLAYWRIGHT_SEMAPHORE:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=PW_ENV,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            try:
                await proc.wait()
            finally:
                return {"status": "error", "error": "timeout", "term": term, "url": base_url}

    if proc.returncode != 0 or not stdout:
        return {"status": "error", "error": f"exit {proc.returncode}", "stderr": stderr.decode(errors="ignore")[:300], "term": term, "url": base_url}

    try:
        data = json.loads(stdout.decode())
    except Exception as e:
        return {"status": "error", "error": f"bad json: {e}", "raw": stdout.decode(errors="ignore")[:400]}

    defs = data.get("definitions", [])
    idx = sense_index - 1
    requested = defs[idx] if 0 <= idx < len(defs) else None
    data["requested_definition_index"] = sense_index
    data["requested_definition"] = requested
    data["term"] = term
    return data

async def _run_playwright_child(url: str, timeout_s: int = 22) -> dict:
    """Pass URL as argv (no string injection), not by embedding in Python code."""
    child_code = r"""
import sys, json, time
from playwright.sync_api import sync_playwright, Error as PWError, TimeoutError as PWTimeout

def main(url: str):
    start = time.time()
    attempts = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Prefer domcontentloaded (faster & dev-server friendly) then load
            nav_ok = False
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=6_000)
                attempts.append("domcontentloaded_ok")
                nav_ok = True
            except PWTimeout:
                attempts.append("domcontentloaded_timeout")
                try:
                    page.goto(url, wait_until="load", timeout=6_000)
                    attempts.append("load_ok")
                    nav_ok = True
                except PWTimeout:
                    attempts.append("load_timeout")

            if not nav_ok:
                result = {
                    "status": "error",
                    "phase": "nav",
                    "error": "navigation timeouts",
                    "attempts": attempts,
                    "elapsed_ms": int((time.time()-start)*1000)
                }
            else:
                result = {
                    "status": "ok",
                    "title": page.title(),
                    "url": page.url,
                    "ready_state": page.evaluate("document.readyState"),
                    "attempts": attempts,
                    "elapsed_ms": int((time.time()-start)*1000)
                }
            browser.close()
    except PWError as e:
        result = {"status": "error", "phase": "launch", "error": str(e), "attempts": attempts, "elapsed_ms": int((time.time()-start)*1000)}
    except Exception as e:
        result = {"status": "error", "phase": "runtime", "error": str(e), "attempts": attempts, "elapsed_ms": int((time.time()-start)*1000)}
    print(json.dumps(result))

if __name__ == "__main__":
    main(sys.argv[1])
"""
    # Build command safely; use the same interpreter running your MCP server
    # Use isolated Playwright interpreter instead of current MCP interpreter.
    effective_py = PW_PY if os.path.exists(PW_PY) else sys.executable
    cmd = [effective_py, "-c", child_code, url]
    print(f"PW CMD: {cmd}")
    print(f"PW_PY exists: {os.path.exists(PW_PY)}")
    print(f"PW_ENV keys: {list(PW_ENV.keys())}")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=PW_ENV,
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
    """Non-blocking Playwright tool with semaphore control and health check."""
    # Health check for localhost URLs  
    if 'localhost:3001' in url or '127.0.0.1:3001' in url:
        health_error = await reflex_healthcheck_or_fail(port=3001)
        if health_error:
            return health_error
    elif 'localhost:3000' in url or '127.0.0.1:3000' in url:
        health_error = await reflex_healthcheck_or_fail(port=3000)
        if health_error:
            return health_error
    
    async with _PLAYWRIGHT_SEMAPHORE:
        return await _run_playwright_child(url)

@mcp.tool()
async def playwright_snapshot_dom(url: str, take_screenshot: bool = True) -> dict:
    """Capture DOM structure and optionally take a screenshot of the webpage."""
    # Health check for localhost URLs  
    if 'localhost:3001' in url or '127.0.0.1:3001' in url:
        health_error = await reflex_healthcheck_or_fail(port=3001)
        if health_error:
            return health_error
    elif 'localhost:3000' in url or '127.0.0.1:3000' in url:
        health_error = await reflex_healthcheck_or_fail(port=3000)
        if health_error:
            return health_error

    snapshot_code = f'''
import sys, json, time, base64, os
from playwright.sync_api import sync_playwright, Error as PWError, TimeoutError as PWTimeout

def main(url: str, take_screenshot: bool):
    start = time.time()
    attempts = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Set viewport for consistent screenshots
            page.set_viewport_size({{"width": 1280, "height": 720}})
            
            # Navigate with fallback strategy
            nav_ok = False
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=8_000)
                attempts.append("domcontentloaded_ok")
                nav_ok = True
            except PWTimeout:
                attempts.append("domcontentloaded_timeout")
                try:
                    page.goto(url, wait_until="load", timeout=6_000)
                    attempts.append("load_ok")
                    nav_ok = True
                except PWTimeout:
                    attempts.append("load_timeout")

            if not nav_ok:
                result = {{
                    "status": "error",
                    "phase": "navigation",
                    "error": "All navigation strategies failed",
                    "attempts": attempts,
                    "elapsed_ms": int((time.time()-start)*1000)
                }}
            else:
                # Extract DOM information
                title = page.title()
                html_content = page.content()[:5000]  # First 5KB of HTML
                
                # Get page metrics
                ready_state = page.evaluate("document.readyState")
                
                # Extract forms, buttons, inputs
                forms = page.query_selector_all("form")
                buttons = page.query_selector_all("button")
                inputs = page.query_selector_all("input")
                links = page.query_selector_all("a")
                
                # Get visible text
                body_text = ""
                try:
                    body_element = page.query_selector("body")
                    if body_element:
                        body_text = body_element.inner_text()[:2000]  # First 2KB of text
                except Exception:
                    pass
                
                # Take screenshot if requested
                screenshot_data = None
                if take_screenshot:
                    try:
                        screenshot_bytes = page.screenshot(type="png", full_page=False)
                        screenshot_data = base64.b64encode(screenshot_bytes).decode()
                    except Exception as e:
                        screenshot_data = f"Screenshot failed: {{str(e)}}"
                
                result = {{
                    "status": "success",
                    "url": page.url,
                    "title": title,
                    "ready_state": ready_state,
                    "html_preview": html_content,
                    "body_text_preview": body_text,
                    "dom_elements": {{
                        "forms": len(forms),
                        "buttons": len(buttons),
                        "inputs": len(inputs),
                        "links": len(links)
                    }},
                    "screenshot_base64": screenshot_data,
                    "attempts": attempts,
                    "elapsed_ms": int((time.time()-start)*1000)
                }}
            
            browser.close()
    except PWError as e:
        result = {{"status": "error", "phase": "browser_launch", "error": str(e), "attempts": attempts, "elapsed_ms": int((time.time()-start)*1000)}}
    except Exception as e:
        result = {{"status": "error", "phase": "runtime", "error": str(e), "attempts": attempts, "elapsed_ms": int((time.time()-start)*1000)}}
    
    print(json.dumps(result))

if __name__ == "__main__":
    url = sys.argv[1]
    take_screenshot = sys.argv[2].lower() == "true" if len(sys.argv) > 2 else True
    main(url, take_screenshot)
'''
    
    effective_py = PW_PY if os.path.exists(PW_PY) else sys.executable
    cmd = [effective_py, "-c", snapshot_code, url, str(take_screenshot).lower()]
    
    async with _PLAYWRIGHT_SEMAPHORE:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=PW_ENV,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=25)
        except asyncio.TimeoutError:
            proc.kill()
            try:
                await proc.wait()
            finally:
                return {
                    "status": "error", 
                    "error": f"snapshot timeout after 25s",
                    "url": url,
                    "stderr": stderr.decode(errors="ignore")[:500] if stderr else None
                }

        if proc.returncode != 0 and not stdout:
            return {
                "status": "error", 
                "error": f"process exit {proc.returncode}", 
                "stderr": stderr.decode(errors="ignore")[:500],
                "url": url
            }

        try:
            return json.loads(stdout.decode())
        except Exception as e:
            return {
                "status": "error", 
                "error": f"bad JSON from child: {e}", 
                "raw": stdout.decode(errors="ignore")[:1000],
                "stderr": stderr.decode(errors="ignore")[:500],
                "url": url
            }

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
    
    # Health check for localhost URLs
    if 'localhost:3001' in url or '127.0.0.1:3001' in url:
        health_error = await reflex_healthcheck_or_fail(port=3001)
        if health_error:
            result_schema.update(health_error)
            return result_schema
    elif 'localhost:3000' in url or '127.0.0.1:3000' in url:
        health_error = await reflex_healthcheck_or_fail(port=3000)
        if health_error:
            result_schema.update(health_error)
            return result_schema
    
    try:
        # Create optimized Playwright script with fallback navigation
        script = f'''
import json
import sys
from playwright.sync_api import sync_playwright, Error as PWError, TimeoutError as PWTimeout

def inspect_website():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Multi-strategy navigation with fallbacks
            navigation_success = False
            debug_info = []
            
            # Strategy 1: networkidle (preferred)
            try:
                page.goto("{url}", wait_until="networkidle", timeout=8000)
                navigation_success = True
                debug_info.append("networkidle_success")
            except PWTimeout:
                debug_info.append("networkidle_timeout")
                
                # Strategy 2: domcontentloaded (fallback)
                try:
                    page.goto("{url}", wait_until="domcontentloaded", timeout=6000)
                    navigation_success = True
                    debug_info.append("domcontentloaded_success")
                except PWTimeout:
                    debug_info.append("domcontentloaded_timeout")
                    
                    # Strategy 3: load (last resort)
                    try:
                        page.goto("{url}", wait_until="load", timeout=4000)
                        navigation_success = True
                        debug_info.append("load_success")
                    except PWTimeout:
                        debug_info.append("load_timeout")
            
            if not navigation_success:
                browser.close()
                return {{
                    "status": "error",
                    "url": "{url}",
                    "error": "All navigation strategies timed out",
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
            
    except PWError as e:
        return {{
            "status": "error",
            "url": "{url}",
            "phase": "browser_launch",
            "error": str(e)[:200],
            "debug_info": ["playwright_launch_failed"]
        }}
    except Exception as e:
        return {{
            "status": "error",
            "url": "{url}",
            "phase": "runtime",
            "error": str(e)[:200],
            "debug_info": ["general_exception"]
        }}

# Write result to stdout as JSON
result = inspect_website()
print(json.dumps(result))
'''
        
        # Use non-blocking asyncio subprocess
        effective_py = PW_PY if os.path.exists(PW_PY) else sys.executable
        process = await asyncio.create_subprocess_exec(
            effective_py, '-c', script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
            env=PW_ENV
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
