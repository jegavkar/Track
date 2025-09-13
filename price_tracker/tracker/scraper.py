import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urlparse
import trafilatura

# Set up logging
logger = logging.getLogger(__name__)

def get_product_price(url):
    """
    Scrape the product price from the given URL
    
    Args:
        url (str): URL of the product
        
    Returns:
        tuple: (product_name, current_price, product_image_url)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        domain = urlparse(url).netloc
        
        if 'amazon' in domain:
            return scrape_amazon(soup, url)
        elif 'flipkart' in domain:
            return scrape_flipkart(soup, url)
        elif 'bestbuy' in domain:
            return scrape_bestbuy(soup, url)
        else:
            # For unsupported websites, try a generic approach with trafilatura
            return scrape_generic(url)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        raise

def clean_price(price_str):
    """Extract numeric price from string and convert to float"""
    if not price_str:
        return None
    # Remove currency symbols, commas, and whitespace
    price_str = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(price_str)
    except ValueError:
        return None

def scrape_amazon(soup, url):
    """Extract product details from Amazon"""
    try:
        # Try to get product name
        product_name = soup.select_one('#productTitle')
        product_name = product_name.get_text().strip() if product_name else "Unknown Product"
        
        # Try different price selectors (Amazon changes these frequently)
        price = None

        # First, try the combined price in a-offscreen
        price_element = soup.select_one('.a-price .a-offscreen')
        if price_element:
            price = clean_price(price_element.get_text())
        else:
            # Try combining whole and fraction parts
            price_whole = soup.select_one('span.a-price-whole')
            price_fraction = soup.select_one('span.a-price-fraction')
            if price_whole:
                price_str = price_whole.get_text().strip()
                if price_fraction:
                    price_str += '.' + price_fraction.get_text().strip()
                price = clean_price(price_str)

        # Fallback to other selectors
        if not price:
            price_selectors = [
                '#priceblock_ourprice',
                '#priceblock_dealprice',
                '.a-price-whole'
            ]
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    price = clean_price(price_element.get_text())
                    if price:
                        break
        
        # Try to get product image
        img_element = soup.select_one('#landingImage') or soup.select_one('#imgBlkFront')
        img_url = img_element.get('src') if img_element else None
        
        return product_name, price, img_url
        
    except Exception as e:
        logger.error(f"Error parsing Amazon product: {e}")
        return "Unknown Product", None, None

def scrape_flipkart(soup, url):
    """Extract product details from Flipkart"""
    try:
        # Try to get product name
        product_name = soup.select_one('.B_NuCI')
        product_name = product_name.get_text().strip() if product_name else "Unknown Product"
        
        # Try to get product price
        price_element = soup.select_one('._30jeq3._16Jk6d')
        price = clean_price(price_element.get_text()) if price_element else None
        
        # Try to get product image
        img_element = soup.select_one('._396cs4')
        img_url = img_element.get('src') if img_element else None
        
        return product_name, price, img_url
        
    except Exception as e:
        logger.error(f"Error parsing Flipkart product: {e}")
        return "Unknown Product", None, None

def scrape_bestbuy(soup, url):
    """Extract product details from Best Buy"""
    try:
        # Try to get product name
        product_name = soup.select_one('.heading-5')
        if not product_name:
            product_name = soup.select_one('.sku-title h1')
        product_name = product_name.get_text().strip() if product_name else "Unknown Product"
        
        # Try to get product price
        price_element = soup.select_one('.priceView-customer-price span')
        if not price_element:
            price_element = soup.select_one('.priceView-binding-price')
        price = clean_price(price_element.get_text()) if price_element else None
        
        # Try to get product image
        img_element = soup.select_one('.primary-image')
        if not img_element:
            img_element = soup.select_one('.picture-wrapper img')
        img_url = img_element.get('src') if img_element else None
        
        return product_name, price, img_url
        
    except Exception as e:
        logger.error(f"Error parsing Best Buy product: {e}")
        return "Unknown Product", None, None

def scrape_generic(url):
    """Extract product details using trafilatura for unsupported websites"""
    try:
        logger.info(f"Using generic scraper for {url}")
        
        # Download the content
        downloaded = trafilatura.fetch_url(url)
        
        # Extract the main text content
        text_content = trafilatura.extract(downloaded)
        
        if not text_content:
            return "Unknown Product", None, None
        
        # Extract metadata
        metadata = trafilatura.extract_metadata(downloaded)
        
        # Use metadata for product name if available
        product_name = "Unknown Product"
        if metadata and metadata.title:
            product_name = metadata.title
        
        # For price, we can't reliably extract it from generic pages
        # We'll return None and let the user manually update it
        price = None
        
        # Try to get an image from metadata
        img_url = None
        if metadata and hasattr(metadata, 'image'):
            img_url = metadata.image
            
        return product_name, price, img_url
        
    except Exception as e:
        logger.error(f"Error parsing website with generic method: {e}")
        return "Unknown Product", None, None

def search_amazon_category(category):
    """
    Search Amazon for products in the given category using requests and BeautifulSoup and return a list of product details.

    Args:
        category (str): The product category to search for.

    Returns:
        list of dict: Each dict contains 'name', 'price', 'image', and 'url' keys.
    """
    import logging

    logger = logging.getLogger(__name__)

    search_url = f"https://www.amazon.com/s?k={category.replace(' ', '+')}"
    logger.info(f"Searching Amazon for category: {category}, URL: {search_url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        results = []

        # Find all search result items
        search_results = soup.select('div.s-main-slot div.s-result-item')
        logger.info(f"Found {len(search_results)} search result items")

        for item in search_results[:10]:  # Limit to top 10 results
            try:
                # Extract product name
                name_elem = item.select_one('h2 a span')
                name = name_elem.get_text().strip() if name_elem else "Unknown Product"

                # Extract product URL
                url_elem = item.select_one('h2 a')
                url = url_elem.get('href') if url_elem else None
                if url and not url.startswith('http'):
                    url = f"https://www.amazon.com{url}"

                # Extract price
                price = None
                try:
                    price_whole = item.select_one('span.a-price-whole')
                    price_fraction = item.select_one('span.a-price-fraction')
                    if price_whole:
                        price_str = price_whole.get_text().strip()
                        if price_fraction:
                            price_str += '.' + price_fraction.get_text().strip()
                        price = float(price_str.replace(',', ''))
                except:
                    pass  # Price not found or parsing error

                # Extract image URL
                img_url = None
                try:
                    img_elem = item.select_one('img.s-image')
                    img_url = img_elem.get('src') if img_elem else None
                except:
                    pass  # Image not found

                results.append({
                    'name': name,
                    'price': price,
                    'image': img_url,
                    'url': url
                })

            except Exception as e:
                logger.warning(f"Error extracting data from search result item: {e}")
                continue

        logger.info(f"Returning {len(results)} products for category {category}")
        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Amazon category search results with requests: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing Amazon category search results: {e}")
        return []
