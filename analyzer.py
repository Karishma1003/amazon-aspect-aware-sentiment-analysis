# reviews/analyzer.py - FIXED VERSION

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from collections import defaultdict, Counter
import re

class ReviewAnalyzer:
    def __init__(self):
        print("Initializing RoBERTa model...")
        try:
            self.model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.eval()
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
        
        self.aspect_keywords = {
            'Quality': ['quality', 'build', 'material', 'durable', 'sturdy', 'solid', 'premium', 'cheap', 'flimsy', 'good', 'bad', 'excellent', 'poor'],
            'Price': ['price', 'cost', 'expensive', 'cheap', 'value', 'worth', 'money', 'affordable', 'overpriced', 'budget'],
            'Performance': ['performance', 'works', 'working', 'function', 'speed', 'fast', 'slow', 'efficient', 'effective'],
            'Design': ['design', 'look', 'appearance', 'style', 'color', 'size', 'compact', 'bulky', 'aesthetic', 'beautiful'],
            'Delivery': ['delivery', 'shipping', 'arrived', 'package', 'packaging', 'box', 'damaged', 'late', 'fast delivery'],
            'Customer Service': ['customer service', 'support', 'help', 'response', 'contact', 'seller', 'return'],
            'Ease of Use': ['easy', 'simple', 'complicated', 'difficult', 'intuitive', 'user-friendly', 'setup', 'install'],
            'Battery Life': ['battery', 'charge', 'charging', 'power', 'runtime', 'lasts', 'battery life'],
            'Features': ['feature', 'features', 'functionality', 'option', 'capability', 'function'],
            'Durability': ['last', 'lasting', 'broke', 'broken', 'stopped working', 'defective', 'reliable', 'durable']
        }
        
        self.sentiment_labels = ['Negative', 'Neutral', 'Positive']
    
    def analyze_sentiment(self, text):
        """Analyze sentiment using RoBERTa"""
        if not text or len(text.strip()) == 0:
            return {
                'sentiment': 'Neutral',
                'confidence': 0.33,
                'scores': [0.33, 0.34, 0.33]
            }
        
        try:
            # Truncate very long text
            text = text[:500]
            
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            confidence, predicted_class = torch.max(predictions, dim=1)
            sentiment = self.sentiment_labels[predicted_class.item()]
            confidence_score = confidence.item()
            
            return {
                'sentiment': sentiment,
                'confidence': confidence_score,
                'scores': predictions[0].tolist()
            }
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return {
                'sentiment': 'Neutral',
                'confidence': 0.33,
                'scores': [0.33, 0.34, 0.33]
            }
    
    def extract_aspects(self, text):
        """Extract product aspects mentioned"""
        text_lower = text.lower()
        mentioned_aspects = []
        
        for aspect, keywords in self.aspect_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    mentioned_aspects.append(aspect)
                    break
        
        return list(set(mentioned_aspects))
    
    def analyze_aspect_sentiment(self, text, aspect):
        """Analyze sentiment for specific aspect"""
        sentences = re.split(r'[.!?]+', text)
        aspect_sentences = []
        
        keywords = self.aspect_keywords.get(aspect, [])
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                aspect_sentences.append(sentence.strip())
        
        if not aspect_sentences:
            return None
        
        aspect_text = '. '.join(aspect_sentences)
        return self.analyze_sentiment(aspect_text)
    
    def analyze_reviews(self, review_objects):
        """Analyze all reviews and generate comprehensive report"""
        
        if not review_objects or len(review_objects) == 0:
            print("No reviews to analyze!")
            return {
                'overall_sentiment': 'Neutral',
                'overall_confidence': 0.5,
                'positive_percentage': 33.0,
                'negative_percentage': 33.0,
                'neutral_percentage': 34.0,
                'aspects': {},
                'total_reviews_analyzed': 0
            }
        
        print(f"Analyzing {len(review_objects)} reviews...")
        
        all_sentiments = []
        aspect_sentiments = defaultdict(list)
        
        for idx, review in enumerate(review_objects):
            try:
                print(f"Analyzing review {idx + 1}/{len(review_objects)}")
                
                # Combine title and text
                full_text = f"{review.title}. {review.text}"
                
                # Skip empty reviews
                if not full_text.strip() or full_text.strip() == ".":
                    continue
                
                # Overall sentiment
                sentiment_result = self.analyze_sentiment(full_text)
                all_sentiments.append(sentiment_result['sentiment'])
                
                # Update review model
                review.sentiment = sentiment_result['sentiment']
                review.sentiment_score = sentiment_result['confidence']
                review.save()
                
                # Extract and analyze aspects
                aspects = self.extract_aspects(full_text)
                
                for aspect in aspects:
                    aspect_sentiment = self.analyze_aspect_sentiment(full_text, aspect)
                    
                    if aspect_sentiment:
                        aspect_sentiments[aspect].append({
                            'sentiment': aspect_sentiment['sentiment'],
                            'confidence': aspect_sentiment['confidence'],
                            'review_text': full_text[:200] + '...' if len(full_text) > 200 else full_text,
                            'rating': review.rating
                        })
            
            except Exception as e:
                print(f"Error analyzing review {idx}: {e}")
                continue
        
        # Calculate overall statistics
        if not all_sentiments:
            return {
                'overall_sentiment': 'Neutral',
                'overall_confidence': 0.5,
                'positive_percentage': 33.0,
                'negative_percentage': 33.0,
                'neutral_percentage': 34.0,
                'aspects': {},
                'total_reviews_analyzed': 0
            }
        
        sentiment_counts = Counter(all_sentiments)
        total_reviews = len(all_sentiments)
        
        print(f"Sentiment counts: {dict(sentiment_counts)}")
        
        # Determine overall sentiment
        if sentiment_counts['Positive'] > sentiment_counts['Negative']:
            overall_sentiment = 'Positive'
        elif sentiment_counts['Negative'] > sentiment_counts['Positive']:
            overall_sentiment = 'Negative'
        else:
            overall_sentiment = 'Neutral'
        
        # Calculate percentages
        positive_pct = (sentiment_counts.get('Positive', 0) / total_reviews * 100) if total_reviews > 0 else 0
        negative_pct = (sentiment_counts.get('Negative', 0) / total_reviews * 100) if total_reviews > 0 else 0
        neutral_pct = (sentiment_counts.get('Neutral', 0) / total_reviews * 100) if total_reviews > 0 else 0
        
        # Process aspect analysis
        aspect_results = {}
        for aspect, sentiments in aspect_sentiments.items():
            if not sentiments:
                continue
                
            aspect_sentiment_counts = Counter([s['sentiment'] for s in sentiments])
            
            # Determine aspect sentiment
            if aspect_sentiment_counts['Positive'] > aspect_sentiment_counts['Negative']:
                aspect_sentiment = 'Positive'
            elif aspect_sentiment_counts['Negative'] > aspect_sentiment_counts['Positive']:
                aspect_sentiment = 'Negative'
            else:
                aspect_sentiment = 'Neutral'
            
            # Calculate average confidence
            avg_confidence = np.mean([s['confidence'] for s in sentiments])
            
            # Get sample reviews
            sample_reviews = sorted(sentiments, key=lambda x: x['confidence'], reverse=True)[:3]
            
            aspect_results[aspect] = {
                'sentiment': aspect_sentiment,
                'confidence': float(avg_confidence),
                'positive_count': aspect_sentiment_counts.get('Positive', 0),
                'negative_count': aspect_sentiment_counts.get('Negative', 0),
                'neutral_count': aspect_sentiment_counts.get('Neutral', 0),
                'sample_reviews': [
                    {
                        'text': s['review_text'],
                        'rating': s['rating'],
                        'sentiment': s['sentiment']
                    } for s in sample_reviews
                ]
            }
        
        print(f"Analysis complete: {overall_sentiment} ({total_reviews} reviews, {len(aspect_results)} aspects)")
        
        return {
            'overall_sentiment': overall_sentiment,
            'overall_confidence': max(positive_pct, negative_pct, neutral_pct) / 100,
            'positive_percentage': positive_pct,
            'negative_percentage': negative_pct,
            'neutral_percentage': neutral_pct,
            'aspects': aspect_results,
            'total_reviews_analyzed': total_reviews
        }