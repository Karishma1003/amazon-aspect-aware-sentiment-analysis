# Amazon Review Sentiment Analysis

> A Django web application that performs aspect-aware sentiment analysis on Amazon product reviews using the RoBERTa transformer model.

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

## Project Workflow

1. User enters an Amazon Product ASIN or Product URL.
2. The application validates the input.
3. Product information and reviews are fetched using the Rainforest API.
4. Reviews are preprocessed.
5. The RoBERTa model analyzes each review and predicts its sentiment.
6. Aspect-wise sentiment analysis is performed.
7. Results are stored in the database.
8. Overall sentiment statistics and aspect analysis are displayed through the Django web interface.


## Screenshots

### Home Page

![Home Page](screenshots/Home%20page.png)

### Results Page

![Results Page](screenshots/Result%20Page%201.png)

![Results Page 2](screenshots/Result%20Page%202.png)

![Results Page 3](screenshots/Result%20Page%203.png)

### All Reviews

![All Reviews](screenshots/All%20reviews.png)


## Project Structure

```
amazon-aspect-aware-sentiment-analysis/
│
├── analysis/
│   ├── analyzer.py
│   ├── api_fetcher.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── templates/
│   └── migrations/
│
├── amazon_project/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── screenshots/
├── manage.py
├── requirements.txt
└── README.md
```

## Future Enhancements

- Improve aspect extraction accuracy.
- Add graphical dashboards for sentiment visualization.
- Export analysis reports.
- Support multiple e-commerce platforms.
- Add user authentication and analysis history.


## Author

**Karishma Bargaje**

Information Technology Graduate

GitHub: https://github.com/Karishma1003

LinkedIn: https://www.linkedin.com/in/karishma-b-120155294


## License

This project was developed for educational and academic purposes.
