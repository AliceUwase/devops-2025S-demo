"""Seed the campus notifier database with sample data.

Run from the project root with::

    python seed_data.py

The script is idempotent: it will not duplicate records that already exist.
It guarantees at least twenty records for each main entity type.
"""

import os
import random
from datetime import timedelta
from typing import List

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campus_notifier.settings")

import django

django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

from events.models import Event, EventCategory, EventRegistration
from notifications.models import (
    CategorySubscription,
    Notification,
    NotificationPreference,
)

CATEGORY_NAMES: List[str] = [
    "Academic",
    "Sports",
    "Cultural",
    "Career",
    "Technology",
    "Health",
    "Arts",
    "Science",
    "Business",
    "Social",
    "Music",
    "Literature",
    "Engineering",
    "Medicine",
    "Law",
    "Education",
    "Environment",
    "Entrepreneurship",
    "Research",
    "Community",
    "Volunteering",
    "Innovation",
]

STATUS_CHOICES: List[str] = ["draft", "published", "cancelled", "completed"]
NOTIFICATION_TYPES: List[str] = [
    "new_event",
    "event_update",
    "event_reminder",
    "event_cancelled",
    "registration_confirmation",
]


def seed_users(count: int = 25) -> List[User]:
    """Create or retrieve the requested number of student users.

    Each user is given the default password ``password123``. Existing users
    are not modified.

    Args:
        count: Number of users to ensure exist.

    Returns:
        List of User instances.
    """
    users: List[User] = []
    for i in range(1, count + 1):
        username = f"student{i}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"student{i}@campus.edu",
                "first_name": f"Student{i}",
                "last_name": "Demo",
            },
        )
        if created:
            user.set_password("password123")
            user.save()
        users.append(user)
    return users


def seed_categories(count: int = 22) -> List[EventCategory]:
    """Create or retrieve event categories from the predefined list.

    Args:
        count: Number of categories to ensure exist.

    Returns:
        List of EventCategory instances.
    """
    categories: List[EventCategory] = []
    for name in CATEGORY_NAMES[:count]:
        category, _ = EventCategory.objects.get_or_create(
            name=name, defaults={"description": f"Events related to {name.lower()}."}
        )
        categories.append(category)
    return categories


def seed_events(
    users: List[User], categories: List[EventCategory], count: int = 25
) -> List[Event]:
    """Create or retrieve the requested number of events.

    Each event is assigned a random organizer, category, status, and
    schedule within a thirty day window around the current time.

    Args:
        users: Pool of users to choose organizers from.
        categories: Pool of categories to assign.
        count: Number of events to ensure exist.

    Returns:
        List of Event instances.
    """
    events: List[Event] = []
    now = timezone.now()
    for i in range(1, count + 1):
        organizer = random.choice(users)
        category = random.choice(categories)
        start = now + timedelta(
            days=random.randint(-10, 30), hours=random.randint(0, 23)
        )
        end = start + timedelta(hours=random.randint(1, 4))
        event, _ = Event.objects.get_or_create(
            title=f"Campus Event {i}",
            defaults={
                "description": f"Description for campus event number {i}.",
                "location": f"Building {random.randint(1, 10)}, Room {random.randint(1, 50)}",
                "start_datetime": start,
                "end_datetime": end,
                "category": category,
                "organizer": organizer,
                "status": random.choice(STATUS_CHOICES),
                "max_participants": random.choice([None, 20, 50, 100]),
                "registration_required": random.choice([True, False]),
            },
        )
        events.append(event)
    return events


def seed_registrations(
    users: List[User], events: List[Event], count: int = 25
) -> List[EventRegistration]:
    """Create registrations linking users to events.

    Duplicate user-event pairs are skipped automatically. Attempts up to
    five times the requested count to reach the target.

    Args:
        users: Pool of users to register.
        events: Pool of events to register for.
        count: Number of registrations to ensure exist.

    Returns:
        List of EventRegistration instances.
    """
    registrations: List[EventRegistration] = []
    attempts = 0
    while len(registrations) < count and attempts < count * 5:
        attempts += 1
        user = random.choice(users)
        event = random.choice(events)
        registration, _ = EventRegistration.objects.get_or_create(
            user=user, event=event, defaults={"attended": random.choice([True, False])}
        )
        registrations.append(registration)
    return registrations


def seed_preferences(users: List[User]) -> List[NotificationPreference]:
    """Create a notification preference record for each user.

    Args:
        users: Users to create preferences for.

    Returns:
        List of NotificationPreference instances.
    """
    preferences: List[NotificationPreference] = []
    for user in users:
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        preferences.append(pref)
    return preferences


def seed_subscriptions(
    users: List[User], categories: List[EventCategory], count: int = 25
) -> List[CategorySubscription]:
    """Create category subscriptions linking users to categories.

    Duplicate user-category pairs are skipped automatically.

    Args:
        users: Pool of users to subscribe.
        categories: Pool of categories to subscribe to.
        count: Number of subscriptions to ensure exist.

    Returns:
        List of CategorySubscription instances.
    """
    subscriptions: List[CategorySubscription] = []
    attempts = 0
    while len(subscriptions) < count and attempts < count * 5:
        attempts += 1
        user = random.choice(users)
        category = random.choice(categories)
        subscription, _ = CategorySubscription.objects.get_or_create(
            user=user, category=category
        )
        subscriptions.append(subscription)
    return subscriptions


def seed_notifications(
    users: List[User], events: List[Event], count: int = 25
) -> List[Notification]:
    """Create the requested number of notifications.

    Each notification is assigned a random user, event, type, and read state.

    Args:
        users: Pool of users to notify.
        events: Pool of events to reference.
        count: Number of notifications to create.

    Returns:
        List of Notification instances.
    """
    notifications: List[Notification] = []
    for i in range(1, count + 1):
        user = random.choice(users)
        event = random.choice(events)
        notification = Notification.objects.create(
            user=user,
            event=event,
            notification_type=random.choice(NOTIFICATION_TYPES),
            title=f"Notification {i}",
            message=f"This is notification number {i} for {user.username}.",
            is_read=random.choice([True, False]),
            sent_via=random.choice(["in_app", "email", "sms", "push"]),
        )
        notifications.append(notification)
    return notifications


def main() -> None:
    """Run all seed functions and print a summary."""
    users = seed_users(25)
    categories = seed_categories(22)
    events = seed_events(users, categories, 25)
    registrations = seed_registrations(users, events, 25)
    preferences = seed_preferences(users)
    subscriptions = seed_subscriptions(users, categories, 25)
    notifications = seed_notifications(users, events, 25)

    print("Seeding complete.")
    print(f"Users: {len(users)}")
    print(f"Categories: {len(categories)}")
    print(f"Events: {len(events)}")
    print(f"Registrations: {len(registrations)}")
    print(f"Preferences: {len(preferences)}")
    print(f"Subscriptions: {len(subscriptions)}")
    print(f"Notifications: {len(notifications)}")


if __name__ == "__main__":
    main()
