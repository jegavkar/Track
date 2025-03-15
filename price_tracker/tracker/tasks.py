import logging
from django.utils import timezone
from .models import TrackedProduct
from .services import update_product_price

logger = logging.getLogger(__name__)

def check_prices():
    """
    Check prices for all products that need updating
    This function can be scheduled using a cron job or Celery task
    """
    logger.info("Starting scheduled price check")
    
    # Get all products that need to be updated
    products_to_update = TrackedProduct.objects.all()
    
    updated_count = 0
    error_count = 0
    
    for product in products_to_update:
        try:
            if product.needs_update():
                success = update_product_price(product)
                if success:
                    updated_count += 1
                else:
                    error_count += 1
        except Exception as e:
            logger.error(f"Error checking price for product {product.id}: {e}")
            error_count += 1
    
    logger.info(f"Price check completed. Updated: {updated_count}, Errors: {error_count}")

# Example for running this task manually (for testing)
def run_manual_price_check():
    """Run a manual price check for all products"""
    check_prices()

# To schedule this with a cron job, create a Django management command that calls check_prices()
# For Celery, you would define a task that calls check_prices()
