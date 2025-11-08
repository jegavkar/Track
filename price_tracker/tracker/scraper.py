import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urlparse
import trafilatura
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Set up logging
logger = logging.getLogger(__name__)

def get_chrome_driver():
    """Create a headless Chrome driver for web scraping"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        logger.error(f"Error creating Chrome driver: {e}")
        raise

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
    Search Amazon for products in the given category. Falls back to demo data if scraping fails.

    Args:
        category (str): The product category to search for.

    Returns:
        list of dict: Each dict contains 'name', 'price', 'image', and 'url' keys.
    """
    logger = logging.getLogger(__name__)

    # First try real scraping with requests (fallback method)
    try:
        results = search_amazon_category_requests(category)
        if results:
            logger.info(f"Successfully fetched {len(results)} real products for category {category}")
            return results
    except Exception as e:
        logger.warning(f"Requests scraping failed for {category}: {e}")

    # If requests fail, try Selenium
    try:
        results = search_amazon_category_selenium(category)
        if results:
            logger.info(f"Successfully fetched {len(results)} products with Selenium for category {category}")
            return results
    except Exception as e:
        logger.warning(f"Selenium scraping failed for {category}: {e}")

    # If both scraping methods fail, return demo data
    logger.info(f"Using demo data for category {category}")
    return get_demo_products(category)

def search_amazon_category_requests(category):
    """Original requests-based scraping method"""
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

        search_results = soup.select('div.s-main-slot div.s-result-item')
        logger.info(f"Found {len(search_results)} search result items")

        for item in search_results[:10]:
            try:
                name_elem = item.select_one('h2 a span')
                name = name_elem.get_text().strip() if name_elem else "Unknown Product"

                url_elem = item.select_one('h2 a')
                url = url_elem.get('href') if url_elem else None
                if url and not url.startswith('http'):
                    url = f"https://www.amazon.com{url}"

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
                    pass

                img_url = None
                try:
                    img_elem = item.select_one('img.s-image')
                    img_url = img_elem.get('src') if img_elem else None
                except:
                    pass

                results.append({
                    'name': name,
                    'price': price,
                    'image': img_url,
                    'url': url
                })

            except Exception as e:
                logger.warning(f"Error extracting data from search result item: {e}")
                continue

        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Amazon category search results with requests: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing Amazon category search results: {e}")
        return []

