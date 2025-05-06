import requests
import json
import os
import random
from faker import Faker
from django.utils.text import slugify
from datetime import datetime, timedelta
import pytz

# Settings
API_KEY = '0020da03e9b44fa1b8396f187c21fd2b'
SOURCES = ['bbc-news', 'cnn', 'al-jazeera-english', 'bloomberg', 'ars-technica', 'the-verge', 'wired']
MEDIA_DIR = 'media/news/images/'
FIXTURE_FILE = 'fixtures/news_fixtures.json'
STUDENT_PROFILES_FIXTURE = 'fixtures/student_profiles.json'
NEWS_LIMIT = 100  # Number of articles per source

# Create necessary directories
os.makedirs(MEDIA_DIR, exist_ok=True)

# Initialize faker
fake = Faker()
fixtures = []

# Load student profiles from fixture file
student_profiles = []
try:
    with open(STUDENT_PROFILES_FIXTURE, 'r', encoding='utf-8') as f:
        student_profiles_data = json.load(f)
        for profile in student_profiles_data:
            if profile['model'] == 'accounts.studentprofile':
                student_profiles.append(profile['pk'])
    
    if student_profiles:
        print(f"✅ Loaded {len(student_profiles)} student profiles from {STUDENT_PROFILES_FIXTURE}")
    else:
        print(f"❌ No student profiles found in {STUDENT_PROFILES_FIXTURE}")
        # Create some dummy profile IDs as fallback
        student_profiles = list(range(1, 11))
except FileNotFoundError:
    print(f"❌ Student profiles fixture file not found: {STUDENT_PROFILES_FIXTURE}")
    # Create some dummy profile IDs as fallback
    student_profiles = list(range(1, 11))
except json.JSONDecodeError:
    print(f"❌ Invalid JSON format in student profiles fixture: {STUDENT_PROFILES_FIXTURE}")
    # Create some dummy profile IDs as fallback
    student_profiles = list(range(1, 11))
except Exception as e:
    print(f"❌ Error loading student profiles: {e}")
    # Create some dummy profile IDs as fallback
    student_profiles = list(range(1, 11))

# List of potential tags for news articles
TAGS = [
    'technology', 'politics', 'business', 'climate', 'sports', 'entertainment',
    'science', 'health', 'education', 'world', 'local', 'economy', 'innovation',
    'research', 'ai', 'machine learning', 'blockchain', 'cybersecurity', 'space',
    'environment', 'sustainability', 'finance', 'startups', 'digital', 'crypto'
]

# Initialize primary key counters
category_pk = 1
news_pk = 1
comment_pk = 1
tag_pk = 1
tagged_item_pk = 1

# Helper to download and save image
def download_image(url, title):
    if not url:
        return ""
        
    filename = f"{slugify(title)[:50]}.jpg"
    filepath = os.path.join(MEDIA_DIR, filename)
    
    # Check if the image already exists
    if os.path.exists(filepath):
        print(f"✅ Image for '{title[:30]}...' already exists. Skipping download.")
        return f"news/images/{filename}"
    
    try:
        # If the image doesn't exist, download it
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"✅ Downloaded image for '{title[:30]}...'")
            return f"news/images/{filename}"
    except Exception as e:
        print(f"❌ Failed to download image for '{title[:30]}...': {e}")
    
    return ""  # Return empty string if image download fails

# Helper to ensure unique slug
generated_slugs = set()
def generate_unique_slug(base_slug):
    if not base_slug:
        base_slug = 'news-article'
    
    # Truncate slug to reasonable length
    base_slug = base_slug[:100]
    
    slug = base_slug
    counter = 1
    while slug in generated_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1
    generated_slugs.add(slug)
    return slug

# Helper to generate HTML content from plain text
def generate_html_content(text, title):
    if not text:
        paragraphs = [fake.paragraph(nb_sentences=random.randint(5, 10)) for _ in range(random.randint(4, 8))]
        text = "\n\n".join(paragraphs)
    
    # Convert plain text to HTML with headers, paragraphs, etc.
    html_content = f"<h1>{title}</h1>\n"
    
    # Add a subtitle/lead paragraph
    html_content += f"<p class='lead'>{fake.paragraph()}</p>\n"
    
    # Add content paragraphs with formatting
    paragraphs = text.split('\n')
    for i, paragraph in enumerate(paragraphs):
        if paragraph.strip():
            # Occasionally add subheadings
            if i > 0 and random.random() < 0.3:
                html_content += f"<h2>{fake.sentence().rstrip('.')}</h2>\n"
            
            # Add paragraph with some formatting
            if random.random() < 0.1:
                # Add formatting to some text
                words = paragraph.split()
                if len(words) > 3:
                    random_pos = random.randint(0, len(words) - 3)
                    words[random_pos] = f"<strong>{words[random_pos]}</strong>"
                paragraph = " ".join(words)
            
            html_content += f"<p>{paragraph}</p>\n"
    
    # Occasionally add blockquote
    if random.random() < 0.4:
        html_content += f"<blockquote><p>{fake.sentence()}</p></blockquote>\n"
    
    # Add final paragraph
    html_content += f"<p>{fake.paragraph()}</p>\n"
    
    return html_content

