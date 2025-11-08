import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urlparse
import trafilatura
import time
import random
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Selenium imports for Amazon scraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logger = logging.getLogger(__name__)

# Initialize UserAgent for rotating user agents
ua = UserAgent()

def create_session_with_retries():
    """
    Create a requests session with retry logic and better headers
    """
    session = requests.Session()

    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

def get_random_headers():
    """
    Generate random headers to avoid bot detection
    """
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }

def make_request_with_retry(url, session=None, max_retries=3, delay_range=(1, 3)):
    """
    Make HTTP request with retry logic and random delays
    """
    if session is None:
        session = create_session_with_retries()

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            # Add random delay between requests
            if attempt > 0:
                delay = random.uniform(*delay_range) * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying request in {delay:.2f} seconds (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(delay)

            headers = get_random_headers()
            logger.info(f"Making request to {url} with User-Agent: {headers['User-Agent'][:50]}...")

            response = session.get(url, headers=headers, timeout=15)

            # Check for bot detection patterns
            if "captcha" in response.text.lower() or "robot" in response.text.lower():
                logger.warning(f"Bot detection detected for {url}")
                if attempt < max_retries:
                    continue
                else:
                    raise Exception("Bot detection triggered")

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.warning(f"Request attempt {attempt + 1} failed: {e}")

            if attempt == max_retries:
                break

    # If we get here, all retries failed
    logger.error(f"All {max_retries + 1} attempts failed for {url}")
    raise last_exception

def get_product_price(url):
    """
    Scrape the product price from the given URL with improved error handling

    Args:
        url (str): URL of the product

    Returns:
        tuple: (product_name, current_price, product_image_url)
    """
    try:
        domain = urlparse(url).netloc.lower()

        if 'amazon' in domain:
            return scrape_amazon_selenium(url)
        elif 'flipkart' in domain:
            return scrape_flipkart_selenium(url)
        elif 'bestbuy' in domain:
            return scrape_bestbuy_selenium(url)
        else:
            # For unsupported websites, try a generic approach with trafilatura
            logger.info(f"Using generic scraper for unsupported domain: {domain}")
            return scrape_generic(url)

    except Exception as e:
        logger.error(f"Unexpected error scraping {url}: {e}")
        return "Unknown Product", None, None

def clean_price(price_str):
    """Extract numeric price from string and convert to float"""
    if not price_str or not isinstance(price_str, str):
        return None
    # Remove currency symbols (₹, $), commas, whitespace, and other non-numeric except dot
    price_str = price_str.strip()
    price_str = re.sub(r'[₹$,\s]', '', price_str)
    price_str = re.sub(r'[^0-9.]', '', price_str)
    if not price_str:
        return None
    try:
        # Handle cases like '123.4567' or '123.45'
        return float(price_str)
    except ValueError:
        # Try splitting if multiple dots
        parts = price_str.split('.')
        if len(parts) == 2 and len(parts[1]) <= 2:
            return float(price_str)
        return None

def scrape_amazon_selenium(url):
    """Extract product details from Amazon using Selenium for JavaScript-rendered content"""
    driver = None
    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Initialize the driver with Service
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        logger.info(f"Fetching Amazon product page: {url}")
        driver.get(url)

        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        )

        # Extract product name
        product_name = "Unknown Product"
        try:
            title_elem = driver.find_element(By.ID, "productTitle")
            product_name = title_elem.text.strip()
        except NoSuchElementException:
            logger.warning("Product title not found")

        # Extract price
        price = None
        price_selectors = [
            '.a-price .a-offscreen',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '#priceblock_saleprice',
            '[data-cy="price-recipe"] .a-price .a-offscreen',
            '.a-price[data-cy="apex-price-to-pay"] .a-offscreen',
            '#corePriceDisplay_desktop_feature_div .a-price-whole',
            '#apex_offerDisplay_mobile_feature_div .a-price .a-offscreen'
        ]

        for selector in price_selectors:
            try:
                price_elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                price_text = price_elem.text.strip()
                price = clean_price(price_text)
                if price is not None:
                    logger.info(f"Price found using selector {selector}: {price}")
                    break
            except (TimeoutException, NoSuchElementException):
                continue

        # If price not found, try combining whole and fraction
        if price is None:
            try:
                whole_elem = driver.find_element(By.CSS_SELECTOR, '.a-price-whole')
                fraction_elem = driver.find_element(By.CSS_SELECTOR, '.a-price-fraction')
                price_str = whole_elem.text.strip() + '.' + fraction_elem.text.strip()
                price = clean_price(price_str)
                logger.info(f"Price found by combining parts: {price}")
            except NoSuchElementException:
                logger.warning("Price parts not found")

        # Extract product image
        img_url = None
        try:
            img_elem = driver.find_element(By.ID, "landingImage")
            img_url = img_elem.get_attribute("src")
        except NoSuchElementException:
            try:
                img_elem = driver.find_element(By.ID, "imgBlkFront")
                img_url = img_elem.get_attribute("src")
            except NoSuchElementException:
                logger.warning("Product image not found")

        logger.info(f"Scraped Amazon product: {product_name}, Price: {price}, Image: {img_url}")
        return product_name, price, img_url

    except Exception as e:
        logger.error(f"Error scraping Amazon with Selenium: {e}")
        return "Unknown Product", None, None
    finally:
        if driver:
            driver.quit()

