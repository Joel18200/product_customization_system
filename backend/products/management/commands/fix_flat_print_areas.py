"""
Correct print-area placement for FLAT garments (t-shirts, hoodies) only.

The supplier sheet's decoration coordinates for apparel were defined against
the original raw photos, not the conf/croped images we store, so they land
near the bottom hem (and often overflow the image). Caps use their own hi-res
source where the coordinates match, so cap/visor/beanie areas are left alone.

This recomputes each flat garment view's print area as a chest/upper-back
region expressed as a fraction of that view's actual stored image, so it sits
correctly regardless of image dimensions.

Usage: python manage.py fix_flat_print_areas
"""
from django.core.management.base import BaseCommand
from PIL import Image

from products.models import ProductView

# Chest / upper-back region as (left, top, width, height) fractions.
FLAT_FRACTIONS = {
    "front": (0.30, 0.26, 0.40, 0.40),   # chest, below the collar
    "back": (0.30, 0.22, 0.40, 0.46),    # upper/mid back
    "custom": (0.30, 0.28, 0.40, 0.40),
}


def _is_cap(view) -> str:
    name = f"{view.product.name} {view.view_name}".lower()
    return any(w in name for w in ("cap", "visor", "beanie", "hat"))


class Command(BaseCommand):
    help = "Recompute chest/back print areas for flat garments (leaves caps untouched)."

    def handle(self, *args, **options):
        updated = skipped_cap = skipped_nopa = 0

        for view in ProductView.objects.select_related("product").all():
            if _is_cap(view):
                skipped_cap += 1
                continue
            pa = view.print_areas.first()
            if not pa:
                skipped_nopa += 1
                continue
            try:
                iw, ih = Image.open(view.image.path).size
            except Exception as exc:
                self.stderr.write(self.style.WARNING(
                    f"  ! {view.product.sku} {view.view_type}: cannot read image ({exc})"
                ))
                continue

            fx, fy, fw, fh = FLAT_FRACTIONS.get(view.view_type, FLAT_FRACTIONS["custom"])
            pa.x = int(iw * fx)
            pa.y = int(ih * fy)
            pa.width = int(iw * fw)
            pa.height = int(ih * fh)
            pa.save(update_fields=["x", "y", "width", "height"])
            updated += 1
            self.stdout.write(
                f"  {view.product.sku:8s} {view.view_type:6s} img={iw}x{ih} "
                f"-> x={pa.x} y={pa.y} w={pa.width} h={pa.height}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Updated {updated} flat-garment areas; "
            f"left {skipped_cap} cap areas untouched; {skipped_nopa} views had no area."
        ))
