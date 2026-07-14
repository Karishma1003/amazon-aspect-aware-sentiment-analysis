# reviews/api_fetcher.py - FIXED WITH TOP REVIEWS FALLBACK

import requests
import re
import time
from django.conf import settings
from datetime import datetime

class RainforestFetcher:
    """Fetch Amazon reviews using Rainforest API with fallback to top_reviews"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or getattr(settings, 'RAINFOREST_API_KEY', None)
        
        if not self.api_key:
            raise Exception("Rainforest API key not found in settings")
        
        print(f"✓ Rainforest API initialized")
    
    def fetch_product_and_reviews(self, asin):
        """
        Fetch product info and reviews from Rainforest API
        Returns: (product_data, reviews_list)
        """
        print(f"\n🔍 Fetching data for ASIN: {asin}")
        
        # Get product details (includes top_reviews!)
        product_response = self._get_product_details_api(asin)
        
        if not product_response:
            raise Exception(f"Product not found for ASIN: {asin}")
        
        product_data = product_response['product_data']
        
        # Try to get reviews from dedicated endpoint first
        reviews = self._get_reviews_api(asin, max_pages=2)
        
        # If reviews endpoint fails, use top_reviews from product data
        if not reviews or len(reviews) == 0:
            print(f"  ⚠️ Reviews endpoint unavailable, using top_reviews from product data")
            reviews = product_response.get('top_reviews', [])
        
        if not reviews or len(reviews) == 0:
            raise Exception(f"No reviews found for ASIN: {asin}")
        
        print(f"✅ Successfully fetched {len(reviews)} reviews")
        return product_data, reviews
    
    def _get_product_details_api(self, asin):
        """Get product information from Rainforest API (includes top_reviews)"""
        url = "https://api.rainforestapi.com/request"
        
        params = {
            'api_key': self.api_key,
            'type': 'product',
            'amazon_domain': 'amazon.com',
            'asin': asin
        }
        
        try:
            print(f"  📦 Fetching product details...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'product' not in data:
                print(f"  ❌ Product not found in API response")
                return None
            
            product = data['product']
            title = product.get('title', f'Product {asin}')
            print(f"  ✅ Product: {title[:60]}...")
            
            product_data = {
                'name': title,
                'rating': float(product.get('rating', 0)),
                'total_reviews': int(product.get('ratings_total', 0)),
                'image_url': product.get('main_image', {}).get('link', ''),
                'asin': asin
            }
            
            # Extract top_reviews from product response
            top_reviews = []
            if 'top_reviews' in product and product['top_reviews']:
                print(f"  📋 Found {len(product['top_reviews'])} top reviews in product data")
                
                for review in product['top_reviews']:
                    # Parse date
                    date_obj = None
                    if 'date' in review and review['date']:
                        try:
                            date_str = review['date'].get('raw', '')
                            # Extract just the date part
                            if 'on' in date_str:
                                date_part = date_str.split('on')[-1].strip()
                                date_obj = datetime.strptime(date_part, '%B %d, %Y').date()
                        except:
                            pass
                    
                    top_reviews.append({
                        'title': review.get('title', 'No Title'),
                        'text': review.get('body', 'No Content'),
                        'rating': int(review.get('rating', 3)),
                        'author': review.get('profile', {}).get('name', 'Anonymous'),
                        'verified': review.get('verified_purchase', False),
                        'date': date_obj
                    })
            
            return {
                'product_data': product_data,
                'top_reviews': top_reviews
            }
        
        except requests.exceptions.RequestException as e:
            print(f"  ❌ API Request Error: {e}")
            raise Exception(f"Failed to fetch product: {e}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            raise
    
    def _get_reviews_api(self, asin, max_pages=2):
        """Get product reviews from dedicated reviews endpoint (with retry)"""
        url = "https://api.rainforestapi.com/request"
        all_reviews = []
        
        for page in range(1, max_pages + 1):
            params = {
                'api_key': self.api_key,
                'type': 'reviews',
                'amazon_domain': 'amazon.com',
                'asin': asin,
                'page': page
            }
            
            # Try up to 2 times per page
            for attempt in range(2):
                try:
                    print(f"  📄 Fetching reviews page {page} (attempt {attempt + 1})...")
                    response = requests.get(url, params=params, timeout=30)
                    
                    # Check for 503 or other errors
                    if response.status_code == 503:
                        print(f"  ⚠️ Reviews endpoint unavailable (503)")
                        return []  # Return empty to trigger fallback
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'reviews' in data and data['reviews']:
                        reviews = data['reviews']
                        
                        for review in reviews:
                            # Parse date
                            date_obj = None
                            if 'date' in review and review['date']:
                                try:
                                    date_str = review['date'].get('raw', '')
                                    if 'on' in date_str:
                                        date_part = date_str.split('on')[-1].strip()
                                        date_obj = datetime.strptime(date_part, '%B %d, %Y').date()
                                except:
                                    pass
                            
                            all_reviews.append({
                                'title': review.get('title', 'No Title'),
                                'text': review.get('body', 'No Content'),
                                'rating': int(review.get('rating', 3)),
                                'author': review.get('profile', {}).get('name', 'Anonymous'),
                                'verified': review.get('verified_purchase', False),
                                'date': date_obj
                            })
                        
                        print(f"  ✅ Got {len(reviews)} reviews (total: {len(all_reviews)})")
                        
                        # Success! Break retry loop
                        break
                    else:
                        print(f"  ⚠️ No reviews on page {page}")
                        return all_reviews  # Return what we have
                
                except requests.exceptions.RequestException as e:
                    print(f"  ⚠️ Reviews API error (attempt {attempt + 1}): {e}")
                    if attempt == 0:
                        time.sleep(2)  # Wait before retry
                        continue
                    else:
                        return []  # Failed both attempts, trigger fallback
                except Exception as e:
                    print(f"  ⚠️ Error on page {page}: {e}")
                    return all_reviews
        
        return all_reviews
    
    @staticmethod
    def extract_asin(url_or_asin):
        """Extract ASIN from URL or validate ASIN"""
        if not url_or_asin:
            return None
        
        # Clean input
        url_or_asin = url_or_asin.strip()
        
        # If already ASIN format (10 alphanumeric characters)
        if re.match(r'^[A-Z0-9]{10}$', url_or_asin, re.IGNORECASE):
            return url_or_asin.upper()
        
        # Extract from URL
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'asin=([A-Z0-9]{10})',
            r'/ASIN/([A-Z0-9]{10})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_asin, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        # Try to extract any 10-character alphanumeric code
        match = re.search(r'([A-Z0-9]{10})', url_or_asin, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        return None