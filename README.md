# TrackMyDeal

A Django-based web application that allows users to track product prices from various online stores (Amazon, Flipkart, Best Buy, and more) and receive notifications when prices drop below their target.

## Project Structure

```
price_tracker/
├── manage.py               # Django management script
├── price_tracker/          # Project settings package
│   ├── __init__.py
│   ├── asgi.py 
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py
└── tracker/                # Main application package
    ├── __init__.py
    ├── admin.py            # Admin interface configuration
    ├── apps.py
    ├── forms.py            # Form definitions
    ├── migrations/         # Database migrations
    ├── models.py           # Database models
    ├── scraper.py          # Web scraping functionality
    ├── services.py         # Business logic services
    ├── tasks.py            # Scheduled tasks
    ├── templates/          # HTML templates
    │   └── tracker/
    │       ├── base.html   # Base template with common elements
    │       ├── home.html   # Homepage template
    │       └── ...         # Other templates
    ├── urls.py             # App URL configuration
    └── views.py            # View functions
```

## Features

- Track prices from multiple e-commerce websites:
  - Amazon
  - Flipkart
  - Best Buy
  - Generic support for other online stores
- User registration and authentication
- Set target prices for products
- Price history tracking
- Email notifications when prices drop below target
- Responsive UI with Bootstrap

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

## Installation

### 1. Clone the repository (or download and extract the ZIP file)

```bash
git clone https://github.com/yourusername/price-tracker.git
cd price_tracker
```

### 2. Create and activate a virtual environment (optional but recommended)

#### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
# Install required packages
pip install django>=4.2.0 beautifulsoup4>=4.9.3 requests>=2.25.1 trafilatura>=1.4.0
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (admin) account

```bash
python manage.py createsuperuser
```
Follow the prompts to set up your admin username, email, and password.

### 6. Run the development server

```bash
python manage.py runserver
```

The application will be available at http://127.0.0.1:8000/

## Usage

1. **Register**: Create a user account by clicking on the "Register" link in the navigation bar
2. **Login**: Sign in with your credentials
3. **Track a Product**: Enter a product URL from Amazon, Flipkart, Best Buy, or other online stores in the form
4. **Set Target Price**: Enter the price you want to pay for the product
5. **Monitor Prices**: View your tracked products in the dashboard
6. **Check Prices Manually**: Click "Check Price Now" on any product to update its price
7. **View Price History**: See the price history of any tracked product

## Admin Access

Access the admin interface at http://127.0.0.1:8000/admin/ using the superuser credentials you created earlier. Here you can:

- Manage users
- View and edit tracked products
- Access price history data

## Scheduled Price Checking

The application includes a management command to check prices automatically:

```bash
python manage.py runpricecheck
```

For production, set up a scheduled task using:
- **Linux/Mac**: Cron job
- **Windows**: Task Scheduler
- **Deployment Services**: Use the scheduler provided by your hosting service

## Understanding the Scraper

The web scraper is a key component of this application, allowing it to extract product information from different online stores.

### Supported E-commerce Platforms

1. **Amazon**: Extracts product name, price, and image URL
2. **Flipkart**: Extracts product name, price, and image URL
3. **Best Buy**: Extracts product name, price, and image URL
4. **Other Websites**: Uses the `trafilatura` library to extract general product information

### How Scraping Works

The application follows these steps to track prices:

1. Sends a request to the product URL with appropriate headers
2. Parses the HTML content using BeautifulSoup
3. Identifies the website based on the URL domain
4. Uses site-specific selectors to extract product details
5. For unsupported websites, falls back to the generic scraper
6. Stores the extracted information in the database

### Customizing Scrapers

If you want to add support for additional e-commerce websites:

1. Identify the CSS selectors for product name, price, and image
2. Add a new condition in the `get_product_price()` function
3. Implement a new scraper function following the pattern of existing ones
4. Update the UI to mention the newly supported website

## Troubleshooting

If you encounter any issues:

1. **Database Errors**: Make sure all migrations are applied
   ```bash
   python manage.py migrate
   ```

2. **Scraping Issues**: Some websites may block scraping attempts. Try:
   - Using a different user agent
   - Implementing delays between requests
   - Using a proxy
   - For complex sites, consider implementing a browser automation solution

3. **Package Installation Problems**: Ensure you're using a compatible Python version and have pip updated
   ```bash
   pip install --upgrade pip
   ```

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgements

- Django - The web framework used
- Beautiful Soup - HTML parsing library
- Trafilatura - Web scraping and text extraction tool
- Bootstrap - Frontend framework