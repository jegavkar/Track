from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import TrackedProduct, PriceHistory
from .scraper import get_product_price
import logging

logger = logging.getLogger(__name__)

def update_product_price(tracked_product):
    """
    Update the price of a tracked product
    
    Args:
        tracked_product (TrackedProduct): The product to update
        
    Returns:
        bool: True if price was updated successfully, False otherwise
    """
    try:
        # Scrape the latest price
        product_name, current_price, product_image = get_product_price(tracked_product.product_url)
        
        if current_price is None:
            logger.warning(f"Could not retrieve price for {tracked_product.product_url}")
            return False
            
        # If this is the first price update, set the original price
        if tracked_product.original_price is None:
            tracked_product.original_price = current_price
            
        # Set product name if it doesn't exist yet
        if not tracked_product.product_name:
            tracked_product.product_name = product_name
            
        # Set product image if available
        if product_image and not tracked_product.product_image:
            tracked_product.product_image = product_image
            
        # Check if price has changed
        price_changed = tracked_product.current_price != current_price
        
        # Update the current price
        tracked_product.current_price = current_price
        tracked_product.save()
        
        # If price changed, add to price history
        if price_changed:
            PriceHistory.objects.create(
                product=tracked_product,
                price=current_price
            )
            
        # Check if target price reached and notification not sent yet
        if not tracked_product.notification_sent and tracked_product.target_reached():
            send_price_alert(tracked_product)
            tracked_product.notification_sent = True
            tracked_product.save()
            
        return True
            
    except Exception as e:
        logger.error(f"Error updating product {tracked_product.id}: {e}")
        return False

def send_price_alert(tracked_product):
    """
    Send an email alert when the price drops below the target
    
    Args:
        tracked_product (TrackedProduct): The product with price drop
    """
    try:
        # Get user's email
        user_email = tracked_product.user.email
        
        if not user_email:
            logger.warning(f"No email found for user {tracked_product.user.username}")
            return
            
        # Prepare email content
        subject = f"Price Drop Alert for {tracked_product.product_name}"
        
        # Render HTML email
        html_message = render_to_string('tracker/emails/price_drop.html', {
            'user': tracked_product.user,
            'product': tracked_product,
            'price_difference': tracked_product.price_difference(),
            'percentage_drop': round(tracked_product.price_difference_percentage(), 2)
        })
        
        # Plain text alternative
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER or 'pricetracker@example.com',
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Price alert sent to {user_email} for {tracked_product.product_name}")
        
    except Exception as e:
        logger.error(f"Error sending price alert: {e}")
