# composio_docs_server_enhanced.py
import os
import re
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import chromadb
from chromadb.config import Settings
import tiktoken
from sentence_transformers import SentenceTransformer
from fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("composio-docs-server-enhanced")

class ComposioDocsRetriever:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.base_url = "https://docs.composio.dev"
        self.collection_name = "composio_docs"
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize tiktoken for text chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name='all-MiniLM-L6-v2'
                )
            )
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name='all-MiniLM-L6-v2'
                )
            )
    
    def get_doc_pages(self) -> List[str]:
        """Get a comprehensive list of documentation pages to scrape"""
        # Core documentation pages - getting started, basics, and fundamentals
        doc_pages = [
            # Main getting started sections
            "/docs/welcome",
            "/docs/getting-started",
            "/docs/installation", 
            "/docs/quickstart",
            "/docs/overview",
            
            # MCP specific documentation
            "/docs/mcp-overview",
            "/docs/mcp-developers",
            "/docs/mcp-getting-started",
            "/docs/mcp-quickstart",
            
            # Authentication and configuration
            "/docs/custom-auth-configs",
            "/docs/authentication",
            "/docs/auth-overview",
            "/docs/auth-setup",
            "/docs/oauth-setup",
            "/docs/auth-management",
            
            # Core concepts and fundamentals
            "/docs/concepts",
            "/docs/core-concepts",
            "/docs/fundamentals",
            "/docs/architecture",
            "/docs/how-it-works",
            "/docs/composio-overview",
            
            # SDK and API basics
            "/sdk-reference/python/python-sdk-reference",
            "/sdk-reference/python/getting-started",
            "/sdk-reference/python/installation",
            "/sdk-reference/python/quickstart",
            "/sdk-reference/javascript/js-sdk-reference",
            "/sdk-reference/javascript/getting-started",
            
            # Toolkits introduction and basics
            "/toolkits/introduction",
            "/toolkits/overview",
            "/toolkits/getting-started",
            "/toolkits/custom-toolkits",
            "/toolkits/toolkit-development",
            
            # Popular providers and integrations
            "/providers/openai",
            "/providers/anthropic", 
            "/providers/google",
            "/providers/azure",
            "/providers/cohere",
            "/providers/overview",
            
            # Common integrations and popular tools
            "/tools/gmail",
            "/tools/slack",
            "/tools/github",
            "/tools/google-calendar",
            "/tools/notion",
            "/tools/trello",
            "/tools/asana",
            "/tools/linear",
            "/tools/jira",
            "/tools/discord",
            "/tools/telegram",
            "/tools/whatsapp",
            
            # Development and usage guides
            "/docs/development",
            "/docs/usage-guide",
            "/docs/best-practices",
            "/docs/troubleshooting",
            "/docs/debugging",
            "/docs/configuration",
            "/docs/environment-setup",
            
            # Examples and tutorials
            "/examples/getting-started",
            "/examples/basic-usage",
            "/examples/advanced-usage",
            "/examples/sample-webserver",
            "/examples/python-examples",
            "/examples/javascript-examples",
            
            # API reference basics
            "/api-reference/overview",
            "/api-reference/getting-started",
            "/api-reference/authentication",
            "/api-reference/auth-configs/get-auth-configs",
            "/api-reference/mcp",
            "/api-reference/tools",
            "/api-reference/actions",
            
            # Platform and dashboard
            "/docs/platform-overview",
            "/docs/dashboard",
            "/docs/workspace-management",
            "/docs/account-setup",
            
            # Advanced topics that are commonly referenced
            "/docs/webhooks",
            "/docs/rate-limiting",
            "/docs/error-handling",
            "/docs/monitoring",
            "/docs/logging",
            "/docs/security",
            "/docs/permissions",
            
            # Migration and updates
            "/docs/migration-guide",
            "/docs/upgrade-guide",
            "/docs/changelog",
            "/docs/versioning",
            
            # Common use cases
            "/docs/use-cases",
            "/docs/automation",
            "/docs/integrations",
            "/docs/workflows",
            "/docs/scheduling"
        ]
        
        # Convert to full URLs and return
        full_urls = [urljoin(self.base_url, page) for page in doc_pages]
        
        # Also try to discover additional pages by checking common patterns
        additional_patterns = [
            "/docs/guides/",
            "/docs/tutorials/", 
            "/examples/",
            "/toolkits/",
            "/providers/"
        ]
        
        # You could extend this to crawl sitemap.xml or nav menu for more pages
        print(f"Configured to scrape {len(full_urls)} documentation pages")
        return full_urls
    
    def scrape_page(self, url: str) -> Dict[str, Any]:
        """Scrape a single documentation page"""
        try:
            # Add headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title - try multiple selectors
            title = ""
            title_selectors = ['title', 'h1', '.page-title', '.doc-title', '[data-testid="page-title"]']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    break
            
            # Remove unwanted elements before extracting content
            unwanted_selectors = [
                'script', 'style', 'nav', 'header', 'footer', 
                '.navigation', '.sidebar', '.toc', '.breadcrumb',
                '.edit-page', '.last-updated', '.page-metadata',
                '.social-links', '.footer-links', '.header-links',
                '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]'
            ]
            
            for selector in unwanted_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Extract main content - try multiple content selectors
            content = ""
            content_selectors = [
                'article',
                '.content',
                '.docs-content', 
                '.documentation-content',
                '.page-content',
                '.main-content',
                'main',
                '[role="main"]',
                '.prose',
                '.markdown-body'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text()
                    break
            
            # Fallback to body if no content found
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text()
            
            # Clean up text
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Skip if content is too short (likely an error page)
            if len(content) < 200:
                print(f"  Warning: Content too short ({len(content)} chars), possibly an error page")
                return None
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'content_length': len(content),
                'content_hash': hashlib.md5(content.encode()).hexdigest()
            }
            
        except requests.exceptions.RequestException as e:
            print(f"  Request error for {url}: {e}")
            return None
        except Exception as e:
            print(f"  Parse error for {url}: {e}")
            return None
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Chunk text into smaller pieces with overlap"""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), chunk_size - overlap):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            if i + chunk_size >= len(tokens):
                break
                
        return chunks
    
    def index_page(self, page_data: Dict[str, Any]):
        """Index a page by chunking and storing in vector DB"""
        if not page_data:
            return
            
        url = page_data['url']
        title = page_data['title']
        content = page_data['content']
        content_hash = page_data['content_hash']
        
        # Check if already indexed with same content
        existing = self.collection.get(
            where={"$and": [{"url": {"$eq": url}}, {"content_hash": {"$eq": content_hash}}]},
            limit=1
        )
        
        if existing['ids']:
            print(f"Page {url} already indexed with same content")
            return
        
        # Delete old versions of this page
        old_docs = self.collection.get(where={"url": {"$eq": url}})
        if old_docs['ids']:
            self.collection.delete(ids=old_docs['ids'])
        
        # Chunk the content
        chunks = self.chunk_text(content)
        
        # Prepare documents for insertion
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue
                
            doc_id = f"{hashlib.md5(url.encode()).hexdigest()}_{i}"
            
            documents.append(chunk)
            metadatas.append({
                "url": url,
                "title": title,
                "chunk_index": i,
                "content_hash": content_hash,
                "source": "composio_docs"
            })
            ids.append(doc_id)
        
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Indexed {len(documents)} chunks from {url}")
    
    def index_all_docs(self):
        """Scrape and index all documentation pages"""
        pages = self.get_doc_pages()
        
        successful_pages = 0
        failed_pages = 0
        total_chunks = 0
        
        print(f"Starting to index {len(pages)} documentation pages...")
        
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
                print(f"  ❌ Error: {str(e)[:100]}...")
        
        final_count = self.collection.count()
        print(f"\n📊 Indexing Summary:")
        print(f"  Total pages attempted: {len(pages)}")
        print(f"  Successful: {successful_pages}")
        print(f"  Failed: {failed_pages}")
        print(f"  New chunks added: {total_chunks}")
        print(f"  Total chunks in database: {final_count}")
        
        return {
            "total_pages": len(pages),
            "successful": successful_pages, 
            "failed": failed_pages,
            "new_chunks": total_chunks,
            "total_chunks": final_count
        }
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search over the indexed documents"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        search_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                search_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'url': results['metadatas'][0][i].get('url', ''),
                    'title': results['metadatas'][0][i].get('title', '')
                })
        
        return search_results

# Initialize the retriever
retriever = ComposioDocsRetriever()

class ComposioAgentCoordinator:
    """Intelligent coordinator for Composio-related requests"""
    
    def __init__(self, retriever: ComposioDocsRetriever):
        self.retriever = retriever
        self.composio_keywords = [
            'composio', 'mcp server', 'mcp servers', 'model context protocol',
            'auth config', 'oauth', 'toolkit', 'tools', 'actions',
            'sdk', 'api', 'integration', 'webhook', 'authentication',
            'gmail', 'slack', 'github', 'notion', 'trello', 'asana',
            'linear', 'jira', 'discord', 'telegram', 'whatsapp',
            'openai', 'anthropic', 'google', 'azure', 'cohere',
            'python sdk', 'javascript sdk', 'fastmcp'
        ]
        
    def detect_composio_intent(self, user_request: str) -> Tuple[bool, float, List[str]]:
        """
        Detect if the user request is about Composio
        Returns: (is_composio_related, confidence_score, matched_keywords)
        """
        request_lower = user_request.lower()
        matched_keywords = []
        
        # Check for explicit mentions
        for keyword in self.composio_keywords:
            if keyword in request_lower:
                matched_keywords.append(keyword)
        
        # Calculate confidence based on keyword matches and context
        confidence = 0.0
        
        if matched_keywords:
            confidence += len(matched_keywords) * 0.2
            
        # Boost confidence for explicit Composio mentions
        if 'composio' in request_lower:
            confidence += 0.5
            
        # Boost for common development patterns with Composio
        development_patterns = [
            'build', 'create', 'develop', 'implement', 'integrate',
            'setup', 'configure', 'connect', 'authenticate', 'sync'
        ]
        
        for pattern in development_patterns:
            if pattern in request_lower and matched_keywords:
                confidence += 0.1
        
        # Boost for API/SDK usage patterns
        api_patterns = ['api', 'sdk', 'function', 'method', 'class', 'import']
        for pattern in api_patterns:
            if pattern in request_lower and matched_keywords:
                confidence += 0.05
                
        confidence = min(confidence, 1.0)  # Cap at 1.0
        is_composio_related = confidence > 0.3 or 'composio' in request_lower
        
        return is_composio_related, confidence, matched_keywords
    
    def extract_search_queries(self, user_request: str, matched_keywords: List[str]) -> List[str]:
        """Extract relevant search queries from the user request"""
        queries = []
        
        # Primary query - the main request
        queries.append(user_request)
        
        # Generate focused queries based on detected keywords
        if 'mcp server' in matched_keywords or 'mcp servers' in matched_keywords:
            queries.append("MCP server setup configuration")
            
        if 'auth' in user_request.lower() or 'authentication' in matched_keywords:
            queries.append("authentication OAuth setup")
            
        if 'sdk' in matched_keywords:
            queries.append("SDK installation usage examples")
            
        # Tool-specific queries
        tool_keywords = ['gmail', 'slack', 'github', 'notion', 'trello', 'asana', 'jira']
        for tool in tool_keywords:
            if tool in matched_keywords:
                queries.append(f"{tool} integration examples")
        
        # Remove duplicates while preserving order
        unique_queries = []
        for query in queries:
            if query not in unique_queries:
                unique_queries.append(query)
                
        return unique_queries[:3]  # Limit to top 3 queries
    
    def format_context_for_prompt(self, search_results: List[Dict], user_request: str) -> str:
        """Format retrieved context for injection into AI prompt"""
        
        if not search_results:
            return ""
            
        context = "\n=== COMPOSIO DOCUMENTATION CONTEXT ===\n"
        context += f"Retrieved documentation relevant to: {user_request}\n\n"
        
        for i, result in enumerate(search_results, 1):
            context += f"--- Source {i} (Relevance: {result['similarity_score']:.3f}) ---\n"
            context += f"Title: {result['title']}\n"
            context += f"URL: {result['url']}\n"
            context += f"Content: {result['content']}\n\n"
            
        context += "=== END COMPOSIO CONTEXT ===\n"
        context += "Please use the above documentation context when generating code or providing guidance about Composio.\n"
        context += "Ensure all methods, classes, and APIs you reference exist in the provided documentation.\n\n"
        
        return context
    
    def validate_code_against_docs(self, generated_code: str) -> Tuple[List[str], List[Dict]]:
        """
        Validate generated code against documentation
        Returns: (potential_issues, validation_results)
        """
        potential_issues = []
        validation_results = []
        
        # Extract potential Composio API calls from code
        api_patterns = [
            r'composio\.([a-zA-Z_][a-zA-Z0-9_]*)',  # composio.method_name
            r'Composio\([^)]*\)',  # Composio() constructor
            r'\.([a-zA-Z_][a-zA-Z0-9_]*)\(',  # .method_name(
            r'@mcp\.tool\(\)',  # MCP decorators
            r'FastMCP\([^)]*\)',  # FastMCP constructor
        ]
        
        found_apis = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, generated_code)
            found_apis.update(matches)
            
        # Search for each API in documentation
        for api in found_apis:
            if len(api) > 2:  # Skip very short matches
                search_results = self.retriever.search(f"{api} method function", n_results=2)
                
                if not search_results or search_results[0]['similarity_score'] < 0.3:
                    potential_issues.append(f"API '{api}' not found in documentation")
                    
                validation_results.extend(search_results)
        
        return potential_issues, validation_results

# Initialize the coordinator
coordinator = ComposioAgentCoordinator(retriever)

@mcp.tool()
def get_database_status() -> dict:
    """
    Get current status of the Composio documentation database.
    
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
            "recommendation": "Database is ready for search" if count > 0 else "Run 'refresh_composio_docs' to populate database"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking database: {str(e)}",
            "database_ready": False
        }

