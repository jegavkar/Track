from django.core.management.base import BaseCommand
from tracker.models import TrackedProduct
from tracker.services import update_product_price
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update current prices for all uncategorized Amazon tracked products'

    def handle(self, *args, **options):
        self.stdout.write('Starting update of uncategorized Amazon product prices...')

        # Get all uncategorized Amazon products
        uncategorized_products = TrackedProduct.objects.filter(category__isnull=True, product_url__icontains='amazon')

        if not uncategorized_products.exists():
            self.stdout.write(self.style.WARNING('No uncategorized products found.'))
            return

        total_products = uncategorized_products.count()
        self.stdout.write(f'Found {total_products} uncategorized products to update.')

        updated_count = 0
        error_count = 0

        for product in uncategorized_products:
            try:
                self.stdout.write(f'Updating price for: {product.product_name or product.product_url}')
                success = update_product_price(product)
                if success:
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Successfully updated: {product.product_name or "Unknown"}'))
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'Failed to update: {product.product_name or product.product_url}'))
            except Exception as e:
                error_count += 1
                logger.error(f'Error updating product {product.id}: {e}')
                self.stdout.write(self.style.ERROR(f'Exception updating {product.product_name or product.product_url}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Update completed. Updated: {updated_count}, Errors: {error_count}'))
