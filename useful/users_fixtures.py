def create_student_fixtures(user_fixtures, app_name):
    """Create student profile and request fixtures."""
    student_profile_fixtures = []
    student_request_fixtures = []
    
    # Keep track of used slugs to ensure uniqueness
    used_slugs = set()
    
    # Choose which users will be students (40% of regular users)
    regular_users = [u for u in user_fixtures if not u["fields"]["is_staff"] and not u["fields"]["is_superuser"]]
    num_student_users = int(len(regular_users) * 0.4)
    student_users = random.sample(regular_users, num_student_users)
    
    # Generate student requests for all student users
    for i, user in enumerate(student_users):
        user_id = user["pk"]
        
        # Create StudentRequest (80% approved, 20% pending)
        is_approved = random.random() < 0.8
        
        # Generate a reason with realistic variation
        reason_options = [
            "I want to learn new skills and improve my knowledge in this field.",
            "I'm interested in the courses offered on this platform.",
            "I'm a student at {university} and need access to additional learning resources.",
            "I want to supplement my current education with online courses.",
            "I'm changing careers and need to learn new skills.",
            "I heard about this platform from friends and would like to join as a student.",
            "I'm interested in continuing education and professional development.",
            "I'm working on a project that requires the knowledge offered here.",
            "I want to expand my horizons and learn something new.",
            "I'm preparing for graduate studies and need additional materials."
        ]
        
        reason = random.choice(reason_options).format(
            university=fake.company()
        )
        
        # Date when request was created
        date_joined = datetime.fromisoformat(user["fields"]["date_joined"])
        request_created_at = fake.date_time_between(
            start_date=date_joined,
            end_date=date_joined + timedelta(days=30),
            tzinfo=pytz.UTC
        )
        
        student_request_fixtures.append({
            "model": f"{app_name}.studentrequest",
            "pk": user_id,
            "fields": {
                "user": user_id,
                "reason": reason,
                "created_at": request_created_at.isoformat(),
                "approved": is_approved
            }
        })
        
        # Only create profiles for approved student requests
        if is_approved:
            # Generate profile data
            first_name = user["fields"]["first_name"]
            last_name = user["fields"]["last_name"]
            full_name = f"{first_name} {last_name}".strip()
            
            # Create a unique slug
            base_slug = slugify(full_name) if full_name else slugify(user["fields"]["username"])
            slug = base_slug
            counter = 1
            
            while slug in used_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            used_slugs.add(slug)
            
            # Generate a bio with varying length and content
            bio_length = random.choice(["short", "medium", "long"])
            if bio_length == "short":
                bio = fake.paragraph()
            elif bio_length == "medium":
                bio = "\n\n".join([fake.paragraph() for _ in range(2)])
            else:
                bio = "\n\n".join([fake.paragraph() for _ in range(3)])
                
            # Some bios might have HTML formatting to test CKEditor field
            if random.random() < 0.3:
                bio = f"<h2>About Me</h2><p>{bio}</p><p><strong>My interests include:</strong></p><ul>"
                for _ in range(random.randint(2, 4)):
                    bio += f"<li>{fake.word()}</li>"
                bio += "</ul>"
            
            # Create some variation in profile picture presence
            profile_picture = "profile_pictures/default.png"
            
            # Date calculations
            profile_created_at = request_created_at + timedelta(hours=random.randint(1, 48))
            
            # Some profiles might have been updated later
            updated_recently = random.random() < 0.3  # 30% updated recently
            profile_updated_at = fake.date_time_between(
                start_date=profile_created_at,
                end_date="now",
                tzinfo=pytz.UTC
            ) if updated_recently else profile_created_at
            
            student_profile_fixtures.append({
                "model": f"{app_name}.studentprofile",
                "pk": user_id,
                "fields": {
                    "user": user_id,
                    "bio": bio,
                    "profile_picture": profile_picture,
                    "slug": slug,
                    "created_at": profile_created_at.isoformat(),
                    "updated_at": profile_updated_at.isoformat()
                }
            })
    
    return student_request_fixtures, student_profile_fixtures#!/usr/bin/env python
"""
Django AllAuth User Fixtures Generator Script (Email-only version)

This script generates fixture data for Django's auth system and django-allauth.
It creates users with email addresses, passwords, and related AllAuth email models.
This version focuses solely on email authentication (no social auth).

Usage:
    python users_fixtures_generator.py [options]

Options:
    --users NUM          Number of users to generate (default: 50)
    --admins NUM         Number of admin users to generate (default: 2)
    --staff NUM          Number of staff users to generate (default: 5)
    --output DIRECTORY   Directory to output fixture files (default: fixtures/)
    --locales LOCALES    Comma-separated list of locales to use (default: en_US)
    --seed NUM           Random seed for reproducible results (default: None)
"""

