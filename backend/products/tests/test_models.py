"""
Tests for Product Customization System models.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from products.models import (
    Category, Product, ProductVariant, ProductView, PrintArea,
    DesignUpload, CustomizationJob, CustomizationVersion,
    RenderJob, Asset,
)


class CategoryModelTest(TestCase):
    def test_create_category(self):
        cat = Category.objects.create(name="Apparel", slug="apparel")
        self.assertEqual(str(cat), "Apparel")
        self.assertTrue(cat.is_active)

    def test_nested_category(self):
        parent = Category.objects.create(name="Apparel", slug="apparel")
        child = Category.objects.create(
            name="T-Shirts", slug="t-shirts", parent=parent
        )
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Apparel", slug="apparel")
        self.product = Product.objects.create(
            name="Black T-Shirt",
            slug="black-tshirt",
            category=self.category,
            sku="TSH-001",
            base_price="24.99",
        )

    def test_create_product(self):
        self.assertEqual(str(self.product), "Black T-Shirt")
        self.assertTrue(self.product.is_active)
        self.assertEqual(self.product.category, self.category)

    def test_product_slug_unique(self):
        with self.assertRaises(Exception):
            Product.objects.create(name="Another", slug="black-tshirt")

    def test_product_tags(self):
        self.product.tags = ["cotton", "unisex"]
        self.product.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.tags, ["cotton", "unisex"])


class ProductViewModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Test", slug="test-product"
        )

    def test_create_product_view(self):
        view = ProductView.objects.create(
            product=self.product,
            view_name="Front View",
            view_type="front",
            image="product_views/test.jpg",
        )
        self.assertEqual(str(view), "Test - Front View")
        self.assertEqual(view.view_type, "front")


class PrintAreaModelTest(TestCase):
    def setUp(self):
        product = Product.objects.create(name="Test", slug="test-pa")
        self.view = ProductView.objects.create(
            product=product, view_name="Front",
            image="product_views/test.jpg",
        )

    def test_create_print_area(self):
        pa = PrintArea.objects.create(
            product_view=self.view,
            label="Chest",
            x=100, y=150, width=300, height=400,
        )
        self.assertEqual(pa.max_dpi, 300)  # default
        self.assertTrue(pa.is_default)  # default


class DesignUploadModelTest(TestCase):
    def test_create_upload(self):
        upload = DesignUpload.objects.create(
            image="design_uploads/test.png",
            original_filename="logo.png",
            file_size=1024,
            width=500,
            height=500,
            mime_type="image/png",
        )
        self.assertEqual(upload.status, "pending")
        self.assertIn("Design Upload", str(upload))


class CustomizationJobModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        product = Product.objects.create(name="Test", slug="test-cj")
        self.view = ProductView.objects.create(
            product=product, view_name="Front",
            image="product_views/test.jpg",
        )
        self.design = DesignUpload.objects.create(
            image="design_uploads/test.png",
        )

    def test_create_customization_job(self):
        job = CustomizationJob.objects.create(
            user=self.user,
            design=self.design,
            product_view=self.view,
            design_settings={"scale": 0.8, "rotation": 15},
        )
        self.assertEqual(job.status, "pending")
        self.assertIsNotNone(job.share_token)
        self.assertFalse(job.is_public)

    def test_customization_version(self):
        job = CustomizationJob.objects.create(
            design=self.design,
            product_view=self.view,
        )
        version = CustomizationVersion.objects.create(
            job=job,
            version_number=1,
            design_settings={"scale": 0.9},
        )
        self.assertEqual(version.version_number, 1)
        self.assertIn(version, job.versions.all())


class RenderJobModelTest(TestCase):
    def setUp(self):
        product = Product.objects.create(name="Test", slug="test-rj")
        view = ProductView.objects.create(
            product=product, view_name="Front",
            image="product_views/test.jpg",
        )
        design = DesignUpload.objects.create(
            image="design_uploads/test.png",
        )
        self.customization = CustomizationJob.objects.create(
            design=design, product_view=view,
        )

    def test_create_render_job(self):
        rj = RenderJob.objects.create(
            customization=self.customization,
            render_type="preview",
            quality=85,
        )
        self.assertEqual(rj.status, "queued")
        self.assertEqual(rj.progress, 0)


class AssetModelTest(TestCase):
    def test_create_asset(self):
        asset = Asset.objects.create(
            name="Product Image",
            file="assets/test.jpg",
            asset_type="product_image",
            file_size=2048,
            mime_type="image/jpeg",
        )
        self.assertEqual(str(asset), "Product Image (product_image)")
