from django.contrib import admin
from .models import TrackedProduct, PriceHistory

class PriceHistoryInline(admin.TabularInline):
    model = PriceHistory
    extra = 0
    readonly_fields = ('price', 'date_checked')
    can_delete = False

class TrackedProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'user', 'current_price', 'target_price', 'last_checked')
    list_filter = ('user', 'last_checked')
    search_fields = ('product_name', 'product_url', 'user__username')
    inlines = [PriceHistoryInline]

admin.site.register(TrackedProduct, TrackedProductAdmin)
admin.site.register(PriceHistory)