import argparse
import json
import os
import random
import sys
import hashlib
import uuid
from datetime import datetime, timedelta
import string
from io import BytesIO

from dateutil import parser

import pytz
from faker import Faker
from django.utils.text import slugify


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate Django user fixtures')
    parser.add_argument('--users', type=int, default=50,
                        help='Number of users to generate (default: 50)')
    parser.add_argument('--admins', type=int, default=2,
                        help='Number of admin users (default: 2)')
    parser.add_argument('--staff', type=int, default=5,
                        help='Number of staff users (default: 5)')
    parser.add_argument('--output', type=str, default='fixtures',
                        help='Output directory (default: fixtures/)')
    parser.add_argument('--locales', type=str, default='en_US',
                        help='Comma-separated list of locales (default: en_US)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducible results')
    parser.add_argument('--app', type=str, default='accounts',
                        help='Django app name where student models are defined (default: accounts)')
    
    return parser.parse_args()


def setup_faker(locales, seed=None):
    """Set up Faker with the specified locales and seed."""
    locales_list = [locale.strip() for locale in locales.split(',')]
    fake = Faker(locales_list)
    if seed is not None:
        Faker.seed(seed)
        random.seed(seed)
    return fake


def generate_password():
    """Generate a secure password hash for Django."""
    # # This is a simplified version - Django's actual password hashing is more complex
    # # For fixtures, we'll use the PBKDF2 algorithm with SHA256
    # raw_password = "password123"  # Default password for all users
    # algorithm = 'pbkdf2_sha256'
    # salt = uuid.uuid4().hex
    # iterations = 260000  # Current Django default
    
    # # Create a hash that mimics Django's format
    # # This is for fixture purposes - in a real app, use django.contrib.auth.hashers
    # hash_obj = hashlib.pbkdf2_hmac(
    #     'sha256', 
    #     raw_password.encode(), 
    #     salt.encode(),
    #     iterations
    # )
    # hash_str = hash_obj.hex()
    
    # # Format as Django stores it
    return "pbkdf2_sha256$1000000$Brr3Sv1QeLIxN04uQocsuL$bzcenUMFi46YSCeaectK/LH4ayH8pt5mtZnJ6md0HcY="


def create_user_fixtures(fake, num_users, num_admins, num_staff):
    """Create user fixtures for Django auth models."""
    usernames = set()
    users = []
    emails = set()  # To ensure unique emails
    
    # Keep track of IDs
    next_id = 1
    
    # Generate admin users first
    for i in range(1, num_admins + 1):
        # Ensure unique email
        while True:
            email = f"admin{i}@example.com"
            if email not in emails:
                emails.add(email)
                break
        
        # Create admin user
        username = f"admin{i}"
        date_joined = fake.date_time_between(start_date='-2y', end_date='now', tzinfo=pytz.UTC)
        last_login = fake.date_time_between(start_date=date_joined, end_date='now', tzinfo=pytz.UTC)
        
        users.append({
            "model": "auth.user",
            "pk": next_id,
            "fields": {
                "password": generate_password(),
                "last_login": last_login.isoformat(),
                "is_superuser": True,
                "username": username,
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": email,
                "is_staff": True,
                "is_active": True,
                "date_joined": date_joined.isoformat(),
            }
        })
        next_id += 1
    
    # Generate staff users
    for i in range(1, num_staff + 1):
        # Ensure unique email
        while True:
            email = f"staff{i}@example.com"
            if email not in emails:
                emails.add(email)
                break
        
        # Create staff user
        username = f"staff{i}"
        date_joined = fake.date_time_between(start_date='-1y', end_date='now', tzinfo=pytz.UTC)
        last_login = fake.date_time_between(start_date=date_joined, end_date='now', tzinfo=pytz.UTC)
        
        users.append({
            "model": "auth.user",
            "pk": next_id,
            "fields": {
                "password": generate_password(),
                "last_login": last_login.isoformat(),
                "is_superuser": False,
                "username": username,
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": email,
                "is_staff": True,
                "is_active": True,
                "date_joined": date_joined.isoformat(),
            }
        })
        next_id += 1
    
    # Generate regular users
    remaining_users = num_users - (num_admins + num_staff)
    for i in range(remaining_users):
        # Ensure unique email
        while True:
            email = fake.email()
            if email not in emails:
                emails.add(email)
                break
        
        # Generate unique username from email
        while True:
            username = email.split('@')[0]
            if len(username) < 3:
                username = f"user_{username}"
            if username in usernames:
                email = fake.email()  # Get a new email if username is taken
                continue
            usernames.add(username)
            break

        
        # Some users may have joined recently, others a while ago
        date_joined = fake.date_time_between(start_date='-3y', end_date='now', tzinfo=pytz.UTC)
        
        # Some users might not have logged in since joining
        has_logged_in = random.random() > 0.1  # 90% have logged in
        last_login = None
        if has_logged_in:
            last_login = fake.date_time_between(start_date=date_joined, end_date='now', tzinfo=pytz.UTC)
        
        # Some users might be inactive
        is_active = random.random() > 0.05  # 95% are active
        
        users.append({
            "model": "auth.user",
            "pk": next_id,
            "fields": {
                "password": generate_password(),
                "last_login": last_login.isoformat() if last_login else None,
                "is_superuser": False,
                "username": username[:30],  # Ensure username isn't too long
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": email,
                "is_staff": False,
                "is_active": is_active,
                "date_joined": date_joined.isoformat(),
            }
        })
        next_id += 1
    
    return users, emails


