# ============================================================================
# FILE 6: reviews/admin.py
# ============================================================================
"""
Django admin configuration
"""
from django.contrib import admin
from .models import Product, Review, AspectAnalysis

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['asin', 'name', 'rating', 'total_reviews', 'overall_sentiment', 'status', 'created_at']
    list_filter = ['overall_sentiment', 'status', 'created_at']
    search_fields = ['asin', 'name']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'author', 'rating', 'sentiment', 'date', 'verified_purchase']
    list_filter = ['rating', 'sentiment', 'verified_purchase']
    search_fields = ['author', 'title', 'text']

@admin.register(AspectAnalysis)
class AspectAnalysisAdmin(admin.ModelAdmin):
    list_display = ['product', 'aspect_name', 'sentiment', 'confidence']
    list_filter = ['sentiment', 'aspect_name']
    search_fields = ['product__name', 'aspect_name']