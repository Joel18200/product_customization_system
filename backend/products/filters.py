"""
Django-filter FilterSets for the Product Customization System.
"""
import django_filters
from .models import Product, CustomizationJob, RenderJob, DesignUpload


class ProductFilter(django_filters.FilterSet):
    """Filter products by category, price range, status, and search."""
    category = django_filters.NumberFilter(field_name="category__id")
    category_slug = django_filters.CharFilter(field_name="category__slug")
    min_price = django_filters.NumberFilter(
        field_name="base_price", lookup_expr="gte"
    )
    max_price = django_filters.NumberFilter(
        field_name="base_price", lookup_expr="lte"
    )
    search = django_filters.CharFilter(method="filter_search")
    tags = django_filters.CharFilter(method="filter_tags")

    class Meta:
        model = Product
        fields = ["category", "is_active"]

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(sku__icontains=value)
        )

    def filter_tags(self, queryset, name, value):
        return queryset.filter(tags__contains=[value])


class CustomizationJobFilter(django_filters.FilterSet):
    """Filter customization jobs by status, date range, user."""
    status = django_filters.CharFilter()
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )
    product = django_filters.NumberFilter(
        field_name="product_view__product__id"
    )

    class Meta:
        model = CustomizationJob
        fields = ["status", "is_public", "user"]


class RenderJobFilter(django_filters.FilterSet):
    """Filter render jobs by status and type."""
    class Meta:
        model = RenderJob
        fields = ["status", "render_type"]


class DesignUploadFilter(django_filters.FilterSet):
    """Filter design uploads by status and type."""
    class Meta:
        model = DesignUpload
        fields = ["status", "mime_type"]
