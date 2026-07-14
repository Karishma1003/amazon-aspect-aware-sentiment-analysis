# ============================================================================
# FILE 1: reviews/models.py
# ============================================================================
"""
Database models for storing products, reviews, and aspect analysis
"""
from django.db import models
from django.utils import timezone

class Product(models.Model):
    """Model to store Amazon product information"""
    asin = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=500)
    image_url = models.URLField(max_length=1000, blank=True)
    rating = models.FloatField(default=0)
    total_reviews = models.IntegerField(default=0)
    
    # Analysis results
    overall_sentiment = models.CharField(max_length=20, blank=True)
    sentiment_confidence = models.FloatField(default=0)
    positive_percentage = models.FloatField(default=0)
    negative_percentage = models.FloatField(default=0)
    neutral_percentage = models.FloatField(default=0)
    
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.asin} - {self.name}"

class Review(models.Model):
    """Model to store individual reviews"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    review_id = models.CharField(max_length=50, unique=True)
    author = models.CharField(max_length=200)
    rating = models.IntegerField()
    title = models.CharField(max_length=500)
    text = models.TextField()
    date = models.DateField(null=True, blank=True)
    verified_purchase = models.BooleanField(default=False)
    
    # Sentiment analysis results
    sentiment = models.CharField(max_length=20, blank=True)
    sentiment_score = models.FloatField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews'
        ordering = ['-date', '-rating']
        indexes = [
            models.Index(fields=['product', 'rating']),
            models.Index(fields=['sentiment']),
        ]
    
    def __str__(self):
        return f"{self.product.asin} - {self.author} - {self.rating}★"

class AspectAnalysis(models.Model):
    """Model to store aspect-based sentiment analysis"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='aspects')
    aspect_name = models.CharField(max_length=100)
    sentiment = models.CharField(max_length=20)
    confidence = models.FloatField(default=0)
    
    positive_count = models.IntegerField(default=0)
    negative_count = models.IntegerField(default=0)
    neutral_count = models.IntegerField(default=0)
    
    sample_reviews = models.TextField(default='[]')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'aspect_analysis'
        unique_together = ['product', 'aspect_name']
        ordering = ['-confidence']
    
    def __str__(self):
        return f"{self.product.asin} - {self.aspect_name} - {self.sentiment}"