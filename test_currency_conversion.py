#!/usr/bin/env python3
"""
Test script for currency conversion functionality
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'price_tracker'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'price_tracker.settings')
django.setup()

from price_tracker.tracker.services import convert_to_inr

def test_currency_conversion():
    """Test the convert_to_inr function with various URLs"""

    test_cases = [
        # Amazon.com (USD to INR)
        ("https://www.amazon.com/product", 100.0, 8300.0),
        # Amazon.in (INR to INR - no conversion)
        ("https://www.amazon.in/product", 5000.0, 5000.0),
        # Flipkart.com (INR to INR - no conversion)
        ("https://www.flipkart.com/product", 3000.0, 3000.0),
        # Best Buy (USD to INR)
        ("https://www.bestbuy.com/product", 200.0, 16600.0),
        # Unknown domain (no conversion)
        ("https://www.unknownsite.com/product", 1500.0, 1500.0),
    ]

    print("Testing Currency Conversion Logic:")
    print("=" * 50)

    all_passed = True
    for url, input_price, expected_price in test_cases:
        result = convert_to_inr(input_price, url)
        passed = abs(result - expected_price) < 0.01  # Allow small floating point differences

        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {url}")
        print(f"  Input: ${input_price} -> Expected: ₹{expected_price} -> Got: ₹{result}")
        if not passed:
            all_passed = False
        print()

    if all_passed:
        print("🎉 All currency conversion tests passed!")
    else:
        print("❌ Some tests failed!")

    return all_passed

if __name__ == "__main__":
    test_currency_conversion()
