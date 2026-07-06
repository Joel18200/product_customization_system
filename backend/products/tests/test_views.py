"""
Tests for Product Customization System API views.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from products.models import (
    Category, Product, ProductView, PrintArea, DesignUpload,
)


class ProductAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(
            name="Apparel", slug="apparel"
        )
        self.product = Product.objects.create(
            name="Black T-Shirt",
            slug="black-tshirt",
            category=self.category,
            sku="TSH-001",
            base_price="24.99",
        )

    def test_list_products(self):
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)

    def test_product_detail(self):
        response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Black T-Shirt")

    def test_product_by_slug(self):
        response = self.client.get("/api/products/slug/black-tshirt/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["slug"], "black-tshirt")

    def test_product_search(self):
        response = self.client.get("/api/products/?search=black")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_product_search_no_results(self):
        response = self.client.get("/api/products/?search=nonexistent")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_product_filter_by_category(self):
        response = self.client.get("/api/products/?category_slug=apparel")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)


class CategoryAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(
            name="Apparel", slug="apparel"
        )

    def test_list_categories(self):
        response = self.client.get("/api/products/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class AuthAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register(self):
        response = self.client.post("/api/auth/register/", {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_register_password_mismatch(self):
        response = self.client.post("/api/auth/register/", {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123",
            "password_confirm": "differentpass",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        User.objects.create_user(
            username="testuser", password="securepass123"
        )
        response = self.client.post("/api/auth/login/", {
            "username": "testuser",
            "password": "securepass123",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_profile_unauthenticated(self):
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_authenticated(self):
        user = User.objects.create_user(
            username="testuser", password="securepass123"
        )
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")


class DesignUploadAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_uploads(self):
        response = self.client.get("/api/products/design-uploads/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminAnalyticsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin", password="admin123"
        )

    def test_analytics_requires_admin(self):
        response = self.client.get("/api/products/admin/analytics/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_analytics_admin_access(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/products/admin/analytics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("products", response.data)
        self.assertIn("renders", response.data)
