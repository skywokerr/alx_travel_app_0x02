# ALX Travel App - Database Modeling and Seeding

## Project Setup

1. Clone the repository
2. Create and activate a virtual environment
3. Install requirements: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Seed the database: `python manage.py seed`

## Models

- **Listing**: Represents properties available for booking
- **Booking**: Tracks reservations made by guests
- **Review**: Stores guest feedback for listings

## Seeding Process

The seed command creates:
- 1 admin user
- 3 host users
- 10 guest users
- 15 listings
- 30 bookings
- 20 reviews

## Requirements

- Python 3.8+
- Django 3.2+
- Faker (for seeding)