def create_allauth_fixtures(users, emails):
    """Create django-allauth related fixtures for email-based authentication only."""
    allauth_fixtures = []
    
    # Create EmailAddress objects for each user (allauth model)
    for i, user in enumerate(users):
        user_id = user["pk"]
        email = user["fields"]["email"]
        is_active = user["fields"]["is_active"]
        
        # Most users have verified emails
        verified = random.random() > 0.1  # 90% are verified
        primary = True  # Each user has one primary email
        
        allauth_fixtures.append({
            "model": "account.emailaddress",
            "pk": user_id,
            "fields": {
                "user": user_id,
                "email": email,
                "verified": verified,
                "primary": primary
            }
        })
        
        # Some users might have email confirmation keys
        if not verified and is_active:

            confirmation_sent = fake.date_time_between(
                start_date=parser.isoparse(user["fields"]["date_joined"]),
                end_date='now',
                tzinfo=pytz.UTC
            )
            
            allauth_fixtures.append({
                "model": "account.emailconfirmation",
                "pk": user_id,
                "fields": {
                    "email_address": user_id,
                    "created": confirmation_sent.isoformat(),
                    "sent": confirmation_sent.isoformat(),
                    "key": hashlib.md5(email.encode()).hexdigest()[:32]
                }
            })
    
    return allauth_fixtures


def create_django_site_fixture():
    """Create a fixture for the default Django site."""
    return [{
        "model": "sites.site",
        "pk": 1,
        "fields": {
            "domain": "example.com",
            "name": "Example Site"
        }
    }]


def save_fixtures(fixtures, output_dir, filename):
    """Save fixtures to a JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fixtures, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(fixtures)} fixtures to {output_path}")


def main():
    """Main function to generate and save fixtures."""
    args = parse_args()
    
    # Setup faker
    global fake  # Make fake available to other functions
    fake = setup_faker(args.locales, args.seed)
    
    # Generate user fixtures
    print(f"Generating fixtures for {args.users} users ({args.admins} admins, {args.staff} staff)...")
    user_fixtures, emails = create_user_fixtures(fake, args.users, args.admins, args.staff)
    save_fixtures(user_fixtures, args.output, 'auth_users.json')
    
    # Generate allauth fixtures (email-only)
    print("Generating django-allauth email fixtures...")
    allauth_fixtures = create_allauth_fixtures(user_fixtures, emails)
    save_fixtures(allauth_fixtures, args.output, 'allauth_email.json')
    
    # Generate site fixture
    print("Generating Django site fixture...")
    site_fixture = create_django_site_fixture()
    save_fixtures(site_fixture, args.output, 'sites.json')
    
    # Generate student fixtures
    print("Generating student profile and request fixtures...")
    student_request_fixtures, student_profile_fixtures = create_student_fixtures(user_fixtures, args.app)
    save_fixtures(student_request_fixtures, args.output, 'student_requests.json')
    save_fixtures(student_profile_fixtures, args.output, 'student_profiles.json')
    
    print(f"\nAll fixtures generated successfully in '{args.output}' directory!")
    print("\nTo load fixtures into your Django project:")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'sites.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'auth_users.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'allauth_email.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'student_requests.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'student_profiles.json')}")


if __name__ == '__main__':
    main()