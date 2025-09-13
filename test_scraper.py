#!/usr/bin/env python3
"""
Test script for scraper.py functionality
"""
import sys
import os

# Add the price_tracker directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'price_tracker'))

from tracker.scraper import search_amazon_category

def test_search_amazon_category():
    """Test the search_amazon_category function"""
    category = 'laptop'
    print(f"Testing search_amazon_category with category: {category}")

    try:
        results = search_amazon_category(category)
        print(f"Found {len(results)} results")

        if results:
            print("First result:")
            print(f"Name: {results[0]['name']}")
            print(f"Price: {results[0]['price']}")
            print(f"Image: {results[0]['image']}")
            print(f"URL: {results[0]['url']}")
        else:
            print("No results found")

        print("Test passed!")
        return True

    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

if __name__ == '__main__':
    test_search_amazon_category()
