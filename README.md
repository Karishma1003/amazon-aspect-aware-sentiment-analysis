# Amazon Aspect-Aware Sentiment Analysis

## Overview

This project is a Django-based web application that performs aspect-aware sentiment analysis on Amazon product reviews using the RoBERTa transformer model. The application fetches reviews using the Rainforest API, analyzes sentiments for different aspects of a product, stores the results in a database, and presents them through an interactive web interface.

## Features

- Fetches Amazon product reviews using the Rainforest API.
- Performs aspect-aware sentiment analysis using the RoBERTa model.
- Analyzes sentiments across different product aspects.
- Stores products, reviews, and analysis results using Django ORM.
- Displays sentiment summaries and analysis results through a user-friendly web interface.
- Reuses previously analyzed products from the database to reduce unnecessary API calls.

## Technologies Used

- Python
- Django
- RoBERTa (Transformer Model)
- Rainforest API
- SQLite
- HTML
- CSS (Inline Styling)
