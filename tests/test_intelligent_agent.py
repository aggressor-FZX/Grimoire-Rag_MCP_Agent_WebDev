#!/usr/bin/env python3
"""
Test script for the intelligent agent functionality
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from composio_docs_server_enhanced import retriever, coordinator

def test_database_status():
    """Test database status"""
    print("=== Database Status ===")
    try:
        count = retriever.collection.count()
        print(f"Total chunks in database: {count}")
        
        if count > 0:
            # Get sample data
            sample_data = retriever.collection.peek(limit=3)
            sample_urls = [metadata.get('url', 'Unknown') for metadata in sample_data.get('metadatas', [])]
            print(f"Sample sources: {sample_urls}")
            print("✅ Database is ready")
        else:
            print("❌ Database is empty")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_intent_detection():
    """Test Composio intent detection"""
    print("\n=== Intent Detection Tests ===")
    
    test_cases = [
        "How do I authenticate with Composio?",
        "What is the weather today?",
        "Show me how to use Composio tools",
        "Create a Python function to sort numbers",
        "How to integrate Composio with my agent?",
        "What is the capital of France?"
    ]
    
    for query in test_cases:
        try:
            is_composio, confidence, keywords = coordinator.detect_composio_intent(query)
            status = "✅ COMPOSIO" if is_composio else "❌ NOT COMPOSIO"
            print(f"{status} | {confidence:.2f} | {query}")
            if keywords:
                print(f"    Keywords: {keywords}")
        except Exception as e:
            print(f"❌ Error with '{query}': {e}")

def test_search_functionality():
    """Test search functionality"""
    print("\n=== Search Tests ===")
    
    test_queries = [
        "authentication setup",
        "tool integration", 
        "getting started"
    ]
    
    for query in test_queries:
        try:
            results = retriever.search(query, n_results=2)
            print(f"\nQuery: '{query}'")
            print(f"Found {len(results)} results")
            
            for i, result in enumerate(results):
                print(f"  {i+1}. Score: {result['similarity_score']:.3f}")
                print(f"     URL: {result['url']}")
                print(f"     Preview: {result['content'][:100]}...")
                
        except Exception as e:
            print(f"❌ Error searching '{query}': {e}")

def test_intelligent_agent():
    """Test the full intelligent agent workflow"""
    print("\n=== Intelligent Agent Test ===")
    
    test_request = "How do I set up authentication with Composio API?"
    
    try:
        print(f"User request: {test_request}")
        
        # Step 1: Intent detection
        is_composio, confidence, keywords = coordinator.detect_composio_intent(test_request)
        print(f"Intent detected: {is_composio} (confidence: {confidence:.2f})")
        print(f"Keywords: {keywords}")
        
        if is_composio:
            # Step 2: Extract search queries
            search_queries = coordinator.extract_search_queries(test_request, keywords)
            print(f"Search queries: {search_queries}")
            
            # Step 3: Retrieve documentation
            all_results = []
            for query in search_queries:
                results = retriever.search(query, n_results=2)
                all_results.extend(results)
            
            print(f"Found {len(all_results)} total results")
            
            # Step 4: Format context
            if all_results:
                formatted_context = coordinator.format_context_for_prompt(all_results[:3], test_request)
                print(f"Formatted context length: {len(formatted_context)} characters")
                print("Context preview:")
                print(formatted_context[:500] + "..." if len(formatted_context) > 500 else formatted_context)
        
    except Exception as e:
        print(f"❌ Error in intelligent agent test: {e}")

if __name__ == "__main__":
    print("Testing Composio Docs Intelligent Agent")
    print("=" * 50)
    
    test_database_status()
    test_intent_detection()
    test_search_functionality()
    test_intelligent_agent()
    
    print("\n" + "=" * 50)
    print("Testing completed!")
