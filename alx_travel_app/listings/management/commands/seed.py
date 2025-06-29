from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from listings.models import Listing, Booking, Review
from faker import Faker
import random
from datetime import datetime, timedelta

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Seeds the database with sample listings, bookings, and reviews'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')
        self.create_users()
        self.create_listings()
        self.create_bookings()
        self.create_reviews()
        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))

    def create_users(self):
        # Create admin user
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

        # Create hosts
        for i in range(3):
            User.objects.create_user(
                username=f'host{i+1}',
                email=f'host{i+1}@example.com',
                password=f'host{i+1}123',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )

        # Create guests
        for i in range(10):
            User.objects.create_user(
                username=f'guest{i+1}',
                email=f'guest{i+1}@example.com',
                password=f'guest{i+1}123',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )

    def create_listings(self):
        hosts = User.objects.filter(username__startswith='host')
        property_types = ['AP', 'HO', 'VI', 'CO', 'TH']
        amenities = [
            "WiFi,Kitchen,Washer,Dryer,Air conditioning,Heating",
            "Pool,Hot tub,Free parking,TV,Cable TV",
            "Gym,BBQ grill,Patio,Fireplace"
        ]

        for i in range(15):
            Listing.objects.create(
                title=fake.sentence(nb_words=4),
                description=fake.paragraph(nb_sentences=5),
                address=fake.street_address(),
                city=fake.city(),
                country=fake.country(),
                price_per_night=random.randint(50, 500),
                property_type=random.choice(property_types),
                num_bedrooms=random.randint(1, 5),
                num_bathrooms=random.randint(1, 3),
                max_guests=random.randint(2, 10),
                amenities=random.choice(amenities),
                host=random.choice(hosts)
            )

    def create_bookings(self):
        listings = Listing.objects.all()
        guests = User.objects.filter(username__startswith='guest')
        statuses = ['PE', 'CO', 'CA', 'CO']

        for i in range(30):
            listing = random.choice(listings)
            check_in = fake.date_between(start_date='-30d', end_date='+30d')
            check_out = check_in + timedelta(days=random.randint(2, 14))
            
            Booking.objects.create(
                listing=listing,
                guest=random.choice(guests),
                check_in=check_in,
                check_out=check_out,
                total_price=(check_out - check_in).days * listing.price_per_night,
                status=random.choice(statuses),
                special_requests=fake.sentence() if random.random() > 0.5 else ''
            )

    def create_reviews(self):
        bookings = Booking.objects.filter(status='CO')
        
        for booking in bookings[:20]:  # Review first 20 completed bookings
            Review.objects.create(
                listing=booking.listing,
                guest=booking.guest,
                rating=random.randint(1, 5),
                comment=fake.paragraph(nb_sentences=2)
            )