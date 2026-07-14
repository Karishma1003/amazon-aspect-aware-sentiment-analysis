# ============================================================================
# FILE 5: reviews/urls.py
# ============================================================================
"""
URL routing configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('analyze/', views.analyze_product, name='analyze_product'),
    path('upload/', views.upload_csv, name='upload_csv'),
    path('results/<str:asin>/', views.review_results, name='review_results'),
    path('reviews/<str:asin>/', views.full_reviews, name='full_reviews'),  # Add this line
    path('check-status/<str:asin>/', views.check_status, name='check_status'),
    path('test-scraper/', views.test_scraper, name='test_scraper'),
    path('quick-test/', views.quick_test, name='quick_test'),
    path('demo-analyze/<str:asin>/', views.quick_test_with_asin, name='quick_test_with_asin'),
    path('test-api/', views.test_api_directly, name='test_api'),
]