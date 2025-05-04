import requests
import json
import os
import random
from faker import Faker
from django.utils.text import slugify
from datetime import datetime

# Settings
API_KEY = '0020da03e9b44fa1b8396f187c21fd2b'
SOURCES = ['bbc-news', 'cnn', 'al-jazeera-english', 'argaam', 'ars-technica', 'bloomberg']  # List of source IDs
MEDIA_DIR = 'media/news/images/'
FIXTURE_FILE = 'fixtures.json'
NEWS_LIMIT = 100
CONTENT_TYPE_ID = 13  # CHANGE THIS to your actual ContentType ID for News

# Init
os.makedirs(MEDIA_DIR, exist_ok=True)
fake = Faker()
fixtures = []

profile = {
    "model": "accounts.studentprofile",
    "pk": 1,
    "fields": {
        "user": 2,
        "bio": fake.text(),
        "profile_picture": "",
        "slug": slugify(fake.name()),
        "created_at": str(datetime.now()),
        "updated_at": str(datetime.now())
    }
}
fixtures.append(profile)

# Helper to download and save image
def download_image(url, title):
    filename = f"{slugify(title)}.jpg"
    filepath = os.path.join(MEDIA_DIR, filename)
    
    # Check if the image already exists
    if os.path.exists(filepath):
        print(f"✅ Image for '{title}' already exists. Skipping download.")
        return f"news/images/{filename}"
    
    try:
        # If the image doesn't exist, download it
        response = requests.get(url, stream=True, timeout=5)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"✅ Downloaded image for '{title}'")
            return f"news/images/{filename}"
    except Exception as e:
        print(f"❌ Failed to download image for '{title}': {e}")
    
    return ""  # Return empty string if image download fails

generated_slugs = set()

# Helper to ensure unique slug
def generate_unique_slug(base_slug):
    slug = base_slug
    counter = 1
    while slug in generated_slugs:  # Check if the slug is already in the generated set
        slug = f"{base_slug}-{counter}"
        counter += 1
    generated_slugs.add(slug)  # Add the generated slug to the set
    return slug

st = 1

# Loop through each source
for source in SOURCES:
    API_URL = f'https://newsapi.org/v2/everything?sortBy=popularity&apiKey={API_KEY}&sources={source}'
    news_data = requests.get(API_URL).json()
    articles = news_data.get('articles', [])[:NEWS_LIMIT]
    
    # Create a category for each source
    category_name = source.replace('-', ' ').title()  # Example: 'bbc-news' becomes 'BBC News'
    category_slug = slugify(category_name)
    category_description = f"News from {category_name}"
    
    category = {
        "model": "news.category",
        "pk": SOURCES.index(source) + 1,
        "fields": {
            "name": category_name,
            "slug": category_slug,
            "description": category_description
        }
    }
    fixtures.append(category)

    # News fixtures for each source
    for i, article in enumerate(articles, start=st):
        title = article['title']
        slug = generate_unique_slug(slugify(title))
        image_path = download_image(article.get('urlToImage'), title) if article.get('urlToImage') else ""

        news = {
            "model": "news.news",
            "pk": i,
            "fields": {
                "title": title,
                "slug": slug,
                "author": 1,
                "category": SOURCES.index(source) + 1,  # Assign the source's category to the article
                "featured_image": image_path,
                "summary": article.get('description') or "",
                "content": article.get('content') or "",
                "is_featured": random.choice([True, False]),
                "status": "published",
                "created_at": str(datetime.now()),
                "updated_at": str(datetime.now()),
                "publish_date": article.get('publishedAt'),
                "views": random.randint(0, 500)
            }
        }
        fixtures.append(news)
    st = st + 100

# Save fixture file
with open(FIXTURE_FILE, "w", encoding="utf-8") as f:
    json.dump(fixtures, f, indent=4)

print(f"✅ Generated news articles with categories for each source and saved to {FIXTURE_FILE}")
