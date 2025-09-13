from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ProductCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (by {self.user.username})"

    class Meta:
        unique_together = ('user', 'name')

class TrackedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255, blank=True)
    product_url = models.URLField()
    product_image = models.URLField(blank=True, null=True)
    target_price = models.FloatField()
    current_price = models.FloatField(null=True, blank=True)
    original_price = models.FloatField(null=True, blank=True)
    last_checked = models.DateTimeField(auto_now=True)
    date_added = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notification_sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.product_name} - {self.current_price}"
    
    def price_difference(self):
        """Return the price difference between original and current price"""
        if not self.original_price or not self.current_price:
            return 0
        return self.original_price - self.current_price
    
    def price_difference_percentage(self):
        """Return the price difference percentage"""
        if not self.original_price or not self.current_price or self.original_price == 0:
            return 0
        return (self.original_price - self.current_price) / self.original_price * 100
    
    def target_reached(self):
        """Check if the current price is at or below the target price"""
        if not self.current_price:
            return False
        return self.current_price <= self.target_price
    
    def needs_update(self):
        """Check if the product price needs to be updated (last check > 6 hours ago)"""
        if not self.last_checked:
            return True
        time_since_check = timezone.now() - self.last_checked
        return time_since_check.total_seconds() > 21600  # 6 hours in seconds

class PriceHistory(models.Model):
    product = models.ForeignKey(TrackedProduct, on_delete=models.CASCADE, related_name='price_history')
    price = models.FloatField()
    date_checked = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.product_name} - ${self.price} on {self.date_checked.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-date_checked']
        verbose_name_plural = 'Price histories'