# Create categories for each source
for source in SOURCES:
    category_name = source.replace('-', ' ').title()
    category_slug = slugify(category_name)
    category_description = f"News from {category_name}"
    
    category = {
        "model": "news.category",
        "pk": category_pk,
        "fields": {
            "name": category_name,
            "slug": category_slug,
            "description": category_description
        }
    }
    fixtures.append(category)
    category_pk += 1

# Generate news articles
for source_idx, source in enumerate(SOURCES):
    API_URL = f'https://newsapi.org/v2/everything?sortBy=popularity&apiKey={API_KEY}&sources={source}'
    
    try:
        response = requests.get(API_URL, timeout=15)
        news_data = response.json()
        
        if news_data.get('status') != 'ok':
            print(f"❌ Error fetching news from {source}: {news_data.get('message', 'Unknown error')}")
            continue
            
        articles = news_data.get('articles', [])[:NEWS_LIMIT]
        
        if not articles:
            print(f"ℹ️ No articles found for source: {source}")
            continue
            
        print(f"✅ Fetched {len(articles)} articles from {source}")
        
        # Process each article
        for article in articles:
            title = article.get('title', f"News from {source}")
            # Truncate title if too long
            if title and len(title) > 190:
                title = title[:190] + "..."
                
            slug = generate_unique_slug(slugify(title))
            image_path = download_image(article.get('urlToImage'), title)
            
            # Generate publish date within the last 30 days
            publish_date = datetime.now(pytz.UTC) - timedelta(days=random.randint(0, 30), 
                                                            hours=random.randint(0, 23), 
                                                            minutes=random.randint(0, 59))
            
            # Create news article
            news_article = {
                "model": "news.news",
                "pk": news_pk,
                "fields": {
                    "title": title,
                    "slug": slug,
                    "author": random.choice(student_profiles),  # Random student profile from fixtures
                    "category": source_idx + 1,  # Category PK
                    "featured_image": image_path,
                    "summary": article.get('description', fake.paragraph()),
                    "content": generate_html_content(article.get('content'), title),
                    "is_featured": random.random() < 0.2,  # 20% chance of being featured
                    "status": "published",
                    "created_at": str(publish_date - timedelta(hours=random.randint(1, 5))),
                    "updated_at": str(publish_date),
                    "publish_date": str(publish_date),
                    "views": random.randint(0, 1000)
                }
            }
            fixtures.append(news_article)
            
            # Generate 3-5 random tags for this article
            article_tags = random.sample(TAGS, random.randint(3, 5))
            
            # Create comments (3-5 per article)
            comment_count = random.randint(3, 5)
            for _ in range(comment_count):
                # Create a comment made 0-10 days after the article was published
                comment_date = publish_date + timedelta(days=random.randint(0, 10), 
                                                     hours=random.randint(0, 23), 
                                                     minutes=random.randint(0, 59))
                
                # Get users related to student profiles
                user_ids = []
                try:
                    # Extract user IDs from student profiles data
                    if 'student_profiles_data' in locals():
                        for profile in student_profiles_data:
                            if profile['model'] == 'accounts.studentprofile' and 'user' in profile['fields']:
                                user_ids.append(profile['fields']['user'])
                except Exception:
                    # Fallback to some default user IDs
                    user_ids = list(range(1, 21))
                
                # Make sure we have at least some user IDs
                if not user_ids:
                    user_ids = list(range(1, 21))
                
                comment = {
                    "model": "news.comment",
                    "pk": comment_pk,
                    "fields": {
                        "news": news_pk,
                        "user": random.choice(user_ids),  # Random user from profiles
                        "content": fake.paragraph(nb_sentences=random.randint(2, 6)),
                        "created_at": str(comment_date),
                        "is_approved": random.random() < 0.8  # 80% chance of being approved
                    }
                }
                fixtures.append(comment)
                comment_pk += 1
            
            # Generate tags for this article using django-taggit
            for tag_name in article_tags:
                # First, check if this tag already exists
                tag_exists = False
                for fixture in fixtures:
                    if fixture["model"] == "taggit.tag" and fixture["fields"]["name"] == tag_name:
                        tag_exists = True
                        tag_id = fixture["pk"]
                        break
                
                # If tag doesn't exist, create it
                if not tag_exists:
                    tag = {
                        "model": "taggit.tag",
                        "pk": tag_pk,
                        "fields": {
                            "name": tag_name,
                            "slug": slugify(tag_name)
                        }
                    }
                    fixtures.append(tag)
                    tag_id = tag_pk
                    tag_pk += 1
                
                # Create TaggedItem for this news article
                tagged_item = {
                    "model": "taggit.taggeditem",
                    "pk": tagged_item_pk,
                    "fields": {
                        "tag": tag_id,
                        "content_type": 18,  # You need to set this to the ContentType ID for News
                        "object_id": news_pk
                    }
                }
                fixtures.append(tagged_item)
                tagged_item_pk += 1
            
            news_pk += 1
            
    except Exception as e:
        print(f"❌ Error processing source {source}: {e}")

# Save fixture file
with open(FIXTURE_FILE, "w", encoding="utf-8") as f:
    json.dump(fixtures, f, indent=4, ensure_ascii=False)

print(f"✅ Generated {news_pk - 1} news articles with {comment_pk - 1} comments")
print(f"✅ Fixture file saved to {FIXTURE_FILE}")