"""
API views for the Product Customization System.

Extends the original CRUD views with filtering, pagination, permissions,
and new endpoints for categories, rendering, versioning, and sharing.
"""
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly,
)
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Q

from .models import (
    Category, Product, ProductVariant, ProductView, PrintArea,
    DesignUpload, CustomizationJob, CustomizationVersion,
    RenderJob, Asset,
)
from .serializers import (
    CategorySerializer,
    ProductListSerializer, ProductDetailSerializer, ProductCreateUpdateSerializer,
    ProductVariantSerializer,
    ProductViewSerializer, ProductViewCreateSerializer,
    PrintAreaSerializer,
    DesignUploadSerializer,
    CustomizationJobSerializer, CustomizationJobDetailSerializer,
    CustomizationVersionSerializer,
    RenderJobSerializer,
    AssetSerializer,
)
from .services.image_utils import validate_image, get_image_dimensions
from accounts.permissions import IsAdminOrReadOnly, IsOwnerOrAdmin


# ──────────────────────────────────────────────
# Categories
# ──────────────────────────────────────────────

class CategoryListView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        """List all top-level categories (with nested children)."""
        categories = Category.objects.filter(
            parent__isnull=True, is_active=True
        ).order_by("ordering", "name")
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new category (admin only)."""
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, id):
        category = get_object_or_404(Category, id=id)
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    def put(self, request, id):
        category = get_object_or_404(Category, id=id)
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        category = get_object_or_404(Category, id=id)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Products
# ──────────────────────────────────────────────

class ProductListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        """List products with optional filtering and search."""
        products = Product.objects.filter(is_active=True).select_related("category")

        # Search
        search = request.query_params.get("search")
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search)
            )

        # Category filter
        category = request.query_params.get("category")
        if category:
            products = products.filter(category_id=category)

        category_slug = request.query_params.get("category_slug")
        if category_slug:
            products = products.filter(category__slug=category_slug)

        # Price range
        min_price = request.query_params.get("min_price")
        if min_price:
            products = products.filter(base_price__gte=min_price)

        max_price = request.query_params.get("max_price")
        if max_price:
            products = products.filter(base_price__lte=max_price)

        # Ordering
        ordering = request.query_params.get("ordering", "-created_at")
        allowed_orderings = [
            "name", "-name", "base_price", "-base_price",
            "created_at", "-created_at",
        ]
        if ordering in allowed_orderings:
            products = products.order_by(ordering)

        # Simple pagination
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_size = min(page_size, 100)  # Cap at 100
        start = (page - 1) * page_size
        end = start + page_size

        total = products.count()
        products_page = products[start:end]

        serializer = ProductListSerializer(
            products_page, many=True, context={"request": request}
        )
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "results": serializer.data,
        })

    def post(self, request):
        """Create a new product (admin only)."""
        if not request.user.is_staff:
            return Response(
                {"detail": "Admin access required."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ProductCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, id):
        """Get full product details with views, print areas, and variants."""
        product = get_object_or_404(
            Product.objects.prefetch_related(
                "views__print_areas", "variants"
            ).select_related("category"),
            id=id
        )
        serializer = ProductDetailSerializer(product, context={"request": request})
        return Response(serializer.data)

    def put(self, request, id):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        product = get_object_or_404(Product, id=id)
        serializer = ProductCreateUpdateSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        product = get_object_or_404(Product, id=id)
        serializer = ProductCreateUpdateSerializer(
            product, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        product = get_object_or_404(Product, id=id)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductBySlugView(APIView):
    """Get product by slug instead of ID (for frontend SEO URLs)."""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        product = get_object_or_404(
            Product.objects.prefetch_related(
                "views__print_areas", "variants"
            ).select_related("category"),
            slug=slug, is_active=True
        )
        serializer = ProductDetailSerializer(product, context={"request": request})
        return Response(serializer.data)


# ──────────────────────────────────────────────
# Product Views
# ──────────────────────────────────────────────

class ProductViewListView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        views = ProductView.objects.all().select_related("product")
        product_id = request.query_params.get("product")
        if product_id:
            views = views.filter(product_id=product_id)
        serializer = ProductViewSerializer(
            views, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductViewCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductViewDetailView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, id):
        pv = get_object_or_404(
            ProductView.objects.prefetch_related("print_areas"), id=id
        )
        serializer = ProductViewSerializer(pv, context={"request": request})
        return Response(serializer.data)

    def put(self, request, id):
        pv = get_object_or_404(ProductView, id=id)
        serializer = ProductViewCreateSerializer(pv, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        pv = get_object_or_404(ProductView, id=id)
        pv.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductViewsByProductView(APIView):
    """List all views for a specific product."""
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        views = ProductView.objects.filter(
            product_id=product_id
        ).prefetch_related("print_areas").order_by("ordering")
        serializer = ProductViewSerializer(
            views, many=True, context={"request": request}
        )
        return Response(serializer.data)


# ──────────────────────────────────────────────
# Print Areas
# ──────────────────────────────────────────────

class PrintAreaListView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        areas = PrintArea.objects.all()
        view_id = request.query_params.get("view")
        if view_id:
            areas = areas.filter(product_view_id=view_id)
        serializer = PrintAreaSerializer(areas, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PrintAreaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PrintAreaDetailView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, id):
        area = get_object_or_404(PrintArea, id=id)
        serializer = PrintAreaSerializer(area)
        return Response(serializer.data)

    def put(self, request, id):
        area = get_object_or_404(PrintArea, id=id)
        serializer = PrintAreaSerializer(area, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        area = get_object_or_404(PrintArea, id=id)
        area.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Design Uploads
# ──────────────────────────────────────────────

class DesignUploadListView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    # Public "try it" flow: anonymous users may upload a design to preview.
    # User is recorded when authenticated; anonymous uploads have user=None.
    # Abuse is bounded by the configured AnonRateThrottle.
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_staff:
            uploads = DesignUpload.objects.all()
        elif request.user.is_authenticated:
            uploads = DesignUpload.objects.filter(user=request.user)
        else:
            return Response([])
        serializer = DesignUploadSerializer(
            uploads, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request):
        """Upload a design with validation."""
        image_file = request.FILES.get("image")
        if not image_file:
            return Response(
                {"error": "No image file provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate image
        validation = validate_image(image_file)
        if not validation["valid"]:
            return Response(
                {"error": validation["error"]},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DesignUploadSerializer(data=request.data)
        if serializer.is_valid():
            upload = serializer.save(
                user=request.user if request.user.is_authenticated else None,
                original_filename=image_file.name,
                file_size=validation["file_size"],
                width=validation["width"],
                height=validation["height"],
                mime_type=validation["mime_type"],
                status="completed",
            )

            # Generate thumbnail async
            try:
                from .tasks import generate_thumbnail_task
                generate_thumbnail_task.delay(str(upload.image))
            except Exception:
                pass  # Non-critical: thumbnail generation can fail silently

            return Response(
                DesignUploadSerializer(upload, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DesignUploadDetailView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, id):
        upload = get_object_or_404(DesignUpload, id=id)
        serializer = DesignUploadSerializer(
            upload, context={"request": request}
        )
        return Response(serializer.data)

    def put(self, request, id):
        upload = get_object_or_404(DesignUpload, id=id)
        serializer = DesignUploadSerializer(upload, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        upload = get_object_or_404(DesignUpload, id=id)
        upload.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Customization Jobs
# ──────────────────────────────────────────────

class CustomizationJobListView(APIView):
    # Public "try it" flow: anonymous users may create a customization to
    # preview a design on a product. Listing returns only the caller's own
    # jobs (or all, for staff); anonymous listing returns an empty set.
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_staff:
            jobs = CustomizationJob.objects.all()
        elif request.user.is_authenticated:
            jobs = CustomizationJob.objects.filter(user=request.user)
        else:
            return Response([])

        status_filter = request.query_params.get("status")
        if status_filter:
            jobs = jobs.filter(status=status_filter)

        jobs = jobs.select_related("design", "product_view__product")

        # Pagination
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        start = (page - 1) * page_size
        total = jobs.count()

        serializer = CustomizationJobSerializer(
            jobs[start:start + page_size], many=True,
            context={"request": request},
        )
        return Response({
            "count": total,
            "page": page,
            "results": serializer.data,
        })

    def post(self, request):
        """Create a customization job and trigger async preview generation."""
        serializer = CustomizationJobSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save(
                user=request.user if request.user.is_authenticated else None,
            )

            # Trigger async rendering
            try:
                from .tasks import generate_preview_task
                generate_preview_task.delay(job.id)
            except Exception:
                # Fallback: synchronous rendering if Celery unavailable
                from .services.renderer import generate_preview
                generate_preview(job.id)
                job.refresh_from_db()

            return Response(
                CustomizationJobSerializer(job, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomizationJobDetailView(APIView):
    # Public "try it" flow: polling (GET) and settings updates (PATCH) must
    # work for anonymous sessions that created the job.
    permission_classes = [AllowAny]

    def get(self, request, id):
        job = get_object_or_404(
            CustomizationJob.objects.select_related(
                "design", "product_view"
            ).prefetch_related("versions", "render_jobs"),
            id=id
        )
        serializer = CustomizationJobDetailSerializer(
            job, context={"request": request}
        )
        return Response(serializer.data)

    def put(self, request, id):
        job = get_object_or_404(CustomizationJob, id=id)
        serializer = CustomizationJobSerializer(job, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        """Update design settings and optionally re-render."""
        job = get_object_or_404(CustomizationJob, id=id)
        serializer = CustomizationJobSerializer(
            job, data=request.data, partial=True
        )
        if serializer.is_valid():
            job = serializer.save()

            # If design_settings changed, save a version and re-render
            if "design_settings" in request.data:
                # Save version
                version_count = job.versions.count()
                CustomizationVersion.objects.create(
                    job=job,
                    version_number=version_count + 1,
                    design_settings=job.design_settings,
                )

                # Re-render preview
                try:
                    from .tasks import generate_preview_task
                    job.status = "pending"
                    job.save(update_fields=["status"])
                    generate_preview_task.delay(job.id)
                except Exception:
                    from .services.renderer import generate_preview
                    generate_preview(job.id)
                    job.refresh_from_db()

            return Response(CustomizationJobSerializer(
                job, context={"request": request}
            ).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        job = get_object_or_404(CustomizationJob, id=id)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Render Jobs
# ──────────────────────────────────────────────

class RenderJobStartView(APIView):
    """Start a new render job for a customization."""
    permission_classes = [AllowAny]

    def post(self, request, job_id):
        """Start a render (preview or final) for a customization job."""
        customization = get_object_or_404(CustomizationJob, id=job_id)
        render_type = request.data.get("render_type", "preview")
        quality = request.data.get("quality", 85)

        render_job = RenderJob.objects.create(
            customization=customization,
            render_type=render_type,
            quality=quality,
        )

        # Dispatch to Celery
        try:
            from .tasks import generate_final_render_task
            generate_final_render_task.delay(render_job.id)
        except Exception:
            from .services.renderer import run_render_job
            run_render_job(render_job.id)
            render_job.refresh_from_db()

        serializer = RenderJobSerializer(render_job, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RenderJobStatusView(APIView):
    """Check render job status (polling endpoint)."""

    def get(self, request, id):
        render_job = get_object_or_404(RenderJob, id=id)
        serializer = RenderJobSerializer(render_job, context={"request": request})
        return Response(serializer.data)


class RenderJobDownloadView(APIView):
    """Get the download URL for a completed render."""

    def get(self, request, id):
        render_job = get_object_or_404(RenderJob, id=id)
        if render_job.status != "completed" or not render_job.output_image:
            return Response(
                {"error": "Render not yet completed."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            "download_url": request.build_absolute_uri(
                render_job.output_image.url
            ),
            "render_metadata": render_job.render_metadata,
        })


# ──────────────────────────────────────────────
# Customization Versions
# ──────────────────────────────────────────────

class CustomizationVersionListView(APIView):
    """List and restore versions for a customization job."""

    def get(self, request, job_id):
        job = get_object_or_404(CustomizationJob, id=job_id)
        versions = job.versions.all()
        serializer = CustomizationVersionSerializer(versions, many=True)
        return Response(serializer.data)

    def post(self, request, job_id):
        """Restore a specific version."""
        job = get_object_or_404(CustomizationJob, id=job_id)
        version_number = request.data.get("version_number")
        if not version_number:
            return Response(
                {"error": "version_number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        version = get_object_or_404(
            CustomizationVersion, job=job, version_number=version_number
        )

        # Restore design settings from version
        job.design_settings = version.design_settings
        job.status = "pending"
        job.save(update_fields=["design_settings", "status"])

        # Re-render
        try:
            from .tasks import generate_preview_task
            generate_preview_task.delay(job.id)
        except Exception:
            from .services.renderer import generate_preview
            generate_preview(job.id)
            job.refresh_from_db()

        return Response(CustomizationJobSerializer(job).data)


# ──────────────────────────────────────────────
# Sharing
# ──────────────────────────────────────────────

class ShareCustomizationView(APIView):
    """Get a public share link for a customization."""

    def get(self, request, share_token):
        """View a shared customization."""
        job = get_object_or_404(
            CustomizationJob.objects.select_related(
                "design", "product_view__product"
            ),
            share_token=share_token, is_public=True
        )
        serializer = CustomizationJobDetailSerializer(job)
        return Response(serializer.data)

    def post(self, request, job_id=None):
        """Toggle public sharing for a customization."""
        if not job_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        job = get_object_or_404(CustomizationJob, id=job_id)
        job.is_public = not job.is_public
        job.save(update_fields=["is_public"])
        return Response({
            "is_public": job.is_public,
            "share_token": str(job.share_token),
            "share_url": request.build_absolute_uri(
                f"/api/products/share/{job.share_token}/"
            ) if job.is_public else None,
        })


# ──────────────────────────────────────────────
# Admin Analytics
# ──────────────────────────────────────────────

class AdminAnalyticsView(APIView):
    """Dashboard analytics for admin users."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)

        # Total counts
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        total_renders = RenderJob.objects.count()
        total_customizations = CustomizationJob.objects.count()

        # Recent activity
        recent_renders = RenderJob.objects.filter(
            queued_at__gte=last_7_days
        ).count()

        # Render status breakdown
        render_statuses = dict(
            RenderJob.objects.values_list("status").annotate(
                count=Count("id")
            ).values_list("status", "count")
        )

        # Average render time (completed renders)
        completed_renders = RenderJob.objects.filter(
            status="completed",
            started_at__isnull=False,
            completed_at__isnull=False,
        )
        avg_render_time = None
        if completed_renders.exists():
            times = []
            for r in completed_renders[:100]:
                delta = (r.completed_at - r.started_at).total_seconds()
                times.append(delta)
            avg_render_time = sum(times) / len(times) if times else None

        # Most customized products
        popular_products = (
            Product.objects.annotate(
                customization_count=Count("views__customization_jobs")
            )
            .order_by("-customization_count")[:10]
            .values("id", "name", "customization_count")
        )

        # Upload stats
        total_uploads = DesignUpload.objects.count()
        recent_uploads = DesignUpload.objects.filter(
            uploaded_at__gte=last_7_days
        ).count()

        return Response({
            "products": {
                "total": total_products,
                "active": active_products,
            },
            "renders": {
                "total": total_renders,
                "recent_7d": recent_renders,
                "by_status": render_statuses,
                "avg_time_seconds": round(avg_render_time, 2) if avg_render_time else None,
            },
            "customizations": {
                "total": total_customizations,
            },
            "uploads": {
                "total": total_uploads,
                "recent_7d": recent_uploads,
            },
            "popular_products": list(popular_products),
        })


# ──────────────────────────────────────────────
# Assets
# ──────────────────────────────────────────────

class AssetListView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        assets = Asset.objects.all()
        asset_type = request.query_params.get("type")
        if asset_type:
            assets = assets.filter(asset_type=asset_type)
        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AssetSerializer(data=request.data)
        if serializer.is_valid():
            asset_file = request.FILES.get("file")
            extra = {}
            if asset_file:
                extra["file_size"] = asset_file.size
                extra["mime_type"] = asset_file.content_type or ""
                # Try to get dimensions
                dims = get_image_dimensions(asset_file)
                if dims:
                    extra["width"], extra["height"] = dims
            serializer.save(**extra)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssetDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, id):
        asset = get_object_or_404(Asset, id=id)
        serializer = AssetSerializer(asset)
        return Response(serializer.data)

    def delete(self, request, id):
        asset = get_object_or_404(Asset, id=id)
        asset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
