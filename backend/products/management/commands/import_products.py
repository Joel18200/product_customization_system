"""
Import products, views, and print areas from the supplier product sheet
(Product Data.xlsx).

Each row in the sheet describes one product *view*: a base image (``croped_image``)
plus a decoration/print area defined by pixel coordinates
(Decoration Start Left/Top = x/y, Max Decoration Width/Height = width/height)
that are measured against that same croped image.

Images can be pulled two ways:
  * Online  — downloaded from the S3 URLs in the sheet (default).
  * Offline — read from a local folder via --source-dir, matched by the
              URL's filename (e.g. 18500_black_conf_front.jpg).

Usage:
  python manage.py import_products                 # download from S3, replace existing
  python manage.py import_products --source-dir ../product_images   # use local files
  python manage.py import_products --dry-run       # show plan, touch nothing
  python manage.py import_products --keep-existing # add without deleting current products

The command is idempotent on slug: re-running updates products in place.
"""
import os
import io
import urllib.request

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from products.models import Category, Product, ProductView, PrintArea

S3_BASE = "https://s3-us-west-2.amazonaws.com/salesonepro-supplier/media/products/"

# Category slug -> display name
CATEGORIES = {
    "t-shirts": "T-Shirts",
    "hoodies": "Hoodies",
    "caps-hats": "Caps & Hats",
}

# view_type normalisation (sheet "type" -> model view_type)
VIEW_TYPE_MAP = {
    "front": "front",
    "back": "back",
    "side_left": "left",
    "side_right": "right",
}

# ── Product data transcribed from Product Data.xlsx ──
# Each view: (image_type, code, sheet_type, max_h, max_w, top, left, croped_path)
PRODUCTS = [
    {
        "identifier": "18500",
        "title": "Gildan Heavy Blend Hooded Sweatshirt (18500)",
        "category": "hoodies",
        "views": [
            ("Flat - Full Front (A4)", "A4", "front", 716, 545, 590, 346,
             "sanmar/18500/18500_black_conf_front.jpg"),
            ("Flat - Full Back (A6)", "A6", "back", 778, 550, 508, 320,
             "sanmar/18500/18500_black_conf_back.jpg"),
        ],
    },
    {
        "identifier": "19-061",
        "title": "OTTO CAP 6 Panel Low Profile Baseball Cap (19-061)",
        "category": "caps-hats",
        "views": [
            ("Cap - Front Center (1)", "1", "front", 143, 240, 87, 158,
             "otto/19-061/19-061_032_conf_front.jpg"),
            ("Cap - Upper Back Center (8)", "8", "back", 46, 257, 115, 150,
             "otto/19-061/19-061_003_conf_back.jpg"),
            ("Cap - Left Side (18)", "18", "side_left", 441, 532, 1063, 1317,
             "product_media/otto/19-061/05e9f4.jpg"),
            ("Cap - Right Side (19)", "19", "side_right", 427, 557, 1073, 582,
             "product_media/otto/19-061/fa96a6.jpg"),
        ],
    },
    {
        "identifier": "2000",
        "title": "Gildan Ultra Cotton 100% Cotton T-Shirt (2000)",
        "category": "t-shirts",
        "views": [
            ("Flat - Full Front (A4)", "A4", "front", 755, 629, 990, 713,
             "sanmar/2000/703604_conf_7740e_front.jpg"),
            ("Flat - Full Back (A6)", "A6", "back", 1156, 723, 935, 621,
             "sanmar/2000/703555-back.jpg"),
        ],
    },
    {
        "identifier": "31-069",
        "title": "OTTO CAP 5 Panel Mid Profile Baseball Cap (31-069)",
        "category": "caps-hats",
        "views": [
            ("Cap - Front Center (1)", "1", "front", 852, 1563, 544, 410,
             "product_media/otto/31-069/e19ffe.jpg"),
            ("Cap - Upper Back Center (8)", "8", "back", 749, 1253, 858, 570,
             "product_media/otto/31-069/3b8ab8.jpg"),
            ("Cap - Left Side (18)", "18", "side_left", 403, 424, 1037, 1325,
             "product_media/otto/31-069/27f3ec.jpg"),
            ("Cap - Right Side (19)", "19", "side_right", 455, 419, 974, 683,
             "product_media/otto/31-069/31-069-009-RS.jpg"),
        ],
    },
    {
        "identifier": "39-165",
        "title": "Polyester Foam Front High Crown Golf Style Mesh Back Cap (39-165)",
        "category": "caps-hats",
        "views": [
            ("Cap - Front Center (1)", "1", "front", 726, 1330, 623, 575,
             "product_media/otto/39-165/ee1aa5.jpg"),
        ],
    },
    {
        "identifier": "5000",
        "title": "Gildan Heavy Cotton 100% Cotton T-Shirt (5000)",
        "category": "t-shirts",
        "views": [
            ("Flat - Full Front (A4)", "A4", "front", 1166, 872, 1036, 585,
             "sanmar/5000/260182_conf_98bc7_front.jpg"),
            ("Flat - Full Back (A6)", "A6", "back", 775, 535, 549, 327,
             "sanmar/5000/5000_orange_conf_back.jpg"),
        ],
    },
    {
        "identifier": "60-662",
        "title": "OTTO CAP Sun Visor (60-662)",
        "category": "caps-hats",
        "views": [
            ("Cap - Front Center (1)", "1", "front", 95, 310, 76, 124,
             "otto/60-662/60-662_003_conf_front.jpg"),
            ("Cap - Left Side (18)", "18", "side_left", 201, 619, 1083, 1240,
             "product_media/otto/60-662/7211a8.jpg"),
            ("Cap - Right Side (19)", "19", "side_right", 197, 580, 1083, 577,
             "product_media/otto/60-662/bc33ca.jpg"),
        ],
    },
    {
        "identifier": "82-480",
        "title": "Superior Cotton Knit Beanie 12\" (82-480)",
        "category": "caps-hats",
        "views": [
            ("Cap - Front Center (1)", "1", "front", 105, 200, 260, 175,
             "otto/82-480/82-480_002_conf_front.jpg"),
            ("Cap - Upper Back Center (8)", "8", "back", 105, 200, 260, 175,
             "otto/82-480/82-480_002_conf_back.jpg"),
        ],
    },
    {
        "identifier": "YST350",
        "title": "Sport-Tek Youth PosiCharge Competitor Tee (YST350)",
        "category": "t-shirts",
        "views": [
            ("Flat - Full Front (A4)", "A4", "front", 698, 489, 705, 354,
             "sanmar/yst350/yst350_purple_conf_front.jpg"),
            ("Flat - Full Back (A6)", "A6", "back", 828, 482, 599, 349,
             "sanmar/yst350/yst350_deeporange_conf_back.jpg"),
        ],
    },
]


