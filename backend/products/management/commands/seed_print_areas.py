"""
Management command: ensure every ProductView has at least one PrintArea.

The original seed only created print areas for the "front" view of each
product, so customizing on back/side views failed with
"No print area configured". This command backfills a sensible default
print area for any view that is missing one, sized as a fraction of the
view's actual image dimensions and tuned per view type.

Idempotent: views that already have a print area are left untouched.

Usage: python manage.py seed_print_areas
"""
from django.core.management.base import BaseCommand
from PIL import Image

from products.models import ProductView, PrintArea


# Print area as (left, top, width, height) fractions of the image, per view type.
# Values mirror the reference mockups: chest/back panels are large centered
# rectangles; cap front is a wide central band; cap back is a thin strip.
FRACTIONS = {
    "front": (0.25, 0.20, 0.50, 0.50),
    "back": (0.25, 0.20, 0.50, 0.55),
    "left": (0.30, 0.30, 0.40, 0.30),
    "right": (0.30, 0.30, 0.40, 0.30),
    "custom": (0.30, 0.30, 0.40, 0.40),
}

# Caps use flatter, wider print bands than apparel.
CAP_FRACTIONS = {
    "front": (0.25, 0.22, 0.50, 0.34),
    "back": (0.28, 0.28, 0.44, 0.14),
    "side": (0.30, 0.30, 0.40, 0.20),
    "left": (0.30, 0.30, 0.40, 0.20),
    "right": (0.30, 0.30, 0.40, 0.20),
}


class Command(BaseCommand):
    help = "Backfill a default PrintArea for every ProductView that lacks one."

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        errors = 0

        for view in ProductView.objects.select_related("product").all():
            if view.print_areas.exists():
                skipped += 1
                continue

            try:
                with Image.open(view.image.path) as img:
                    iw, ih = img.size
            except Exception as exc:
                self.stderr.write(
                    self.style.WARNING(
                        f"  ! Could not read image for view {view.id} "
                        f"({view}): {exc}"
                    )
                )
                errors += 1
                continue

            is_cap = "cap" in (view.product.name or "").lower() or \
                "cap" in (view.product.slug or "").lower()
            table = CAP_FRACTIONS if is_cap else FRACTIONS
            fx, fy, fw, fh = table.get(view.view_type, FRACTIONS["custom"])

            label = {
                "front": "Front", "back": "Back",
                "left": "Left Side", "right": "Right Side",
                "side": "Side", "custom": "Main",
            }.get(view.view_type, "Main")

            PrintArea.objects.create(
                product_view=view,
                label=label,
                x=int(iw * fx),
                y=int(ih * fy),
                width=int(iw * fw),
                height=int(ih * fh),
                max_dpi=300,
                is_default=True,
            )
            created += 1
            self.stdout.write(
                f"  + {view.product.name} / {view.view_name} "
                f"({view.view_type}) -> {int(iw*fw)}x{int(ih*fh)}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Created {created}, skipped {skipped} "
                f"(already had areas), errors {errors}."
            )
        )
