from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator

from .forms import UserRegistrationForm, TrackedProductForm
from .models import TrackedProduct, PriceHistory
from .services import update_product_price

def home(request):
    """Home page view with product tracking form for logged-in users"""
    if request.user.is_authenticated:
        form = TrackedProductForm()
        return render(request, 'tracker/home.html', {'form': form})
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
    """User dashboard showing tracked products"""
    user_products = TrackedProduct.objects.filter(user=request.user).order_by('-date_added')
    
    # Paginate results - 10 products per page
    paginator = Paginator(user_products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'tracker/dashboard.html', {'page_obj': page_obj})

@login_required
def track_product(request):
    """Add a new product to track"""
    if request.method == 'POST':
        form = TrackedProductForm(request.POST)
        if form.is_valid():
            # Create but don't save the product instance yet
            product = form.save(commit=False)
            product.user = request.user
            
            try:
                # Fetch initial product data
                update_product_price(product)
                messages.success(request, f"Successfully added {product.product_name} to your tracking list!")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error tracking product: {str(e)}")
                return render(request, 'tracker/home.html', {'form': form})
    else:
        form = TrackedProductForm()
    
    return render(request, 'tracker/home.html', {'form': form})

@login_required
def untrack_product(request, product_id):
    """Remove a product from tracking"""
    product = get_object_or_404(TrackedProduct, id=product_id, user=request.user)
    product_name = product.product_name
    product.delete()
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
        "current_price": 2495.17
    },
    {
        "name": "Samsung Galaxy S23",
        "discount": "25%",
        "original_price": 82999.17,
        "current_price": 62249.17
    },
    {
        "name": "Apple AirPods Pro",
        "discount": "20%",
        "original_price": 20749.17,
        "current_price": 16599.17
    },
    {
        "name": "Sony WH-1000XM4",
        "discount": "30%",
        "original_price": 29049.17,
        "current_price": 20334.17
    },
    {
        "name": "Nintendo Switch",
        "discount": "15%",
        "original_price": 24899.17,
        "current_price": 21164.17
    }
]
    
    return render(request, 'tracker/top_offers.html', {'offers': offers})
