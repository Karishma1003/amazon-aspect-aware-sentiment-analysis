# reviews/views.py - FIXED VERSION WITH ACCURATE ANALYSIS

from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Product, Review, AspectAnalysis
from .api_fetcher import RainforestFetcher
from .analyzer import ReviewAnalyzer  # Import the RoBERTa analyzer
import json
import traceback

def index(request):
    """Home page with ASIN input"""
    return render(request, 'reviews/index.html')

def analyze_product(request):
    """Analyze product using Rainforest API + RoBERTa sentiment analysis"""
    if request.method == 'POST':
        user_input = request.POST.get('asin', '') or request.POST.get('url', '')
        user_input = user_input.strip()
        
        if not user_input:
            return render(request, 'reviews/error.html', {
                'error': 'Please provide ASIN or URL'
            })
        
        try:
            # Initialize API fetcher and analyzer
            api_fetcher = RainforestFetcher()
            analyzer = ReviewAnalyzer()  # Use RoBERTa model
            
            # Extract ASIN
            asin = api_fetcher.extract_asin(user_input)
            
            if not asin:
                return render(request, 'reviews/error.html', {
                    'error': f'Invalid ASIN or URL: {user_input}'
                })
            
            print(f"\n{'='*60}")
            print(f"ANALYZING ASIN: {asin}")
            print(f"{'='*60}\n")
            
            # Check if already analyzed recently
            try:
                existing = Product.objects.get(asin=asin)
                if existing.status == 'completed':
                    print(f"✓ Product already analyzed, showing cached results")
                    return redirect('review_results', asin=asin)
            except Product.DoesNotExist:
                pass
            
            # Create product with pending status
            product, _ = Product.objects.update_or_create(
                asin=asin,
                defaults={
                    'name': f'Loading Product {asin}...',
                    'status': 'processing'
                }
            )
            
            # Fetch from Rainforest API
            print(f"📡 Fetching from Rainforest API...")
            product_data, reviews_list = api_fetcher.fetch_product_and_reviews(asin)
            
            if not reviews_list or len(reviews_list) == 0:
                product.status = 'failed'
                product.save()
                return render(request, 'reviews/error.html', {
                    'error': f'No reviews found for ASIN: {asin}. Product may not exist or have no reviews.'
                })
            
            print(f"✓ Found {len(reviews_list)} reviews")
            
            # Save reviews to database first
            print(f"\n💾 Saving reviews to database...")
            review_objects = []
            for idx, review_data in enumerate(reviews_list[:100]):  # Limit to 100 reviews
                try:
                    review_obj, created = Review.objects.update_or_create(
                        product=product,
                        review_id=f"{asin}_{idx}",
                        defaults={
                            'author': review_data.get('author', 'Anonymous')[:200],
                            'rating': review_data.get('rating', 3),
                            'title': review_data.get('title', '')[:500],
                            'text': review_data.get('text', '')[:5000],
                            'verified_purchase': review_data.get('verified', False),
                            'date': review_data.get('date'),
                        }
                    )
                    review_objects.append(review_obj)
                except Exception as e:
                    print(f"Error saving review {idx}: {e}")
                    continue
            
            print(f"✓ Saved {len(review_objects)} reviews")
            
            # Perform sentiment analysis using RoBERTa
            print(f"\n🤖 Running RoBERTa sentiment analysis...")
            analysis_results = analyzer.analyze_reviews(review_objects)
            
            # Update product with results
            print(f"\n💾 Saving analysis results...")
            product.name = product_data['name'][:500]
            product.image_url = product_data.get('image_url', '')
            product.rating = product_data.get('rating', 0)
            product.total_reviews = analysis_results.get('total_reviews_analyzed', len(review_objects))
            product.overall_sentiment = analysis_results.get('overall_sentiment', 'Neutral')
            product.sentiment_confidence = analysis_results.get('overall_confidence', 0.5)
            product.positive_percentage = analysis_results.get('positive_percentage', 0)
            product.negative_percentage = analysis_results.get('negative_percentage', 0)
            product.neutral_percentage = analysis_results.get('neutral_percentage', 0)
            product.status = 'completed'
            product.save()
            
            # Save aspect analysis
            if 'aspects' in analysis_results:
                for aspect_name, aspect_data in analysis_results['aspects'].items():
                    try:
                        AspectAnalysis.objects.update_or_create(
                            product=product,
                            aspect_name=aspect_name,
                            defaults={
                                'sentiment': aspect_data.get('sentiment', 'Neutral'),
                                'confidence': aspect_data.get('confidence', 0.5),
                                'positive_count': aspect_data.get('positive_count', 0),
                                'negative_count': aspect_data.get('negative_count', 0),
                                'neutral_count': aspect_data.get('neutral_count', 0),
                                'sample_reviews': json.dumps(aspect_data.get('sample_reviews', []))
                            }
                        )
                    except Exception as e:
                        print(f"Error saving aspect {aspect_name}: {e}")
            
            print(f"\n{'='*60}")
            print(f"✅ ANALYSIS COMPLETE!")
            print(f"Overall: {product.overall_sentiment}")
            print(f"Confidence: {product.sentiment_confidence:.2f}")
            print(f"Positive: {product.positive_percentage:.1f}%")
            print(f"Negative: {product.negative_percentage:.1f}%")
            print(f"Neutral: {product.neutral_percentage:.1f}%")
            print(f"{'='*60}\n")
            
            return redirect('review_results', asin=asin)
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}\n")
            traceback.print_exc()
            
            # Update product status
            try:
                product = Product.objects.get(asin=asin)
                product.status = 'failed'
                product.save()
            except:
                pass
            
            return render(request, 'reviews/error.html', {
                'error': f'Analysis failed: {str(e)[:200]}'
            })
    
    return redirect('index')

