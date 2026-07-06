"""
Serializers for the Product Customization System.

Provides both lightweight (list) and detailed (detail) serializers
for all models with proper nesting and computed fields.
"""
from rest_framework import serializers
from .models import (
    Category, Product, ProductVariant, ProductView, PrintArea,
    DesignUpload, CustomizationJob, CustomizationVersion,
    RenderJob, Asset,
)


# ──────────────────────────────────────────────
# Category
# ──────────────────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id", "name", "slug", "description", "parent",
            "image", "ordering", "is_active", "product_count", "children",
        ]

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data


# ──────────────────────────────────────────────
# Print Area
# ──────────────────────────────────────────────

class PrintAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintArea
        fields = [
            "id", "product_view", "label", "x", "y",
            "width", "height", "rotation", "max_dpi", "is_default",
        ]


# ──────────────────────────────────────────────
# Product View
# ──────────────────────────────────────────────

class ProductViewSerializer(serializers.ModelSerializer):
    print_areas = PrintAreaSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    image_width = serializers.SerializerMethodField()
    image_height = serializers.SerializerMethodField()

    class Meta:
        model = ProductView
        fields = [
            "id", "product", "view_name", "view_type", "image",
            "image_url", "image_width", "image_height",
            "rotation_metadata", "ordering", "print_areas",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def _dimensions(self, obj):
        """Read image dimensions, tolerating missing files."""
        try:
            return obj.image.width, obj.image.height
        except Exception:
            return None, None

    def get_image_width(self, obj):
        return self._dimensions(obj)[0]

    def get_image_height(self, obj):
        return self._dimensions(obj)[1]


class ProductViewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductView
        fields = [
            "id", "product", "view_name", "view_type", "image",
            "rotation_metadata", "ordering",
        ]


# ──────────────────────────────────────────────
# Product Variant
# ──────────────────────────────────────────────

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            "id", "product", "name", "sku", "color",
            "size", "price_override", "is_active",
        ]


# ──────────────────────────────────────────────
# Product
# ──────────────────────────────────────────────

class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for catalog listings."""
    category_name = serializers.CharField(
        source="category.name", read_only=True, default=None
    )
    view_count = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "category",
            "category_name", "sku", "base_price", "thumbnail",
            "thumbnail_url", "is_active", "view_count", "created_at",
        ]

    def get_view_count(self, obj):
        return obj.views.count()

    def get_thumbnail_url(self, obj):
        """Return thumbnail URL, falling back to first view image."""
        request = self.context.get("request")
        if obj.thumbnail:
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        first_view = obj.views.order_by("ordering").first()
        if first_view and first_view.image:
            if request:
                return request.build_absolute_uri(first_view.image.url)
            return first_view.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full product detail with nested views, print areas, and variants."""
    category = CategorySerializer(read_only=True)
    views = ProductViewSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "category",
            "sku", "base_price", "tags", "thumbnail",
            "is_active", "views", "variants",
            "created_at", "updated_at",
        ]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products."""
    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "category",
            "sku", "base_price", "tags", "thumbnail", "is_active",
        ]


# ──────────────────────────────────────────────
# Design Upload
# ──────────────────────────────────────────────

class DesignUploadSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = DesignUpload
        fields = [
            "id", "user", "image", "original_filename", "file_size",
            "width", "height", "mime_type", "thumbnail",
            "thumbnail_url", "uploaded_at", "status",
        ]
        read_only_fields = [
            "user", "original_filename", "file_size", "width",
            "height", "mime_type", "thumbnail", "uploaded_at", "status",
        ]

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None


# ──────────────────────────────────────────────
# Customization Job
# ──────────────────────────────────────────────

class CustomizationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizationJob
        fields = [
            "id", "user", "design", "product_view",
            "design_settings", "output_image", "status",
            "share_token", "is_public", "created_at", "updated_at",
        ]
        read_only_fields = [
            "user", "output_image", "status",
            "share_token", "created_at", "updated_at",
        ]


class CustomizationJobDetailSerializer(serializers.ModelSerializer):
    """Full customization detail with nested design, product view, and versions."""
    design = DesignUploadSerializer(read_only=True)
    product_view = ProductViewSerializer(read_only=True)
    versions = serializers.SerializerMethodField()
    render_jobs = serializers.SerializerMethodField()

    class Meta:
        model = CustomizationJob
        fields = [
            "id", "user", "design", "product_view",
            "design_settings", "output_image", "status",
            "share_token", "is_public",
            "versions", "render_jobs",
            "created_at", "updated_at",
        ]

    def get_versions(self, obj):
        versions = obj.versions.all()[:10]
        return CustomizationVersionSerializer(
            versions, many=True, context=self.context
        ).data

    def get_render_jobs(self, obj):
        jobs = obj.render_jobs.all()[:5]
        return RenderJobSerializer(
            jobs, many=True, context=self.context
        ).data


# ──────────────────────────────────────────────
# Customization Version
# ──────────────────────────────────────────────

class CustomizationVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizationVersion
        fields = [
            "id", "job", "version_number", "design_settings",
            "snapshot_image", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ──────────────────────────────────────────────
# Render Job
# ──────────────────────────────────────────────

class RenderJobSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()

    class Meta:
        model = RenderJob
        fields = [
            "id", "customization", "render_type", "quality",
            "status", "progress", "output_image",
            "render_metadata", "error_message",
            "queued_at", "started_at", "completed_at", "duration",
        ]
        read_only_fields = [
            "status", "progress", "output_image",
            "render_metadata", "error_message",
            "queued_at", "started_at", "completed_at",
        ]

    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            delta = obj.completed_at - obj.started_at
            return round(delta.total_seconds(), 2)
        return None


# ──────────────────────────────────────────────
# Asset
# ──────────────────────────────────────────────

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "id", "name", "file", "asset_type", "file_size",
            "width", "height", "mime_type", "checksum", "created_at",
        ]
        read_only_fields = ["file_size", "width", "height", "checksum", "created_at"]