@mcp.tool()
def composio_intelligent_agent(user_request: str, include_code_validation: bool = True) -> dict:
    """
    Intelligent agent that detects Composio-related requests and provides contextual assistance.
    
    This tool automatically:
    1. Detects if the request is Composio-related
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
        # Step 1: Detect Composio intent
        is_composio, confidence, keywords = coordinator.detect_composio_intent(user_request)
        
        if not is_composio:
            return {
                "status": "not_composio_related",
                "confidence": confidence,
                "message": "Request does not appear to be Composio-related",
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
            "status": "composio_detected",
            "confidence": confidence,
            "detected_keywords": keywords,
            "search_queries_used": search_queries,
            "documentation_context": formatted_context,
            "retrieved_sources": len(top_results),
            "user_request": user_request,
            "guidance": {
                "next_steps": [
                    "Use the provided documentation context when generating code",
                    "Reference the specific methods and classes mentioned in the context", 
                    "Follow the patterns shown in the retrieved examples",
                    "Ensure proper authentication setup as described"
                ],
                "key_apis": [result['url'] for result in top_results[:3]]
            }
        }
        
        # Add code validation if requested
        if include_code_validation:
            response["validation_info"] = {
                "message": "After generating code, use 'validate_composio_code' tool to check against documentation",
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
def validate_composio_code(code: str, original_request: str = "") -> dict:
    """
    Validate generated code against Composio documentation.
    
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
                "check_apis": issues if issues else ["All APIs appear to be documented"],
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
def detect_composio_intent(text: str) -> dict:
    """
    Simple tool to detect if text is Composio-related (for testing/debugging).
    
    Args:
        text: Text to analyze
        
    Returns:
        Detection results
    """
    try:
        is_composio, confidence, keywords = coordinator.detect_composio_intent(text)
        
        return {
            "is_composio_related": is_composio,
            "confidence": confidence,
            "matched_keywords": keywords,
            "text": text
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "text": text
        }
    """
    Search the Composio documentation using semantic search.
    
    Args:
        query: The search query or question
        max_results: Maximum number of results to return (default: 5)
        auto_refresh: If True, check if index needs updating (default: False)
    
    Returns:
        Dictionary containing search results with relevant documentation chunks
    """
    try:
        # Optional: Check if we need to refresh the index
        if auto_refresh:
            total_docs = retriever.collection.count()
            if total_docs == 0:
                print("No documents in index, auto-indexing...")
                retriever.index_all_docs()
        
        results = retriever.search(query, n_results=max_results)
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results,
            "status": "success"
        }
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "status": "error"
        }

