from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import TrackedProduct, ProductCategory

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        
    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class TrackedProductForm(forms.ModelForm):
    class Meta:
        model = TrackedProduct
        fields = ('product_url', 'target_price', 'category')
        widgets = {
            'product_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.amazon.com/product-url'}),
            'target_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '999'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'product_url': 'Product URL',
            'target_price': 'Target Price',
            'category': 'Product Category',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = ProductCategory.objects.filter(user=user)
        else:
            self.fields['category'].queryset = ProductCategory.objects.none()

    def clean_target_price(self):
        target_price = self.cleaned_data.get('target_price')
        if target_price <= 0:
            raise forms.ValidationError("Target price must be greater than zero.")
        return target_price

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Electronics'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description'}),
        }
        labels = {
            'name': 'Category Name',
            'description': 'Description',
        }
