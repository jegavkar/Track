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
        price_selectors = [
            '.a-price .a-offscreen',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '.a-price-whole',
            '.a-price .a-price-whole'
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