@mcp.tool()
def index_composio_docs() -> dict:
    """
    Scrape and index all Composio documentation pages.
    This should be run periodically to keep the index updated.
    
    Returns:
        Status of the indexing operation
    """
    try:
        retriever.index_all_docs()
        total_docs = retriever.collection.count()
        
        return {
            "status": "success",
            "message": f"Successfully indexed documentation. Total chunks: {total_docs}",
            "total_chunks": total_docs
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error indexing docs: {str(e)}"
        }

@mcp.tool()
def get_index_stats() -> dict:
    """
    Get statistics about the current documentation index.
    
    Returns:
        Statistics about indexed documents
    """
    try:
        total_docs = retriever.collection.count()
        
        # Get sample of metadata to analyze
        sample = retriever.collection.get(limit=100, include=['metadatas'])
        
        urls = set()
        sources = {}
        
        for metadata in sample['metadatas']:
            if metadata.get('url'):
                urls.add(metadata['url'])
            source = metadata.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "status": "success",
            "total_chunks": total_docs,
            "unique_pages": len(urls),
            "sample_urls": list(urls)[:10],  # First 10 URLs
            "sources": sources
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting stats: {str(e)}"
        }

@mcp.tool()
def get_composio_docs(section: str = None) -> dict:
    """
    Retrieve the latest Composio MCP documentation (legacy function for compatibility).
    For better results, use search_composio_docs instead.
    """
    base_url = "https://docs.composio.dev/docs/mcp-developers"
    url = f"{base_url}#{section}" if section else base_url
    
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return {"content": resp.text}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()
