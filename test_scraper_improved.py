#!/usr/bin/env python3
"""
Test script for scraper_improved.py functionality
"""
import sys
import os

# Add the price_tracker directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'price_tracker'))

from tracker.scraper_improved import get_product_price

def test_get_product_price():
    """Test the get_product_price function with sample URLs"""
    # Sample URLs for testing (use real but simple ones)
    test_urls = [
        # Amazon India example (replace with a real URL if needed)
        "https://www.amazon.in/dp/B08N5WRWNW",  # Example product
        # Flipkart example
        "https://www.flipkart.com/product/p/itm123456",  # Example
    ]

    for url in test_urls:
        print(f"\nTesting URL: {url}")
        try:
            product_name, price, image_url = get_product_price(url)
            print(f"Product Name: {product_name}")
            print(f"Price: {price}")
            print(f"Image URL: {image_url}")
            if price is not None:
                print("SUCCESS: Price extracted!")
            else:
                print("FAILED: Price not found")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == '__main__':
    test_get_product_price()
