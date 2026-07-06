"""
Enhanced Django admin configuration for the Product Customization System.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Product, ProductVariant, ProductView, PrintArea,
    DesignUpload, CustomizationJob, CustomizationVersion,
    RenderJob, Asset,
)


# ──────────────────────────────────────────────
# Inlines
# ──────────────────────────────────────────────

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ["name", "sku", "color", "size", "price_override", "is_active"]


class ProductViewInline(admin.TabularInline):
    model = ProductView
    extra = 1
    fields = ["view_name", "view_type", "image", "ordering"]
    readonly_fields = ["image_preview"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 60px;" />', obj.image.url
            )
        return "-"


class PrintAreaInline(admin.TabularInline):
    model = PrintArea
    extra = 1
    fields = ["label", "x", "y", "width", "height", "rotation", "is_default"]


class CustomizationVersionInline(admin.TabularInline):
    model = CustomizationVersion
    extra = 0
    readonly_fields = ["version_number", "design_settings", "created_at"]
    fields = ["version_number", "design_settings", "snapshot_image", "created_at"]


class RenderJobInline(admin.TabularInline):
    model = RenderJob
    extra = 0
    readonly_fields = ["render_type", "status", "progress", "queued_at",
                       "started_at", "completed_at", "error_message"]
    fields = ["render_type", "status", "progress", "quality",
              "queued_at", "completed_at", "error_message"]


# ──────────────────────────────────────────────
# Model Admins
# ──────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "ordering", "is_active"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["ordering", "name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "category", "sku", "base_price",
                    "is_active", "thumbnail_preview", "created_at"]
    list_filter = ["is_active", "category", "created_at"]
    search_fields = ["name", "slug", "sku", "description"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline, ProductViewInline]
    readonly_fields = ["created_at", "updated_at"]
    list_editable = ["is_active"]
    actions = ["activate_products", "deactivate_products"]

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-height: 40px;" />', obj.thumbnail.url
            )
        return "-"
    thumbnail_preview.short_description = "Thumb"

    @admin.action(description="Activate selected products")
    def activate_products(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected products")
    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["product", "name", "sku", "color", "size", "is_active"]
    list_filter = ["is_active", "product"]
    search_fields = ["name", "sku"]


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ["product", "view_name", "view_type", "ordering",
                    "image_preview"]
    list_filter = ["view_type", "product"]
    search_fields = ["view_name", "product__name"]
    inlines = [PrintAreaInline]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 60px;" />', obj.image.url
            )
        return "-"
    image_preview.short_description = "Preview"


@admin.register(PrintArea)
class PrintAreaAdmin(admin.ModelAdmin):
    list_display = ["product_view", "label", "x", "y", "width", "height",
                    "rotation", "is_default"]
    list_filter = ["is_default"]
    search_fields = ["product_view__view_name", "label"]


@admin.register(DesignUpload)
class DesignUploadAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "original_filename", "mime_type",
                    "file_size_display", "status", "uploaded_at",
                    "image_preview"]
    list_filter = ["status", "mime_type", "uploaded_at"]
    search_fields = ["original_filename", "user__username"]
    readonly_fields = ["uploaded_at", "file_size", "width", "height"]

    def file_size_display(self, obj):
        if obj.file_size:
            kb = obj.file_size / 1024
            if kb > 1024:
                return f"{kb / 1024:.1f} MB"
            return f"{kb:.0f} KB"
        return "-"
    file_size_display.short_description = "Size"

    def image_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-height: 40px;" />', obj.thumbnail.url
            )
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 40px;" />', obj.image.url
            )
        return "-"
    image_preview.short_description = "Preview"


@admin.register(CustomizationJob)
class CustomizationJobAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "design", "product_view", "status",
                    "is_public", "created_at", "output_preview"]
    list_filter = ["status", "is_public", "created_at"]
    search_fields = ["user__username", "share_token"]
    readonly_fields = ["share_token", "created_at", "updated_at"]
    inlines = [CustomizationVersionInline, RenderJobInline]

    def output_preview(self, obj):
        if obj.output_image:
            return format_html(
                '<img src="{}" style="max-height: 40px;" />', obj.output_image.url
            )
        return "-"
    output_preview.short_description = "Output"


@admin.register(CustomizationVersion)
class CustomizationVersionAdmin(admin.ModelAdmin):
    list_display = ["job", "version_number", "created_at"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at"]


@admin.register(RenderJob)
class RenderJobAdmin(admin.ModelAdmin):
    list_display = ["id", "customization", "render_type", "status",
                    "progress", "quality", "queued_at", "completed_at"]
    list_filter = ["status", "render_type", "queued_at"]
    readonly_fields = ["queued_at", "started_at", "completed_at",
                       "render_metadata"]
    actions = ["retry_failed_jobs"]

    @admin.action(description="Retry failed render jobs")
    def retry_failed_jobs(self, request, queryset):
        failed = queryset.filter(status="failed")
        failed.update(status="queued", progress=0, error_message="")
        self.message_user(request, f"Re-queued {failed.count()} failed jobs.")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["name", "asset_type", "mime_type", "file_size",
                    "width", "height", "created_at"]
    list_filter = ["asset_type", "mime_type"]
    search_fields = ["name", "checksum"]
    readonly_fields = ["created_at"]


# Admin site customization
admin.site.site_header = "Product Customization Admin"
admin.site.site_title = "Customization Admin"
admin.site.index_title = "Dashboard"
