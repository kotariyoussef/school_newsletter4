import requests
import json
import os
import random
from faker import Faker
from django.utils.text import slugify
from datetime import datetime

# Settings
API_URL = 'https://newsapi.org/v2/everything?sortBy=popularity&apiKey=0020da03e9b44fa1b8396f187c21fd2b&sources=bbc-news'
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
        "user": 1,
        "bio": fake.text(),
        "profile_picture": "",
        "slug": slugify(fake.name()),
        "created_at": str(datetime.now()),
        "updated_at": str(datetime.now())
    }
}
fixtures.append(profile)

# Category
category = {
    "model": "news.category",
    "pk": 1,
    "fields": {
        "name": "BBC News",
        "slug": "bbc-news",
        "description": "News from BBC"
    }
}
fixtures.append(category)

# Tags setup
tags_used = {"bbc", "news"}
tag_id_map = {}
tagged_items = []
tag_pk_start = 1
tagged_pk_start = 1000

# Tag fixtures
for tag_pk, tag_name in enumerate(tags_used, start=tag_pk_start):
    tag_id_map[tag_name] = tag_pk
    fixtures.append({
        "model": "taggit.tag",
        "pk": tag_pk,
        "fields": {
            "name": tag_name,
            "slug": slugify(tag_name)
        }
    })

# Helper to download and save image
def download_image(url, title):
    # Slugify the title to generate the image file name
    filename = f"{slugify(title)}.jpg"  # Assuming .jpg, can adjust if needed
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

# Fetch articles
news_data = requests.get(API_URL).json()
articles = news_data.get('articles', [])[:NEWS_LIMIT]

# News fixtures
for i, article in enumerate(articles, start=101):
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
            "category": 1,
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

    # TaggedItems for this news
    for tag_name in tags_used:
        tagged_items.append({
            "model": "taggit.taggeditem",
            "pk": tagged_pk_start,
            "fields": {
                "tag": tag_id_map[tag_name],
                "content_type": CONTENT_TYPE_ID,
                "object_id": i
            }
        })
        tagged_pk_start += 1

# Add tagged items at the end
fixtures.extend(tagged_items)

# Save fixture file
with open(FIXTURE_FILE, "w", encoding="utf-8") as f:
    json.dump(fixtures, f, indent=4)

print(f"✅ Generated {len(articles)} news articles and saved to {FIXTURE_FILE}")