def scrape_flipkart_selenium(url):
    """Extract product details from Flipkart using Selenium for JavaScript-rendered content"""
    driver = None
    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Initialize the driver with Service
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        logger.info(f"Fetching Flipkart product page: {url}")
        driver.get(url)

        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "B_NuCI"))
        )

        # Extract product name
        product_name = "Unknown Product"
        try:
            title_elem = driver.find_element(By.CLASS_NAME, "B_NuCI")
            product_name = title_elem.text.strip()
        except NoSuchElementException:
            logger.warning("Product title not found")

        # Extract price
        price = None
        price_selectors = [
            '._30jeq3._16Jk6d',
            '._30jeq3',
            '._16Jk6d'
        ]

        for selector in price_selectors:
            try:
                price_elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                price_text = price_elem.text.strip()
                price = clean_price(price_text)
                if price is not None:
                    logger.info(f"Price found using selector {selector}: {price}")
                    break
            except (TimeoutException, NoSuchElementException):
                continue

        # Extract product image
        img_url = None
        try:
            img_elem = driver.find_element(By.CLASS_NAME, "_396cs4")
            img_url = img_elem.get_attribute("src")
        except NoSuchElementException:
            logger.warning("Product image not found")

        logger.info(f"Scraped Flipkart product: {product_name}, Price: {price}, Image: {img_url}")
        return product_name, price, img_url

    except Exception as e:
        logger.error(f"Error scraping Flipkart with Selenium: {e}")
        return "Unknown Product", None, None
    finally:
        if driver:
            driver.quit()

def scrape_bestbuy_selenium(url):
    """Extract product details from Best Buy using Selenium for JavaScript-rendered content"""
    driver = None
    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Initialize the driver with Service
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        logger.info(f"Fetching Best Buy product page: {url}")
        driver.get(url)

        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".heading-5, .sku-title h1"))
        )

        # Extract product name
        product_name = "Unknown Product"
        try:
            title_elem = driver.find_element(By.CSS_SELECTOR, ".heading-5")
            product_name = title_elem.text.strip()
        except NoSuchElementException:
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, ".sku-title h1")
                product_name = title_elem.text.strip()
            except NoSuchElementException:
                logger.warning("Product title not found")

        # Extract price
        price = None
        price_selectors = [
            '.priceView-customer-price span',
            '.priceView-binding-price',
            '.priceView-hero-price span'
        ]

        for selector in price_selectors:
            try:
                price_elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                price_text = price_elem.text.strip()
                price = clean_price(price_text)
                if price is not None:
                    logger.info(f"Price found using selector {selector}: {price}")
                    break
            except (TimeoutException, NoSuchElementException):
                continue

        # Extract product image
        img_url = None
        try:
            img_elem = driver.find_element(By.CLASS_NAME, "primary-image")
            img_url = img_elem.get_attribute("src")
        except NoSuchElementException:
            try:
                img_elem = driver.find_element(By.CSS_SELECTOR, ".picture-wrapper img")
                img_url = img_elem.get_attribute("src")
            except NoSuchElementException:
                logger.warning("Product image not found")

        logger.info(f"Scraped Best Buy product: {product_name}, Price: {price}, Image: {img_url}")
        return product_name, price, img_url

    except Exception as e:
        logger.error(f"Error scraping Best Buy with Selenium: {e}")
        return "Unknown Product", None, None
    finally:
        if driver:
            driver.quit()



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
    Search Amazon for products in the given category using improved requests and return a list of product details.

    Args:
        category (str): The product category to search for.

    Returns:
        list of dict: Each dict contains 'name', 'price', 'image', and 'url' keys.
    """
    import logging

    logger = logging.getLogger(__name__)

    search_url = f"https://www.amazon.com/s?k={category.replace(' ', '+')}"
    logger.info(f"Searching Amazon for category: {category}, URL: {search_url}")

    try:
        # Create session with retry logic
        session = create_session_with_retries()

        # Add random delay before making request
        time.sleep(random.uniform(1, 3))

        response = make_request_with_retry(search_url, session=session)

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
        logger.error(f"Error fetching Amazon category search results: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing Amazon category search results: {e}")
        return []
