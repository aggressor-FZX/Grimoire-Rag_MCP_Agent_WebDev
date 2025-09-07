# Obsolete: moved to obsoleate/ (original content removed).
#!/usr/bin/env python3
"""
Reflex Documentation MCP Server with Intelligent Agent

Advanced MCP server that provides intelligent, semantic access to Reflex documentation
with automatic intent detection and context injection for building web apps with Reflex.
"""

import os
import re
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Tuple, Optional
import time
import asyncio
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import tiktoken
from fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("reflex-docs-server-enhanced")

class ReflexDocsRetriever:
    """Advanced retriever for Reflex documentation with semantic search capabilities."""
    
    def __init__(self, persist_directory: str = "./reflex_chroma_db"):
        """Initialize the retriever with persistent storage."""
        self.persist_directory = persist_directory
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="reflex_docs",
            metadata={"description": "Reflex documentation chunks with embeddings"}
        )
        
        print(f"Initialized Reflex docs retriever with {self.collection.count()} existing chunks")
    
    def scrape_page(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """Scrape a single documentation page with retry logic and context-aware code block extraction."""
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove non-content elements
                for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                    element.decompose()
                
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "Untitled"
                
                content_selectors = ['main', '.content', '.documentation', '.docs-content', '[role="main"]', 'article', '.markdown-body']
                content_element = None
                for selector in content_selectors:
                    content_element = soup.select_one(selector)
                    if content_element:
                        break
                
                if not content_element:
                    content_element = soup.find('body')
                
                if not content_element:
                    print(f"  ❌ Failed: No content element found for {url}")
                    return None

                # New context-aware extraction logic
                content_blocks = []
                # Find all relevant tags in order
                for element in content_element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li', 'pre', 'table']):
                    if element.name == 'pre':
                        # Reconstruct code with indentation from span lines
                        lines = element.find_all('span', class_='line')
                        code_text = '\n'.join(''.join(span.get_text() for span in line.find_all('span')) for line in lines)

                        if not code_text.strip():
                            # Fallback for simple <pre> tags without line spans
                            code_text = element.get_text()

                        if not code_text.strip():
                            continue

                        context_text = ""
                        # Find the most relevant preceding text
                        prev_element = element
                        while True:
                            prev_element = prev_element.find_previous()
                            if prev_element is None:
                                break
                            if prev_element.name in ['p', 'h1', 'h2', 'h3', 'h4', 'li']:
                                context_text = prev_element.get_text(strip=True)
                                if context_text:
                                    break # Found the closest context
                        
                        combined_block = ""
                        if context_text:
                            combined_block = f"Context: {context_text}\n\nCode Example:\n```python\n{code_text}\n```"
                            # If the context was the last thing added, replace it
                            if content_blocks and content_blocks[-1] == context_text:
                                content_blocks[-1] = combined_block
                            else:
                                content_blocks.append(combined_block)
                        else:
                            content_blocks.append(f"Code Example:\n```python\n{code_text}\n```")
                    else:
                        # Handle other text/table elements
                        text = element.get_text(strip=True)
                        if text and len(text) > 15:
                            # Check if this text is context for a code block that immediately follows
                            next_sibling = element.find_next_sibling()
                            if not (next_sibling and next_sibling.name == 'pre'):
                                content_blocks.append(text)

                if not content_blocks:
                    print(f"  ❌ Failed: No content blocks extracted from {url}")
                    return None

                cleaned_content = '\n\n---\n\n'.join(content_blocks)
                
                return {
                    'url': url,
                    'title': title_text,
                    'content': cleaned_content,
                    'length': len(cleaned_content)
                }
                
            except Exception as e:
                print(f"  Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None
    
    def chunk_text(self, text: str, max_tokens: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks based on token count."""
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            end = start + max_tokens
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            start = end - overlap
        
        return chunks
    
    def index_page(self, page_data: Dict):
        """Index a page by chunking and storing in vector database."""
        content = page_data['content']
        chunks = self.chunk_text(content)
        
        for i, chunk in enumerate(chunks):
            doc_id = f"{page_data['url']}#chunk_{i}"
            
            # Check if already exists
            try:
                existing = self.collection.get(ids=[doc_id])
                if existing['ids']:
                    continue
            except:
                pass
            
            # Create embedding
            embedding = self.model.encode(chunk).tolist()
            
            # Store in vector database
            self.collection.add(
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{
                    'url': page_data['url'],
                    'title': page_data['title'],
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }],
                ids=[doc_id]
            )
    
    def search(self, query: str, n_results: int = 10) -> List[Dict]:
        """Search for relevant documentation chunks."""
        query_embedding = self.model.encode(query).tolist()
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
        except Exception as e:
            # This handles the case where the collection was deleted and recreated by another process.
            print(f"Query failed with error: {e}. Attempting to reconnect to collection...")
            try:
                self.collection = self.client.get_or_create_collection(name="reflex_docs")
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    include=['documents', 'metadatas', 'distances']
                )
                print("Reconnected and query successful.")
            except Exception as e2:
                print(f"Failed to reconnect and query: {e2}")
                # Return empty results if reconnection fails
                return []

        formatted_results = []
        if results.get('documents') and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'url': results['metadatas'][0][i].get('url', 'N/A'),
                    'title': results['metadatas'][0][i].get('title', 'N/A'),
                    'similarity_score': 1 - results['distances'][0][i] if results['distances'] else 0
                })
        
        return formatted_results
    
    def get_reflex_documentation_pages(self) -> List[str]:
        """Get comprehensive list of Reflex documentation pages from the text file."""
        urls_file = os.path.join(os.path.dirname(__file__), 'reflex_urls.txt')
        if not os.path.exists(urls_file):
            print(f"Warning: {urls_file} not found. Using empty URL list.")
            return []

        with open(urls_file, 'r', encoding='utf-8') as f:
            raw_urls = f.readlines()

        cleaned_urls = set()
        for url in raw_urls:
            url = url.strip()
            if not url:
                continue

            # Skip malformed URLs from previous extractions
            if "https://reflex.devhttps://" in url:
                url = url.replace("https://reflex.devhttps://", "https://")

            # We only want documentation pages
            if not url.startswith("https://reflex.dev/docs/"):
                continue

            # Skip assets
            if any(url.endswith(ext) for ext in ['.png', '.svg', '.ico', '.css', '.js', '.webmanifest']):
                continue
            
            # Remove URL fragments
            url = url.split('#')[0]

            # Remove trailing slash for consistency
            if url.endswith('/'):
                url = url[:-1]

            if url:
                cleaned_urls.add(url)
        
        # Return a sorted list for consistent processing order
        return sorted(list(cleaned_urls))
    
    def refresh_documentation(self, max_pages: int = None, force_refresh: bool = False) -> Dict:
        """Refresh the documentation database by scraping all pages."""
        current_count = self.collection.count()
        if current_count > 0 and not force_refresh:
            return {
                "status": "skipped",
                "message": f"Database already contains {current_count} chunks. Use force_refresh=True to re-scrape.",
                "current_chunk_count": current_count
            }

        if force_refresh:
            print("Clearing existing collection...")
            try:
                self.client.delete_collection(name=self.collection.name)
                self.collection = self.client.get_or_create_collection(
                    name="reflex_docs",
                    metadata={"description": "Reflex documentation chunks with embeddings"}
                )
                print(f"Collection '{self.collection.name}' cleared and recreated.")
            except Exception as e:
                print(f"Warning: Could not clear collection, it might not exist. Error: {e}")

        pages = self.get_reflex_documentation_pages()
        
        if max_pages:
            pages = pages[:max_pages]
        
        successful_pages = 0
        failed_pages = 0
        total_chunks = 0
        
        print(f"Starting to index {len(pages)} Reflex documentation pages...")
        
        for i, url in enumerate(pages, 1):
            print(f"[{i}/{len(pages)}] Scraping {url}...")
            
            try:
                page_data = self.scrape_page(url)
                if page_data:
                    # Count chunks before indexing
                    chunks_before = self.collection.count()
                    self.index_page(page_data)
                    chunks_after = self.collection.count()
                    page_chunks = chunks_after - chunks_before
                    total_chunks += page_chunks
                    successful_pages += 1
                    print(f"  ✅ Success: {page_chunks} chunks added")
                else:
                    failed_pages += 1
                    print(f"  ❌ Failed: No content extracted")
            except Exception as e:
                failed_pages += 1
                print(f"  ❌ Failed: {str(e)}")
            
            # Add delay to be respectful
            time.sleep(0.5)
        
        return {
            "total_pages_attempted": len(pages),
            "successful_pages": successful_pages,
            "failed_pages": failed_pages,
            "total_chunks_added": total_chunks,
            "total_chunks_in_db": self.collection.count()
        }

    def refresh_from_xml_file(self, xml_file_path: str, force_refresh: bool = False) -> Dict:
        """Refresh the documentation database by parsing a local XML file."""
        current_count = self.collection.count()
        if current_count > 0 and not force_refresh:
            return {
                "status": "skipped",
                "message": f"Database already contains {current_count} chunks. Use force_refresh=True to re-scrape.",
                "current_chunk_count": current_count
            }

        if force_refresh:
            print("Clearing existing collection...")
            try:
                self.client.delete_collection(name=self.collection.name)
                self.collection = self.client.get_or_create_collection(
                    name="reflex_docs",
                    metadata={"description": "Reflex documentation chunks with embeddings"}
                )
                print(f"Collection '{self.collection.name}' cleared and recreated.")
            except Exception as e:
                print(f"Warning: Could not clear collection, it might not exist. Error: {e}")

        print(f"Reading from XML file: {xml_file_path}")
        try:
            with open(xml_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return {"status": "error", "message": f"XML file not found at {xml_file_path}"}

        soup = BeautifulSoup(content, 'html.parser')
        
        content_blocks = []
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li', 'pre', 'table']):
            if element.name == 'pre':
                lines = element.find_all('span', class_='line')
                code_text = '\n'.join(''.join(span.get_text() for span in line.find_all('span')) for line in lines)

                if not code_text.strip():
                    code_text = element.get_text()

                if not code_text.strip():
                    continue

                context_text = ""
                prev_element = element
                while True:
                    prev_element = prev_element.find_previous()
                    if prev_element is None:
                        break
                    if prev_element.name in ['p', 'h1', 'h2', 'h3', 'h4', 'li']:
                        context_text = prev_element.get_text(strip=True)
                        if context_text:
                            break
                
                combined_block = ""
                if context_text:
                    combined_block = f"Context: {context_text}\n\nCode Example:\n```python\n{code_text}\n```"
                    if content_blocks and content_blocks[-1] == context_text:
                        content_blocks[-1] = combined_block
                    else:
                        content_blocks.append(combined_block)
                else:
                    content_blocks.append(f"Code Example:\n```python\n{code_text}\n```")
            else:
                text = element.get_text(strip=True)
                if text and len(text) > 15:
                    next_sibling = element.find_next_sibling()
                    if not (next_sibling and next_sibling.name == 'pre'):
                        content_blocks.append(text)

        if not content_blocks:
            return {"status": "error", "message": "No content blocks extracted from XML."}

        full_content = '\n\n---\n\n'.join(content_blocks)
        page_data = {
            'url': os.path.basename(xml_file_path),
            'title': 'Local XML Dump',
            'content': full_content
        }
        
        chunks_before = self.collection.count()
        self.index_page(page_data)
        chunks_after = self.collection.count()
        total_chunks = chunks_after - chunks_before

        stats = {
            "status": "completed",
            "source_file": xml_file_path,
            "total_chunks_added": total_chunks,
            "total_chunks_in_db": self.collection.count()
        }
        return stats


class ReflexAgentCoordinator:
    """Intelligent coordination system for Reflex-related queries and responses."""
    
    def __init__(self, retriever: ReflexDocsRetriever):
        self.retriever = retriever
        
        # Reflex-specific keywords for intent detection
        self.reflex_keywords = {
            'reflex', 'rx', 'react', 'web app', 'frontend', 'backend', 'full-stack',
            'component', 'state', 'event', 'var', 'style', 'page', 'route', 'router',
            'database', 'model', 'query', 'api', 'deployment', 'hosting', 'auth',
            'authentication', 'upload', 'file', 'asset', 'custom component',
            'styling', 'css', 'responsive', 'layout', 'form', 'table', 'chart',
            'navbar', 'sidebar', 'modal', 'toast', 'theme', 'color mode',
            'client storage', 'local storage', 'session', 'middleware'
        }
        
        # Context keywords that might indicate Reflex usage
        self.context_keywords = {
            'python web framework', 'fullstack python', 'react components',
            'web application', 'web app development', 'python frontend',
            'python react', 'reactive ui', 'state management', 'web framework'
        }
    
    def detect_reflex_intent(self, user_input: str) -> Tuple[bool, float, List[str]]:
        """Detect if user input is related to Reflex development."""
        text_lower = user_input.lower()
        
        # Direct keyword matches
        direct_matches = [kw for kw in self.reflex_keywords if kw in text_lower]
        context_matches = [kw for kw in self.context_keywords if kw in text_lower]
        
        # Calculate confidence score
        confidence = 0.0
        
        # Direct Reflex mentions get high confidence
        if 'reflex' in text_lower or 'rx.' in text_lower:
            confidence = 1.0
        elif direct_matches:
            confidence = min(0.9, 0.3 + len(direct_matches) * 0.15)
        elif context_matches:
            confidence = min(0.7, 0.2 + len(context_matches) * 0.1)
        
        # Additional patterns that suggest Reflex usage
        reflex_patterns = [
            r'rx\.\w+',  # rx.text, rx.button, etc.
            r'reflex\s+\w+',
            r'python.*web.*app',
            r'fullstack.*python',
            r'react.*component.*python'
        ]
        
        for pattern in reflex_patterns:
            if re.search(pattern, text_lower):
                confidence = max(confidence, 0.8)
        
        all_matches = direct_matches + context_matches
        is_reflex_related = confidence > 0.5
        
        return is_reflex_related, confidence, all_matches
    
    def extract_search_queries(self, user_input: str, keywords: List[str]) -> List[str]:
        """Extract relevant search queries from user input for Reflex docs."""
        queries = []
        
        # Add the original input as primary query
        queries.append(user_input)
        
        # Generate focused queries based on detected keywords
        if 'component' in user_input.lower():
            queries.append(f"reflex components {' '.join(keywords)}")
        
        if 'state' in user_input.lower():
            queries.append("reflex state management events vars")
        
        if any(word in user_input.lower() for word in ['style', 'css', 'design']):
            queries.append("reflex styling theming responsive design")
        
        if any(word in user_input.lower() for word in ['route', 'page', 'navigation']):
            queries.append("reflex routing pages navigation")
        
        if any(word in user_input.lower() for word in ['database', 'data', 'model']):
            queries.append("reflex database models queries")
        
        if any(word in user_input.lower() for word in ['deploy', 'host', 'production']):
            queries.append("reflex deployment hosting production")
        
        if any(word in user_input.lower() for word in ['auth', 'login', 'user']):
            queries.append("reflex authentication login user management")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in queries:
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        
        return unique_queries[:5]  # Limit to 5 queries
    
    def format_context_for_prompt(self, search_results: List[Dict], user_request: str) -> str:
        """Format search results into context suitable for prompt injection."""
        if not search_results:
            return "No relevant Reflex documentation found for this query."
        
        context = f"""
=== REFLEX DOCUMENTATION CONTEXT ===
Retrieved documentation relevant to: {user_request}

"""
        
        for i, result in enumerate(search_results, 1):
            context += f"--- Source {i} (Relevance: {result['similarity_score']:.3f}) ---\n"
            context += f"Title: {result['title']}\n"
            context += f"URL: {result['url']}\n"
            context += f"Content: {result['content'][:800]}{'...' if len(result['content']) > 800 else ''}\n\n"
        
        context += """=== END REFLEX DOCUMENTATION CONTEXT ===

Use this documentation to provide accurate, up-to-date information about Reflex.
When providing code examples, follow Reflex conventions and patterns shown in the documentation.
"""
        
        return context
    
    def validate_code_against_docs(self, code: str) -> Tuple[List[str], List[Dict]]:
        """Validate generated code against Reflex documentation patterns."""
        issues = []
        validation_results = []
        
        # Check for common Reflex patterns
        if 'import reflex as rx' not in code and 'rx.' in code:
            issues.append("Missing 'import reflex as rx' statement")
        
        # Look for component usage patterns
        component_patterns = re.findall(r'rx\.(\w+)', code)
        if component_patterns:
            # Search for documentation about these components
            for component in set(component_patterns):
                search_query = f"rx.{component} component usage"
                results = self.retriever.search(search_query, n_results=2)
                validation_results.extend(results)
        
        # Check for state class patterns
        if 'class' in code and 'rx.State' in code:
            search_query = "reflex State class events vars"
            results = self.retriever.search(search_query, n_results=2)
            validation_results.extend(results)
        
        # Check for app definition patterns
        if 'app = rx.App' in code:
            search_query = "reflex app configuration setup"
            results = self.retriever.search(search_query, n_results=2)
            validation_results.extend(results)
        
        return issues, validation_results


# Initialize components
retriever = ReflexDocsRetriever()
coordinator = ReflexAgentCoordinator(retriever)

@mcp.tool()
def get_reflex_database_status() -> dict:
    """
    Get current status of the Reflex documentation database.
    
    Returns:
        Database statistics and status information
    """
    try:
        count = retriever.collection.count()
        
        # Get some sample data to check database health
        if count > 0:
            sample_data = retriever.collection.peek(limit=3)
            sample_urls = [metadata.get('url', 'Unknown') for metadata in sample_data.get('metadatas', [])]
        else:
            sample_urls = []
        
        return {
            "status": "active" if count > 0 else "empty",
            "total_chunks": count,
            "sample_sources": sample_urls[:3],
            "database_ready": count > 0,
            "recommendation": "Database is ready for search" if count > 0 else "Run 'refresh_reflex_docs' to populate database"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking database: {str(e)}",
            "database_ready": False
        }

@mcp.tool()
def reflex_intelligent_agent(user_request: str, include_code_validation: bool = True) -> dict:
    """
    Intelligent agent that detects Reflex-related requests and provides contextual assistance.
    
    This tool automatically:
    1. Detects if the request is Reflex-related
    2. Retrieves relevant documentation
    3. Formats context for code generation
    4. Optionally validates generated code against docs
    
    Args:
        user_request: The user's request or question
        include_code_validation: Whether to include code validation info
    
    Returns:
        Comprehensive response with context, guidance, and validation
    """
    try:
        # Step 1: Detect Reflex intent
        is_reflex, confidence, keywords = coordinator.detect_reflex_intent(user_request)
        
        if not is_reflex:
            return {
                "status": "not_reflex_related",
                "confidence": confidence,
                "message": "Request does not appear to be Reflex-related",
                "user_request": user_request
            }
        
        # Step 2: Extract search queries
        search_queries = coordinator.extract_search_queries(user_request, keywords)
        
        # Step 3: Retrieve relevant documentation
        all_results = []
        for query in search_queries:
            results = retriever.search(query, n_results=3)
            all_results.extend(results)
        
        # Remove duplicates and sort by relevance
        unique_results = {}
        for result in all_results:
            key = result['url'] + str(result['metadata'].get('chunk_index', 0))
            if key not in unique_results or result['similarity_score'] > unique_results[key]['similarity_score']:
                unique_results[key] = result
        
        top_results = sorted(unique_results.values(), key=lambda x: x['similarity_score'], reverse=True)[:5]
        
        # Step 4: Format context for prompt injection
        formatted_context = coordinator.format_context_for_prompt(top_results, user_request)
        
        # Step 5: Prepare comprehensive response
        response = {
            "status": "reflex_detected",
            "confidence": confidence,
            "detected_keywords": keywords,
            "search_queries_used": search_queries,
            "documentation_context": formatted_context,
            "retrieved_sources": len(top_results),
            "user_request": user_request,
            "guidance": {
                "next_steps": [
                    "Use the provided documentation context when generating code",
                    "Follow Reflex conventions: import reflex as rx, use rx.components", 
                    "Reference the specific patterns shown in the retrieved examples",
                    "Ensure proper State class usage and event handling"
                ],
                "key_docs": [result['url'] for result in top_results[:3]]
            }
        }
        
        # Add code validation if requested
        if include_code_validation:
            response["validation_info"] = {
                "message": "After generating code, use 'validate_reflex_code' tool to check against documentation",
                "recommended": True
            }
        
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error in intelligent agent: {str(e)}",
            "user_request": user_request
        }

@mcp.tool()
def validate_reflex_code(code: str, original_request: str = "") -> dict:
    """
    Validate generated code against Reflex documentation.
    
    Args:
        code: The generated code to validate
        original_request: Original user request for context
    
    Returns:
        Validation results with potential issues and documentation references
    """
    try:
        # Validate code against documentation
        issues, validation_results = coordinator.validate_code_against_docs(code)
        
        # Additional context search if original request provided
        if original_request:
            context_results = retriever.search(original_request, n_results=2)
            validation_results.extend(context_results)
        
        return {
            "status": "validation_complete",
            "potential_issues": issues,
            "issues_found": len(issues),
            "validation_sources": len(validation_results),
            "recommendations": {
                "check_patterns": issues if issues else ["All patterns appear to be documented"],
                "reference_docs": [result['url'] for result in validation_results[:3]]
            },
            "validation_results": validation_results[:5],  # Limit results
            "code_length": len(code),
            "original_request": original_request
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Error validating code: {str(e)}",
            "code_length": len(code)
        }

@mcp.tool()
def search_reflex_docs(query: str, max_results: int = 5, auto_refresh: bool = False) -> dict:
    """
    Search Reflex documentation using semantic similarity.
    
    Args:
        query: Search query for Reflex documentation
        max_results: Maximum number of results to return (1-20)
        auto_refresh: Whether to refresh docs if database is empty
    
    Returns:
        Dictionary containing search results and metadata
    """
    try:
        # Validate parameters
        max_results = max(1, min(20, max_results))
        
        # Check if database needs refresh
        current_count = retriever.collection.count()
        if current_count == 0 and auto_refresh:
            print("Database empty, refreshing with limited pages...")
            refresh_result = retriever.refresh_documentation(max_pages=20)
            current_count = refresh_result["total_chunks_in_db"]
        
        if current_count == 0:
            return {
                "status": "empty_database",
                "message": "No Reflex documentation indexed. Use refresh_reflex_docs tool first.",
                "results": [],
                "query": query
            }
        
        # Perform search
        results = retriever.search(query, n_results=max_results)
        
        return {
            "status": "success",
            "query": query,
            "results_count": len(results),
            "total_docs_in_db": current_count,
            "results": results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}",
            "query": query,
            "results": []
        }

@mcp.tool()
def refresh_reflex_docs(max_pages: int = None, force_refresh: bool = False) -> dict:
    """
    Refresh the Reflex documentation database by scraping the latest docs.
    
    Args:
        max_pages: Maximum number of pages to scrape (None for all)
        force_refresh: Whether to re-scrape even if docs exist
    
    Returns:
        Dictionary with refresh results and statistics
    """
    try:
        current_count = retriever.collection.count()
        
        if current_count > 0 and not force_refresh:
            return {
                "status": "skipped",
                "message": f"Database already contains {current_count} chunks. Use force_refresh=True to re-scrape.",
                "current_chunk_count": current_count
            }
        
        print("Starting Reflex documentation refresh...")
        refresh_stats = retriever.refresh_documentation(max_pages=max_pages)
        
        return {
            "status": "completed",
            "message": "Reflex documentation database refreshed successfully",
            **refresh_stats
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Refresh failed: {str(e)}"
        }

@mcp.tool()
def detect_reflex_intent(text: str) -> dict:
    """
    Simple tool to detect if text is Reflex-related (for testing/debugging).
    
    Args:
        text: Text to analyze
        
    Returns:
        Detection results
    """
    try:
        is_reflex, confidence, keywords = coordinator.detect_reflex_intent(text)
        
        return {
            "is_reflex_related": is_reflex,
            "confidence": confidence,
            "matched_keywords": keywords,
            "text": text
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "text": text
        }

@mcp.tool()
def refresh_reflex_docs_from_xml(xml_file_path: str, force_refresh: bool = True) -> dict:
    """
    Refresh the documentation database by parsing a local XML file.
    
    Args:
        xml_file_path: The absolute path to the XML file.
        force_refresh: Whether to clear the database before indexing.
    
    Returns:
        Dictionary with refresh results and statistics.
    """
    try:
        print(f"Starting documentation refresh from XML file: {xml_file_path}...")
        stats = retriever.refresh_from_xml_file(xml_file_path=xml_file_path, force_refresh=force_refresh)
        return {
            "status": "completed",
            "message": "Reflex documentation database refreshed successfully from XML.",
            **stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"XML Refresh failed: {str(e)}"
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reflex Docs MCP Server CLI")
    parser.add_argument("command", nargs='?', default="run", help="Command to run: 'run' or 'test-search'")
    parser.add_argument("--query", help="Search query for test-search")

    args = parser.parse_args()

    if args.command == "test-search":
        query = args.query if args.query else "how to add a button"
        print(f"--- Testing Search for: '{query}' ---")
        retriever = ReflexDocsRetriever()
        results = retriever.search(query, n_results=5)
        if results:
            for i, res in enumerate(results, 1):
                print(f"\n--- Result {i} (Score: {res['similarity_score']:.4f}) ---")
                print(f"URL: {res['url']}")
                print(f"Title: {res['title']}")
                print("Content:")
                print(res['content'])
                print("-" * 20)
        else:
            print("No results found.")
    elif args.command == "run":
        mcp.run()
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
