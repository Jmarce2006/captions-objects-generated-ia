import os
import json
import random

from faker import Faker
from flask import current_app
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from moments.core.extensions import db
from moments.models import Comment, Notification, Photo, Tag, User

fake = Faker()


def fake_admin():
    admin = User(
        name="Grey Li",
        username="greyli",
        password="moments",
        email="admin@helloflask.com",
        bio=fake.sentence(),
        website="https://greyli.com",
        confirmed=True,
    )
    notification = Notification(message="Hello, welcome to Moments.", receiver=admin)
    db.session.add(notification)
    db.session.add(admin)
    db.session.commit()


def fake_user(count=10):
    for _ in range(count):
        user = User(
            name=fake.name(),
            confirmed=True,
            username=fake.user_name(),
            password="123456",
            bio=fake.sentence(),
            location=fake.city(),
            website=fake.url(),
            member_since=fake.date_this_decade(),
            email=fake.email(),
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_follow(count=30):
    for _ in range(count):
        user = db.session.scalar(select(User).order_by(func.random()).limit(1))
        user2 = db.session.scalar(select(User).order_by(func.random()).limit(1))
        if user != user2:
            user.follow(user2)
    db.session.commit()


def fake_tag(count=20):
    for _ in range(count):
        tag = Tag(name=fake.word())
        db.session.add(tag)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            fake_tag(1)


def fake_photo(count=30):
    upload_path = current_app.config["MOMENTS_UPLOAD_PATH"]

    # Load AI-generated metadata (captions + objects)
    metadata_file = os.path.join(os.getcwd(), "image_metadata.json")
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            image_metadata = json.load(f)
    else:
        image_metadata = {}

    # Get all existing images in the upload folder
    image_files = [f for f in os.listdir(upload_path) if f.lower().endswith((".jpg", ".png"))]

    print(f"Found {len(image_files)} images in the upload folder.")

    for i, filename in enumerate(image_files):
        print(f"Processing image: {filename}...")

        # Get AI-generated description, fallback to random text if missing
        metadata = image_metadata.get(filename, {})
        description = metadata.get("caption", fake.sentence())
        detected_objects = metadata.get("objects", [])

        # Assign a random user as the author
        user_count = db.session.scalar(select(func.count(User.id)))
        user = db.session.get(User, random.randint(1, user_count))

        # Create the Photo object
        photo = Photo(
            description=description,  # AI-generated description
            filename=filename,
            filename_m=filename,
            filename_s=filename,
            author=user,
            created_at=fake.date_time_this_year(),
        )
        db.session.add(photo)

        # Assign AI-detected objects as tags
        for obj in detected_objects:
            tag = db.session.scalar(select(Tag).where(Tag.name == obj))  # Check if tag exists
            if not tag:
                tag = Tag(name=obj)  # Create new tag
                db.session.add(tag)
                db.session.commit()  # Commit immediately to avoid integrity issues
            photo.tags.append(tag)

        # Assign random existing tags
        # for _ in range(random.randint(1, 5)):
        #     tag_count = db.session.scalar(select(func.count(Tag.id)))
        #     tag = db.session.get(Tag, random.randint(1, tag_count))
        #     if tag and tag not in photo.tags:
        #         photo.tags.append(tag)

    db.session.commit()
    print("Images added to the database with AI-generated captions and object tags.")


def fake_collect(count=50):
    for _ in range(count):
        user_count = db.session.scalar(select(func.count(User.id)))
        user = db.session.get(User, random.randint(1, user_count))
        photo_count = db.session.scalar(select(func.count(Photo.id)))
        photo = db.session.get(Photo, random.randint(1, photo_count))
        if user and photo:
            user.collect(photo)
    db.session.commit()


def fake_comment(count=100):
    for _ in range(count):
        user_count = db.session.scalar(select(func.count(User.id)))
        user = db.session.get(User, random.randint(1, user_count))
        photo_count = db.session.scalar(select(func.count(Photo.id)))
        photo = db.session.get(Photo, random.randint(1, photo_count))
        if user and photo:
            comment = Comment(
                author=user,
                body=fake.sentence(),
                created_at=fake.date_time_this_year(),
                photo=photo,
            )
            db.session.add(comment)
    db.session.commit()
