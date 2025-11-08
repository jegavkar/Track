# TODO: Modify Uncategorised Products Update to Only Update Amazon Products

## Tasks:
- [x] Modify `update_uncategorized_prices_history` view in `views.py` to filter uncategorized products by Amazon URLs (product_url__icontains='amazon')
- [x] Modify `update_uncategorized_prices` view in `views.py` to filter uncategorized products by Amazon URLs (product_url__icontains='amazon')
- [x] Update the button text in `product_history.html` from "Update All Prices" to "Update Amazon Prices"
- [x] Update success messages in views to reflect "Amazon uncategorized products"
- [x] Modify management command to filter uncategorized products by Amazon URLs
- [x] Test the changes to ensure only Amazon products are updated