class Command(BaseCommand):
    help = "Import products/views/print-areas from the supplier sheet (Product Data.xlsx)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir",
            help="Local folder of images (matched by URL filename). "
                 "If omitted, images are downloaded from S3.",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Show what would happen without writing anything.",
        )
        parser.add_argument(
            "--keep-existing", action="store_true",
            help="Do not delete current products before importing.",
        )

    # ── image loading ──────────────────────────────────────────────
    def _load_image_bytes(self, croped_path, source_dir):
        """Return (filename, bytes) for a view image, or (filename, None) on failure."""
        filename = os.path.basename(croped_path)
        if source_dir:
            local = os.path.join(source_dir, filename)
            if os.path.exists(local):
                with open(local, "rb") as f:
                    return filename, f.read()
            return filename, None
        # Download from S3
        url = S3_BASE + croped_path
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=30).read()
            return filename, data
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(self.style.WARNING(f"    ! download failed: {url} ({exc})"))
            return filename, None

    def _validate_area(self, img_bytes, left, top, width, height, label):
        """Warn if the print area falls outside the image bounds."""
        try:
            from PIL import Image
            iw, ih = Image.open(io.BytesIO(img_bytes)).size
        except Exception:
            return
        if left + width > iw or top + height > ih:
            self.stderr.write(self.style.WARNING(
                f"    ! print area '{label}' ({left},{top},{width},{height}) "
                f"exceeds image {iw}x{ih} — check coordinates."
            ))

    # ── main ───────────────────────────────────────────────────────
    def handle(self, *args, **opts):
        source_dir = opts.get("source_dir")
        dry = opts.get("dry_run")
        keep = opts.get("keep_existing")

        if source_dir and not os.path.isdir(source_dir):
            self.stderr.write(self.style.ERROR(f"source-dir not found: {source_dir}"))
            return

        mode = f"local folder '{source_dir}'" if source_dir else "S3 download"
        self.stdout.write(f"Importing {len(PRODUCTS)} products (images via {mode})"
                          + (" [DRY RUN]" if dry else ""))

        if dry:
            for p in PRODUCTS:
                self.stdout.write(f"  {p['identifier']}: {p['title']} "
                                  f"[{p['category']}] — {len(p['views'])} views")
            self.stdout.write("Dry run complete. Nothing written.")
            return

        with transaction.atomic():
            # Categories
            cats = {}
            for slug, name in CATEGORIES.items():
                cat, _ = Category.objects.get_or_create(
                    slug=slug, defaults={"name": name}
                )
                cats[slug] = cat

            if not keep:
                deleted = Product.objects.count()
                Product.objects.all().delete()
                self.stdout.write(f"  Removed {deleted} existing products.")

            created_p = created_v = created_a = failed = 0

            for p in PRODUCTS:
                slug = slugify(p["identifier"])
                product, _ = Product.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "name": p["title"],
                        "category": cats[p["category"]],
                        "sku": p["identifier"],
                        "is_active": True,
                        "description": p["title"],
                    },
                )
                created_p += 1
                product.views.all().delete()  # rebuild views cleanly
                self.stdout.write(f"  {p['identifier']}: {p['title']}")

                for i, (itype, code, stype, mh, mw, top, left, cpath) in enumerate(p["views"]):
                    filename, data = self._load_image_bytes(cpath, source_dir)
                    if not data:
                        failed += 1
                        continue

                    view = ProductView(
                        product=product,
                        view_name=itype,
                        view_type=VIEW_TYPE_MAP.get(stype, "custom"),
                        ordering=i,
                    )
                    # store under a stable, collision-free name
                    stored = f"{p['identifier']}_{code}_{stype}_{filename}"
                    view.image.save(stored, ContentFile(data), save=False)
                    view.save()
                    created_v += 1

                    self._validate_area(data, left, top, mw, mh, itype)
                    PrintArea.objects.create(
                        product_view=view,
                        label=f"{itype} ({code})",
                        x=left, y=top, width=mw, height=mh,
                        max_dpi=300, is_default=True,
                    )
                    created_a += 1
                    self.stdout.write(f"    + {itype} -> {stored}")

            self.stdout.write(self.style.SUCCESS(
                f"\nDone. Products: {created_p}, views: {created_v}, "
                f"print areas: {created_a}, image failures: {failed}."
            ))
            if failed:
                self.stderr.write(self.style.WARNING(
                    "Some images could not be fetched. Re-run with internet access "
                    "or supply them via --source-dir."
                ))
