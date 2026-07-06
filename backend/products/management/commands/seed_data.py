"""
Management command to seed the database with sample products.

Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from products.models import Category, Product, ProductView, PrintArea


class Command(BaseCommand):
    help = "Seed database with sample products, views, and print areas"

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        # Categories
        apparel, _ = Category.objects.get_or_create(
            slug="apparel",
            defaults={"name": "Apparel", "description": "Clothing and wearable items", "ordering": 1}
        )
        accessories, _ = Category.objects.get_or_create(
            slug="accessories",
            defaults={"name": "Accessories", "description": "Hats, bags, and accessories", "ordering": 2}
        )

        tshirts, _ = Category.objects.get_or_create(
            slug="t-shirts",
            defaults={"name": "T-Shirts", "parent": apparel, "ordering": 1}
        )
        hoodies, _ = Category.objects.get_or_create(
            slug="hoodies",
            defaults={"name": "Hoodies", "parent": apparel, "ordering": 2}
        )
        hats, _ = Category.objects.get_or_create(
            slug="hats",
            defaults={"name": "Hats & Caps", "parent": accessories, "ordering": 1}
        )

        self.stdout.write(self.style.SUCCESS(f"  Created {Category.objects.count()} categories"))

        # Products
        products_data = [
            {
                "name": "Classic Black T-Shirt",
                "slug": "classic-black-tshirt",
                "description": "Premium cotton t-shirt in classic black. Perfect for custom prints.",
                "category": tshirts,
                "sku": "TSH-BLK-001",
                "base_price": 24.99,
                "tags": ["cotton", "unisex", "casual"],
            },
            {
                "name": "White Crew Neck T-Shirt",
                "slug": "white-crew-neck-tshirt",
                "description": "Soft white crew neck t-shirt. Ideal canvas for vibrant designs.",
                "category": tshirts,
                "sku": "TSH-WHT-001",
                "base_price": 22.99,
                "tags": ["cotton", "unisex", "casual"],
            },
            {
                "name": "Black Pullover Hoodie",
                "slug": "black-pullover-hoodie",
                "description": "Warm fleece hoodie with kangaroo pocket. Great for bold prints.",
                "category": hoodies,
                "sku": "HOD-BLK-001",
                "base_price": 44.99,
                "tags": ["fleece", "unisex", "winter"],
            },
            {
                "name": "Khaki Baseball Cap",
                "slug": "khaki-baseball-cap",
                "description": "Structured baseball cap with adjustable strap. Embroidery-ready.",
                "category": hats,
                "sku": "CAP-KHK-001",
                "base_price": 19.99,
                "tags": ["cotton", "unisex", "outdoor"],
            },
            {
                "name": "Forest Green T-Shirt",
                "slug": "forest-green-tshirt",
                "description": "Rich forest green cotton tee. Earthy tones for nature-inspired designs.",
                "category": tshirts,
                "sku": "TSH-GRN-001",
                "base_price": 24.99,
                "tags": ["cotton", "unisex", "casual"],
            },
        ]

        for data in products_data:
            Product.objects.get_or_create(
                slug=data["slug"],
                defaults=data,
            )

        self.stdout.write(self.style.SUCCESS(f"  Created {Product.objects.count()} products"))

        # Note: ProductViews and PrintAreas should be created via admin
        # once actual product images are uploaded. Here we create placeholder
        # entries for any existing product views.
        self.stdout.write(
            self.style.SUCCESS(
                "\nSeeding complete! Upload product images via admin "
                "and configure print areas for each view."
            )
        )
