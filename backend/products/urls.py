"""
URL configuration for the products app.

Provides routes for products, categories, views, print areas,
design uploads, customizations, rendering, versioning, sharing,
assets, and admin analytics.
"""
from django.urls import path
from .views import (
    # Categories
    CategoryListView, CategoryDetailView,
    # Products
    ProductListView, ProductDetailView, ProductBySlugView,
    # Product Views
    ProductViewListView, ProductViewDetailView, ProductViewsByProductView,
    # Print Areas
    PrintAreaListView, PrintAreaDetailView,
    # Design Uploads
    DesignUploadListView, DesignUploadDetailView,
    # Customization Jobs
    CustomizationJobListView, CustomizationJobDetailView,
    # Render Jobs
    RenderJobStartView, RenderJobStatusView, RenderJobDownloadView,
    # Versions
    CustomizationVersionListView,
    # Sharing
    ShareCustomizationView,
    # Admin
    AdminAnalyticsView,
    # Assets
    AssetListView, AssetDetailView,
)

urlpatterns = [
    # ── Categories ──
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/<int:id>/", CategoryDetailView.as_view(), name="category-detail"),

    # ── Products ──
    path("", ProductListView.as_view(), name="product-list"),
    path("<int:id>/", ProductDetailView.as_view(), name="product-detail"),
    path("slug/<slug:slug>/", ProductBySlugView.as_view(), name="product-by-slug"),

    # ── Product Views ──
    path("views/", ProductViewListView.as_view(), name="product-view-list"),
    path("views/<int:id>/", ProductViewDetailView.as_view(), name="product-view-detail"),
    path("<int:product_id>/views/", ProductViewsByProductView.as_view(), name="product-views-by-product"),

    # ── Print Areas ──
    path("print-areas/", PrintAreaListView.as_view(), name="print-area-list"),
    path("print-areas/<int:id>/", PrintAreaDetailView.as_view(), name="print-area-detail"),

    # ── Design Uploads ──
    path("design-uploads/", DesignUploadListView.as_view(), name="design-upload-list"),
    path("design-uploads/<int:id>/", DesignUploadDetailView.as_view(), name="design-upload-detail"),

    # ── Customization Jobs ──
    path("customization-jobs/", CustomizationJobListView.as_view(), name="customization-job-list"),
    path("customization-jobs/<int:id>/", CustomizationJobDetailView.as_view(), name="customization-job-detail"),

    # ── Render Jobs ──
    path("customization-jobs/<int:job_id>/render/", RenderJobStartView.as_view(), name="render-job-start"),
    path("render-jobs/<int:id>/status/", RenderJobStatusView.as_view(), name="render-job-status"),
    path("render-jobs/<int:id>/download/", RenderJobDownloadView.as_view(), name="render-job-download"),

    # ── Versions ──
    path("customization-jobs/<int:job_id>/versions/", CustomizationVersionListView.as_view(), name="customization-version-list"),

    # ── Sharing ──
    path("share/<uuid:share_token>/", ShareCustomizationView.as_view(), name="share-customization"),
    path("customization-jobs/<int:job_id>/share/", ShareCustomizationView.as_view(), name="toggle-share"),

    # ── Assets ──
    path("assets/", AssetListView.as_view(), name="asset-list"),
    path("assets/<int:id>/", AssetDetailView.as_view(), name="asset-detail"),

    # ── Admin Analytics ──
    path("admin/analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
]