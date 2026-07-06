
import uuid
from django.conf import settings
from django.db import models


class Category(models.Model):
    """Product category with optional parent for nested hierarchy."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="children"
    )
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    ordering = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["ordering", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["parent", "ordering"]),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Core product model.

    Extended from original: added category, sku, base_price, tags, thumbnail.
    Original fields preserved: name, slug, description, is_active, created_at.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="products"
    )
    sku = models.CharField(max_length=50, blank=True, db_index=True)
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    tags = models.JSONField(default=list, blank=True)
    thumbnail = models.ImageField(
        upload_to="product_thumbnails/", blank=True, null=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    """Product variant (e.g., color/size combinations)."""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )
    name = models.CharField(max_length=100)  # e.g., "Black / Large"
    sku = models.CharField(max_length=50, blank=True, db_index=True)
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=20, blank=True)
    price_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.product.name} — {self.name}"


class ProductView(models.Model):
    """
    A specific view/angle of a product (front, back, side, etc.).

    Extended from original: added view_type choices, rotation_metadata, ordering.
    Original fields preserved: product, view_name, image.
    """
    VIEW_TYPE_CHOICES = [
        ("front", "Front"),
        ("back", "Back"),
        ("left", "Left Side"),
        ("right", "Right Side"),
        ("custom", "Custom Angle"),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="views"
    )
    view_name = models.CharField(max_length=100)
    view_type = models.CharField(
        max_length=20, choices=VIEW_TYPE_CHOICES, default="front"
    )
    image = models.ImageField(upload_to="product_views/")
    rotation_metadata = models.JSONField(default=dict, blank=True)
    ordering = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordering", "view_name"]
        indexes = [
            models.Index(fields=["product", "view_type"]),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.view_name}"


class PrintArea(models.Model):
    """
    Defines the printable area on a product view.

    Extended from original: added label, max_dpi, rotation, is_default.
    Original fields preserved: product_view, x, y, width, height.
    """
    product_view = models.ForeignKey(
        ProductView, on_delete=models.CASCADE, related_name="print_areas"
    )
    label = models.CharField(max_length=100, blank=True, default="Main")
    x = models.IntegerField()
    y = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()
    rotation = models.FloatField(default=0.0)
    max_dpi = models.IntegerField(default=300)
    is_default = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["product_view", "is_default"]),
        ]

    def __str__(self):
        return f"{self.product_view.product.name}-{self.product_view.view_name} Print Area ({self.label})"


class DesignUpload(models.Model):
    """
    User-uploaded design/artwork.

    Extended from original: added user FK, original_filename, file_size,
    dimensions, mime_type, thumbnail.
    Original fields preserved: image, uploaded_at, status.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="uploads", null=True, blank=True
    )
    image = models.ImageField(upload_to="design_uploads/")
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(default=0)  # bytes
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=50, blank=True)
    thumbnail = models.ImageField(
        upload_to="design_thumbnails/", blank=True, null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["user", "-uploaded_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Design Upload {self.id} ({self.status})"


class CustomizationJob(models.Model):
    """
    A customization session linking a design to a product view.

    Extended from original: added user FK, design_settings JSON,
    share_token, is_public.
    Original fields preserved: design, product_view, output_image, status, created_at.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="customizations", null=True, blank=True
    )
    design = models.ForeignKey(
        DesignUpload, on_delete=models.CASCADE, related_name="customizations"
    )
    product_view = models.ForeignKey(
        ProductView, on_delete=models.CASCADE, related_name="customization_jobs"
    )
    # Design transform settings
    design_settings = models.JSONField(
        default=dict, blank=True,
        help_text="Scale, rotation, position, alignment settings"
    )
    output_image = models.ImageField(
        upload_to="generated_previews/", blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    share_token = models.UUIDField(default=uuid.uuid4, db_index=True, editable=False)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["share_token"]),
        ]

    def __str__(self):
        return f"Customization #{self.id}"


class CustomizationVersion(models.Model):
    """Versioned snapshot of a customization for undo/history."""
    job = models.ForeignKey(
        CustomizationJob, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.IntegerField()
    design_settings = models.JSONField(
        default=dict,
        help_text="Snapshot of design settings at this version"
    )
    snapshot_image = models.ImageField(
        upload_to="version_snapshots/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        unique_together = ["job", "version_number"]

    def __str__(self):
        return f"Customization #{self.job_id} v{self.version_number}"


class RenderJob(models.Model):
    """
    Individual render task, tracked separately from the customization.
    Allows multiple render types (preview, final, thumbnail) per customization.
    """
    RENDER_TYPE_CHOICES = [
        ("preview", "Preview"),
        ("final", "Final Render"),
        ("thumbnail", "Thumbnail"),
    ]
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    customization = models.ForeignKey(
        CustomizationJob, on_delete=models.CASCADE, related_name="render_jobs"
    )
    render_type = models.CharField(max_length=20, choices=RENDER_TYPE_CHOICES)
    quality = models.IntegerField(default=85)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="queued"
    )
    progress = models.IntegerField(default=0)  # 0-100
    output_image = models.ImageField(
        upload_to="renders/", blank=True, null=True
    )
    render_metadata = models.JSONField(
        default=dict, blank=True,
        help_text="Timing, dimensions, pipeline details"
    )
    error_message = models.TextField(blank=True)
    queued_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-queued_at"]
        indexes = [
            models.Index(fields=["customization", "render_type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Render #{self.id} ({self.render_type}) — {self.status}"


class Asset(models.Model):
    """General-purpose asset storage for product images, designs, renders."""
    ASSET_TYPE_CHOICES = [
        ("product_image", "Product Image"),
        ("design", "Design"),
        ("thumbnail", "Thumbnail"),
        ("render", "Render"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="assets/")
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    file_size = models.IntegerField(default=0)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=50, blank=True)
    checksum = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["asset_type"]),
            models.Index(fields=["checksum"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.asset_type})"