def search_amazon_category_selenium(category):
    """Selenium-based scraping method"""
    search_url = f"https://www.amazon.com/s?k={category.replace(' ', '+')}"
    logger.info(f"Searching Amazon with Selenium for category: {category}, URL: {search_url}")

    driver = None
    try:
        driver = get_chrome_driver()
        driver.get(search_url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.s-main-slot div.s-result-item'))
        )

        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results = []

        search_results = soup.select('div.s-main-slot div.s-result-item')
        logger.info(f"Found {len(search_results)} search result items with Selenium")

        for item in search_results[:10]:
            try:
                name_elem = item.select_one('h2 a span')
                name = name_elem.get_text().strip() if name_elem else "Unknown Product"

                url_elem = item.select_one('h2 a')
                url = url_elem.get('href') if url_elem else None
                if url and not url.startswith('http'):
                    url = f"https://www.amazon.com{url}"

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
                    pass

                img_url = None
                try:
                    img_elem = item.select_one('img.s-image')
                    img_url = img_elem.get('src') if img_elem else None
                except:
                    pass

                results.append({
                    'name': name,
                    'price': price,
                    'image': img_url,
                    'url': url
                })

            except Exception as e:
                logger.warning(f"Error extracting data from search result item: {e}")
                continue

        return results

    except Exception as e:
        logger.error(f"Error fetching Amazon category search results with Selenium: {e}")
        return []
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def get_demo_products(category):
    """Return demo products for when scraping fails"""
    demo_products = {
        'Electronics': [
            {'name': 'Apple iPhone 15 Pro', 'price': 999.99, 'image': 'https://via.placeholder.com/300x200?text=iPhone+15+Pro', 'url': 'https://amazon.com/iphone15pro'},
            {'name': 'Samsung Galaxy S24', 'price': 799.99, 'image': 'https://via.placeholder.com/300x200?text=Galaxy+S24', 'url': 'https://amazon.com/galaxys24'},
            {'name': 'MacBook Air M3', 'price': 1099.99, 'image': 'https://via.placeholder.com/300x200?text=MacBook+Air+M3', 'url': 'https://amazon.com/macbookairm3'},
            {'name': 'Sony WH-1000XM5', 'price': 299.99, 'image': 'https://via.placeholder.com/300x200?text=Sony+WH-1000XM5', 'url': 'https://amazon.com/sonywh1000xm5'},
            {'name': 'Nintendo Switch OLED', 'price': 349.99, 'image': 'https://via.placeholder.com/300x200?text=Nintendo+Switch+OLED', 'url': 'https://amazon.com/nintendoswitcholed'},
        ],
        'Home & Kitchen': [
            {'name': 'Instant Pot Duo 7-in-1', 'price': 79.99, 'image': 'https://via.placeholder.com/300x200?text=Instant+Pot+Duo', 'url': 'https://amazon.com/instantpotduo'},
            {'name': 'KitchenAid Stand Mixer', 'price': 379.99, 'image': 'https://via.placeholder.com/300x200?text=KitchenAid+Mixer', 'url': 'https://amazon.com/kitchenaidmixer'},
            {'name': 'Dyson V15 Cordless Vacuum', 'price': 599.99, 'image': 'https://via.placeholder.com/300x200?text=Dyson+V15', 'url': 'https://amazon.com/dysonv15'},
            {'name': 'Nespresso Coffee Machine', 'price': 199.99, 'image': 'https://via.placeholder.com/300x200?text=Nespresso+Machine', 'url': 'https://amazon.com/nespresso'},
            {'name': 'Air Fryer XL', 'price': 89.99, 'image': 'https://via.placeholder.com/300x200?text=Air+Fryer+XL', 'url': 'https://amazon.com/airfryerxl'},
        ],
        'Clothing': [
            {'name': 'Levi\'s 501 Original Jeans', 'price': 69.99, 'image': 'https://via.placeholder.com/300x200?text=Levis+501+Jeans', 'url': 'https://amazon.com/levis501'},
            {'name': 'Nike Air Max 270', 'price': 129.99, 'image': 'https://via.placeholder.com/300x200?text=Nike+Air+Max+270', 'url': 'https://amazon.com/nikeairmax270'},
            {'name': 'Adidas Ultraboost 22', 'price': 149.99, 'image': 'https://via.placeholder.com/300x200?text=Adidas+Ultraboost', 'url': 'https://amazon.com/adidasultraboost'},
            {'name': 'The North Face Jacket', 'price': 199.99, 'image': 'https://via.placeholder.com/300x200?text=North+Face+Jacket', 'url': 'https://amazon.com/northfacejacket'},
            {'name': 'Ray-Ban Aviator Sunglasses', 'price': 154.99, 'image': 'https://via.placeholder.com/300x200?text=Ray-Ban+Aviator', 'url': 'https://amazon.com/raybanaviator'},
        ],
        'Books': [
            {'name': 'Atomic Habits by James Clear', 'price': 16.99, 'image': 'https://via.placeholder.com/300x200?text=Atomic+Habits', 'url': 'https://amazon.com/atomichabits'},
            {'name': 'The Psychology of Money', 'price': 14.99, 'image': 'https://via.placeholder.com/300x200?text=Psychology+of+Money', 'url': 'https://amazon.com/psychologyofmoney'},
            {'name': 'Educated by Tara Westover', 'price': 12.99, 'image': 'https://via.placeholder.com/300x200?text=Educated', 'url': 'https://amazon.com/educated'},
            {'name': 'Sapiens by Yuval Noah Harari', 'price': 18.99, 'image': 'https://via.placeholder.com/300x200?text=Sapiens', 'url': 'https://amazon.com/sapiens'},
            {'name': 'The Alchemist by Paulo Coelho', 'price': 10.99, 'image': 'https://via.placeholder.com/300x200?text=The+Alchemist', 'url': 'https://amazon.com/thealchemist'},
        ],
        'Beauty & Personal Care': [
            {'name': 'CeraVe Moisturizing Cream', 'price': 15.99, 'image': 'https://via.placeholder.com/300x200?text=CeraVe+Cream', 'url': 'https://amazon.com/ceravecream'},
            {'name': 'The Ordinary Hyaluronic Acid', 'price': 6.99, 'image': 'https://via.placeholder.com/300x200?text=The+Ordinary+HA', 'url': 'https://amazon.com/theordinaryha'},
            {'name': 'Neutrogena Sunscreen SPF 50', 'price': 8.99, 'image': 'https://via.placeholder.com/300x200?text=Neutrogena+SPF50', 'url': 'https://amazon.com/neutrogenasunscreen'},
            {'name': 'L\'Oreal Paris Mascara', 'price': 7.99, 'image': 'https://via.placeholder.com/300x200?text=LOreal+Mascara', 'url': 'https://amazon.com/lorealmascara'},
            {'name': 'Nivea Body Lotion', 'price': 5.99, 'image': 'https://via.placeholder.com/300x200?text=Nivea+Lotion', 'url': 'https://amazon.com/nivealotion'},
        ]
    }

    return demo_products.get(category, [
        {'name': f'Sample {category} Product 1', 'price': 29.99, 'image': 'https://via.placeholder.com/300x200?text=Sample+Product', 'url': 'https://amazon.com/sample1'},
        {'name': f'Sample {category} Product 2', 'price': 49.99, 'image': 'https://via.placeholder.com/300x200?text=Sample+Product', 'url': 'https://amazon.com/sample2'},
        {'name': f'Sample {category} Product 3', 'price': 79.99, 'image': 'https://via.placeholder.com/300x200?text=Sample+Product', 'url': 'https://amazon.com/sample3'},
        {'name': f'Sample {category} Product 4', 'price': 99.99, 'image': 'https://via.placeholder.com/300x200?text=Sample+Product', 'url': 'https://amazon.com/sample4'},
        {'name': f'Sample {category} Product 5', 'price': 149.99, 'image': 'https://via.placeholder.com/300x200?text=Sample+Product', 'url': 'https://amazon.com/sample5'},
    ])