def review_results(request, asin):
    """Display analysis results"""
    try:
        product = Product.objects.get(asin=asin)
        
        if product.status != 'completed':
            return render(request, 'reviews/processing.html', {
                'asin': asin,
                'product': product
            })
        
        # Get aspects
        aspects = AspectAnalysis.objects.filter(product=product).order_by('-confidence')
        
        aspect_data = []
        for aspect in aspects:
            try:
                sample_reviews = json.loads(aspect.sample_reviews) if aspect.sample_reviews else []
            except:
                sample_reviews = []
            
            aspect_data.append({
                'name': aspect.aspect_name,
                'sentiment': aspect.sentiment,
                'confidence': float(aspect.confidence) * 100,
                'positive_count': aspect.positive_count,
                'negative_count': aspect.negative_count,
                'neutral_count': aspect.neutral_count,
                'sample_reviews': sample_reviews[:3]  # Limit to 3 samples
            })
        
        # Determine sentiment class for styling
        sentiment_class = 'neutral'
        if product.overall_sentiment == 'Positive':
            sentiment_class = 'good'
        elif product.overall_sentiment == 'Negative':
            sentiment_class = 'poor'
        
        context = {
            'product': product,
            'aspects': aspect_data,
            'overall_sentiment': product.overall_sentiment,
            'sentiment_class': sentiment_class,
            'positive_percentage': product.positive_percentage,
            'negative_percentage': product.negative_percentage,
            'neutral_percentage': product.neutral_percentage,
            'rating': product.rating
        }
        
        return render(request, 'reviews/results.html', context)
        
    except Product.DoesNotExist:
        return render(request, 'reviews/error.html', {
            'error': f'Product with ASIN {asin} not found. Please analyze it first.'
        })

def full_reviews(request, asin):
    """Display all reviews"""
    try:
        product = Product.objects.get(asin=asin)
        reviews = Review.objects.filter(product=product).order_by('-rating', '-date')[:100]
        
        context = {
            'product': product,
            'reviews': reviews
        }
        
        return render(request, 'reviews/full_reviews.html', context)
        
    except Product.DoesNotExist:
        return render(request, 'reviews/error.html', {
            'error': 'Product not found'
        })

def upload_csv(request):
    """Handle CSV upload - Not implemented"""
    return render(request, 'reviews/error.html', {
        'error': 'CSV upload feature is not available. Please use ASIN or URL instead.'
    })

def check_status(request, asin):
    """Check analysis status (AJAX endpoint)"""
    try:
        product = Product.objects.get(asin=asin)
        return JsonResponse({
            'status': product.status,
            'redirect_url': f'/results/{asin}/' if product.status == 'completed' else None
        })
    except Product.DoesNotExist:
        return JsonResponse({'status': 'not_found'})

def test_scraper(request):
    """Test API functionality"""
    asin = request.GET.get('asin', 'B073JYC4XM')
    try:
        api_fetcher = RainforestFetcher()
        product_data, reviews = api_fetcher.fetch_product_and_reviews(asin)
        
        return JsonResponse({
            'status': 'success',
            'product_name': product_data['name'],
            'reviews_count': len(reviews),
            'sample_review': reviews[0] if reviews else None
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

def quick_test(request):
    """Quick test endpoint - redirects to home"""
    return redirect('index')

def quick_test_with_asin(request, asin):
    """Quick test with ASIN - redirects to analyze"""
    return redirect('analyze_product')

def test_api_directly(request):
    """Test Rainforest API directly"""
    import requests
    
    asin = request.GET.get('asin', 'B073JYC4XM')
    api_key = 'CC91926244584FCCAAA71ADA6960AE42'
    
    try:
        # Test product endpoint
        product_params = {
            'api_key': api_key,
            'amazon_domain': 'amazon.in',
            'asin': asin,
            'type': 'product'
        }
        product_response = requests.get('https://api.rainforestapi.com/request', params=product_params, timeout=30)
        product_data = product_response.json()
        
        # Test reviews endpoint
        reviews_params = {
            'api_key': api_key,
            'amazon_domain': 'amazon.in',
            'asin': asin,
            'type': 'reviews'
        }
        reviews_response = requests.get('https://api.rainforestapi.com/request', params=reviews_params, timeout=30)
        reviews_data = reviews_response.json()
        
        return JsonResponse({
            'success': True,
            'product_status': product_response.status_code,
            'product_found': 'product' in product_data,
            'product_title': product_data.get('product', {}).get('title', 'N/A'),
            'product_rating': product_data.get('product', {}).get('rating', 0),
            'reviews_status': reviews_response.status_code,
            'reviews_count': len(reviews_data.get('reviews', [])),
            'sample_review': reviews_data.get('reviews', [{}])[0] if reviews_data.get('reviews') else None
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })