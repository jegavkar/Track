from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator

from .forms import UserRegistrationForm, TrackedProductForm, ProductCategoryForm
from .models import TrackedProduct, PriceHistory, ProductCategory
from .services import update_product_price

def home(request):
    """Home page view with product tracking form for logged-in users"""
    if request.user.is_authenticated:
        product_form = TrackedProductForm(user=request.user)
        category_form = ProductCategoryForm()
        return render(request, 'tracker/home.html', {'form': product_form, 'category_form': category_form})
    return render(request, 'tracker/home.html')

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'tracker/register.html', {'form': form})

@login_required
def dashboard(request):
    """User dashboard showing currently tracked products grouped by categories"""
    user_products = TrackedProduct.objects.filter(user=request.user, is_active=True).select_related('category').prefetch_related('price_history').order_by('-date_added')

    # Group products by category
    categories = {}
    uncategorized = []

    for product in user_products:
        if product.category:
            if product.category.name not in categories:
                categories[product.category.name] = {
                    'category': product.category,
                    'products': []
                }
            categories[product.category.name]['products'].append(product)
        else:
            uncategorized.append(product)

    # Convert to list for template
    category_list = list(categories.values())

    return render(request, 'tracker/dashboard.html', {
        'category_list': category_list,
        'uncategorized': uncategorized,
        'user_products': user_products
    })

@login_required
def track_product(request):
    """Add a new product to track"""
    if request.method == 'POST':
        form = TrackedProductForm(request.POST, user=request.user)
        if form.is_valid():
            # Create but don't save the product instance yet
            product = form.save(commit=False)
            product.user = request.user
            product.save()  # Save the product first

            # Try to fetch initial product data
            if update_product_price(product):
                messages.success(request, f"Successfully added {product.product_name} to your tracking list!")
            else:
                messages.warning(request, f"Added product to tracking list, but could not fetch current price. It will be updated automatically later.")

            return redirect('dashboard')
    else:
        form = TrackedProductForm(user=request.user)

    return render(request, 'tracker/home.html', {'form': form, 'category_form': ProductCategoryForm()})

@login_required
def track_category(request):
    """Create a new product category"""
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, f"Successfully created category '{category.name}'!")
            return redirect('home')
    else:
        form = ProductCategoryForm()

    return render(request, 'tracker/home.html', {'form': TrackedProductForm(user=request.user), 'category_form': form})

@login_required
def untrack_product(request, product_id):
    """Mark a product as inactive instead of deleting"""
    product = get_object_or_404(TrackedProduct, id=product_id, user=request.user)
    product_name = product.product_name
    product.is_active = False
    product.save()
    messages.success(request, f"{product_name} has been removed from your tracking list.")
    return redirect('dashboard')

@login_required
def check_price(request, product_id):
    """Manually check price for a product"""
    product = get_object_or_404(TrackedProduct, id=product_id, user=request.user)
    
    try:
        update_product_price(product)
        messages.success(request, f"Price updated for {product.product_name}")
    except Exception as e:
        messages.error(request, f"Error updating price: {str(e)}")
    
    return redirect('dashboard')

@login_required
def product_details(request, product_id):
    """View product details and price history"""
    product = get_object_or_404(TrackedProduct, id=product_id, user=request.user)
    price_history = product.price_history.all()

    return render(request, 'tracker/product_details.html', {
        'product': product,
        'price_history': price_history
    })

@login_required
def product_history(request):
    """View all tracked products history - currently tracking and previously tracked"""
    # Currently tracking products (active)
    active_products = TrackedProduct.objects.filter(user=request.user, is_active=True).select_related('category').prefetch_related('price_history').order_by('-date_added')

    # Previously tracked products (inactive)
    inactive_products = TrackedProduct.objects.filter(user=request.user, is_active=False).select_related('category').prefetch_related('price_history').order_by('-date_added')

    # Group active products by category
    active_categories = {}
    active_uncategorized = []
    for product in active_products:
        if product.category:
            if product.category.name not in active_categories:
                active_categories[product.category.name] = {
                    'category': product.category,
                    'products': []
                }
            active_categories[product.category.name]['products'].append(product)
        else:
            active_uncategorized.append(product)

    # Group inactive products by category
    inactive_categories = {}
    inactive_uncategorized = []
    for product in inactive_products:
        if product.category:
            if product.category.name not in inactive_categories:
                inactive_categories[product.category.name] = {
                    'category': product.category,
                    'products': []
                }
            inactive_categories[product.category.name]['products'].append(product)
        else:
            inactive_uncategorized.append(product)

    return render(request, 'tracker/product_history.html', {
        'active_categories': list(active_categories.values()),
        'active_uncategorized': active_uncategorized,
        'inactive_categories': list(inactive_categories.values()),
        'inactive_uncategorized': inactive_uncategorized,
    })

def top_categories(request):
    """View top product categories"""
    # In a real-world scenario, this would be dynamic data from a database
    # For this example, we'll use static categories
    categories = [
        {'name': 'Electronics', 'popular_items': ['Smartphones', 'Laptops', 'Headphones']},
        {'name': 'Home & Kitchen', 'popular_items': ['Appliances', 'Cookware', 'Furniture']},
        {'name': 'Clothing', 'popular_items': ['Men\'s Fashion', 'Women\'s Fashion', 'Kids']},
        {'name': 'Books', 'popular_items': ['Fiction', 'Non-fiction', 'Education']},
        {'name': 'Beauty & Personal Care', 'popular_items': ['Skincare', 'Makeup', 'Haircare']}
    ]
    
    return render(request, 'tracker/top_categories.html', {'categories': categories})

def top_offers(request):
    """View top current offers"""
    # In a real-world scenario, this would be dynamic data from a database or API
    # For this example, we'll use static offers
    offers = [
    {
        "name": "Amazon Echo Dot",
        "discount": "40%",
        "original_price": 4159.17,
        "current_price": 2495.17,
        "savings": 4159.17 - 2495.17
    },
    {
        "name": "Samsung Galaxy S23",
        "discount": "25%",
        "original_price": 82999.17,
        "current_price": 62249.17,
        "savings": 82999.17 - 62249.17
    },
    {
        "name": "Apple AirPods Pro",
        "discount": "20%",
        "original_price": 20749.17,
        "current_price": 16599.17,
        "savings": 20749.17 - 16599.17
    },
    {
        "name": "Sony WH-1000XM4",
        "discount": "30%",
        "original_price": 29049.17,
        "current_price": 20334.17,
        "savings": 29049.17 - 20334.17
    },
    {
        "name": "Nintendo Switch",
        "discount": "15%",
        "original_price": 24899.17,
        "current_price": 21164.17,
        "savings": 24899.17 - 21164.17
    }
]

    return render(request, 'tracker/top_offers.html', {'offers': offers})

import logging
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from .scraper import search_amazon_category

logger = logging.getLogger(__name__)

@require_GET
def browse_category(request, category):
    """
    API endpoint to browse products from Amazon by category.
    """
    try:
        logger.info(f"Browsing category: {category}")
        products = search_amazon_category(category)
        logger.info(f"Found {len(products)} products for category {category}")
        return JsonResponse({'products': products})
    except Exception as e:
        logger.error(f"Error browsing category {category}: {str(e)}")
        return JsonResponse({'error': 'Failed to fetch products', 'details': str(e)}, status=500)
