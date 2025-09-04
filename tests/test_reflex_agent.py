#!/usr/bin/env python3
"""
Test script for the Reflex intelligent agent functionality
"""

import os
import sys
# Add parent directory to path so we can import the server
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from reflex_docs_server_enhanced import retriever, coordinator

def test_database_status():
    """Test database status"""
    print("=== Reflex Database Status ===")
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
            print("❌ Database is empty - need to run refresh_reflex_docs")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_intent_detection():
    """Test Reflex intent detection"""
    print("\n=== Intent Detection Tests ===")
    
    test_cases = [
        "How do I create a button in Reflex?",
        "What is the weather today?",
        "Show me how to use rx.text component",
        "Create a Python function to sort numbers",
        "How to manage state in Reflex apps?",
        "What is the capital of France?",
        "How to deploy a Reflex application?",
        "Create a responsive layout with rx components",
        "Build a fullstack Python web app",
        "React component styling in Reflex"
    ]
    
    for query in test_cases:
        try:
            is_reflex, confidence, keywords = coordinator.detect_reflex_intent(query)
            status = "✅ REFLEX" if is_reflex else "❌ NOT REFLEX"
            print(f"{status} | {confidence:.2f} | {query}")
            if keywords:
                print(f"    Keywords: {keywords}")
        except Exception as e:
            print(f"❌ Error with '{query}': {e}")

def test_search_functionality():
    """Test search functionality"""
    print("\n=== Search Tests ===")
    
    count = retriever.collection.count()
    if count == 0:
        print("⚠️ Database is empty. Run refresh first to test search.")
        return
    
    test_queries = [
        "button component",
        "state management", 
        "routing pages",
        "styling themes",
        "database models"
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
    
    test_request = "How do I create a simple Reflex app with state management?"
    
    try:
        print(f"User request: {test_request}")
        
        # Step 1: Intent detection
        is_reflex, confidence, keywords = coordinator.detect_reflex_intent(test_request)
        print(f"Intent detected: {is_reflex} (confidence: {confidence:.2f})")
        print(f"Keywords: {keywords}")
        
        if is_reflex:
            # Step 2: Extract search queries
            search_queries = coordinator.extract_search_queries(test_request, keywords)
            print(f"Search queries: {search_queries}")
            
            # Check if database has content
            count = retriever.collection.count()
            if count > 0:
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
            else:
                print("⚠️ Database is empty - cannot test retrieval functionality")
        
    except Exception as e:
        print(f"❌ Error in intelligent agent test: {e}")

def test_quick_refresh():
    """Test refreshing with a few pages"""
    print("\n=== Quick Refresh Test ===")
    
    try:
        print("Testing refresh with 5 pages...")
        refresh_stats = retriever.refresh_documentation(max_pages=5)
        
        print("Refresh results:")
        for key, value in refresh_stats.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"❌ Error in refresh test: {e}")

if __name__ == "__main__":
    print("Testing Reflex Docs Intelligent Agent")
    print("=" * 50)
    
    test_database_status()
    test_intent_detection()
    
    # Ask user if they want to test with actual data
    print(f"\n{'='*50}")
    print("Database tests require indexed documentation.")
    print("Would you like to:")
    print("1. Test search with existing data (if any)")
    print("2. Run quick refresh (5 pages) then test") 
    print("3. Skip database-dependent tests")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        test_search_functionality()
        test_intelligent_agent()
    elif choice == "2":
        test_quick_refresh()
        test_search_functionality()
        test_intelligent_agent()
    else:
        print("Skipping database-dependent tests")
    
    print("\n" + "=" * 50)
    print("Testing completed!")
