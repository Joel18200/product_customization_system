"""
Setup script: Downloads/generates product images, configures print areas.
Run with: python manage.py shell < setup_products.py
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
from products.models import Product, ProductView, PrintArea

MEDIA_ROOT = Path('media')
VIEWS_DIR = MEDIA_ROOT / 'product_views'
VIEWS_DIR.mkdir(parents=True, exist_ok=True)


def create_tshirt_image(color, filename, size=(800, 900)):
    """Generate a realistic-looking t-shirt mockup image."""
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)
    w, h = size

    # Body shape
    body_color = tuple(max(0, c - 15) for c in color)
    # Collar
    draw.ellipse([w*0.3, h*0.02, w*0.7, h*0.12], fill=body_color)
    # Neck hole
    neck_color = tuple(max(0, c - 40) for c in color)
    draw.ellipse([w*0.38, h*0.01, w*0.62, h*0.09], fill=neck_color)

    # Sleeves shadow
    sleeve_shadow = tuple(max(0, c - 25) for c in color)
    draw.polygon([(w*0.05, h*0.1), (w*0.0, h*0.35), (w*0.15, h*0.35), (w*0.25, h*0.15)], fill=sleeve_shadow)
    draw.polygon([(w*0.95, h*0.1), (w*1.0, h*0.35), (w*0.85, h*0.35), (w*0.75, h*0.15)], fill=sleeve_shadow)

    # Fabric wrinkle lines (subtle darker lines)
    wrinkle_color = tuple(max(0, c - 10) for c in color)
    for i in range(8):
        y = h * 0.15 + (h * 0.7 * i / 8)
        # Slight curve
        points = []
        for x_step in range(20):
            x = w * 0.2 + (w * 0.6 * x_step / 20)
            y_off = np.sin(x_step * 0.8) * 3 + np.sin(x_step * 0.3) * 5
            points.append((x, y + y_off))
        if len(points) > 1:
            draw.line(points, fill=wrinkle_color, width=1)

    # Side seam lines
    seam_color = tuple(max(0, c - 20) for c in color)
    draw.line([(w*0.2, h*0.15), (w*0.18, h*0.95)], fill=seam_color, width=2)
    draw.line([(w*0.8, h*0.15), (w*0.82, h*0.95)], fill=seam_color, width=2)

    # Bottom hem
    draw.rectangle([w*0.15, h*0.93, w*0.85, h*0.96], fill=body_color)

    # Add slight noise for fabric texture
    arr = np.array(img)
    noise = np.random.randint(-8, 8, arr.shape, dtype=np.int16)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    # Soften slightly
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    filepath = VIEWS_DIR / filename
    img.save(filepath, 'JPEG', quality=92)
    return f'product_views/{filename}'


def create_hoodie_image(color, filename, size=(800, 950)):
    """Generate a hoodie mockup."""
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)
    w, h = size

    body_color = tuple(max(0, c - 15) for c in color)

    # Hood
    hood_color = tuple(max(0, c - 20) for c in color)
    draw.arc([w*0.25, h*-0.05, w*0.75, h*0.15], 0, 180, fill=hood_color, width=4)
    draw.rectangle([w*0.28, h*0.0, w*0.72, h*0.08], fill=hood_color)

    # Collar/hood opening
    neck_color = tuple(max(0, c - 45) for c in color)
    draw.polygon([(w*0.4, h*0.06), (w*0.5, h*0.12), (w*0.6, h*0.06)], fill=neck_color)

    # Kangaroo pocket
    pocket_color = tuple(max(0, c - 18) for c in color)
    draw.rounded_rectangle([w*0.28, h*0.55, w*0.72, h*0.72], radius=15, fill=pocket_color)
    draw.line([(w*0.5, h*0.55), (w*0.5, h*0.72)], fill=tuple(max(0, c-30) for c in color), width=2)

    # Drawstrings
    draw.line([(w*0.43, h*0.08), (w*0.43, h*0.25)], fill=(200, 200, 200), width=2)
    draw.line([(w*0.57, h*0.08), (w*0.57, h*0.25)], fill=(200, 200, 200), width=2)

    # Wrinkles
    wrinkle_color = tuple(max(0, c - 10) for c in color)
    for i in range(6):
        y = h * 0.12 + (h * 0.4 * i / 6)
        points = [(w*0.25 + w*0.5*x/15, y + np.sin(x*0.7)*4) for x in range(15)]
        draw.line(points, fill=wrinkle_color, width=1)

    # Side seams
    seam = tuple(max(0, c - 22) for c in color)
    draw.line([(w*0.2, h*0.1), (w*0.18, h*0.95)], fill=seam, width=2)
    draw.line([(w*0.8, h*0.1), (w*0.82, h*0.95)], fill=seam, width=2)

    # Fabric texture
    arr = np.array(img)
    noise = np.random.randint(-6, 6, arr.shape, dtype=np.int16)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    filepath = VIEWS_DIR / filename
    img.save(filepath, 'JPEG', quality=92)
    return f'product_views/{filename}'


def create_cap_image(color, filename, size=(800, 600)):
    """Generate a cap/hat mockup."""
    img = Image.new('RGB', size, (30, 30, 40))
    draw = ImageDraw.Draw(img)
    w, h = size

    # Brim
    brim_color = tuple(max(0, c - 20) for c in color)
    draw.ellipse([w*0.1, h*0.55, w*0.75, h*0.85], fill=brim_color)

    # Crown
    draw.ellipse([w*0.15, h*0.1, w*0.85, h*0.65], fill=color)

    # Panel lines
    panel_color = tuple(max(0, c - 15) for c in color)
    draw.line([(w*0.5, h*0.1), (w*0.5, h*0.55)], fill=panel_color, width=2)
    draw.line([(w*0.3, h*0.2), (w*0.25, h*0.55)], fill=panel_color, width=1)
    draw.line([(w*0.7, h*0.2), (w*0.75, h*0.55)], fill=panel_color, width=1)

    # Button on top
    draw.ellipse([w*0.47, h*0.08, w*0.53, h*0.14], fill=brim_color)

    # Fabric texture
    arr = np.array(img)
    noise = np.random.randint(-5, 5, arr.shape, dtype=np.int16)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    filepath = VIEWS_DIR / filename
    img.save(filepath, 'JPEG', quality=92)
    return f'product_views/{filename}'


# ═══════════════════════════════════════
# Generate images and configure products
# ═══════════════════════════════════════

products = Product.objects.all()
print(f"Found {products.count()} products")

product_configs = {
    'classic-black-tshirt': {
        'color': (35, 35, 40),
        'type': 'tshirt',
        'views': [
            ('Front View', 'front', 'black_tshirt_front.jpg'),
            ('Back View', 'back', 'black_tshirt_back.jpg'),
        ],
        'print_area': {'x': 200, 'y': 180, 'width': 400, 'height': 450, 'label': 'Chest'},
    },
    'forest-green-tshirt': {
        'color': (34, 85, 52),
        'type': 'tshirt',
        'views': [
            ('Front View', 'front', 'green_tshirt_front.jpg'),
            ('Back View', 'back', 'green_tshirt_back.jpg'),
        ],
        'print_area': {'x': 200, 'y': 180, 'width': 400, 'height': 450, 'label': 'Chest'},
    },
    'white-crew-neck-tshirt': {
        'color': (230, 230, 235),
        'type': 'tshirt',
        'views': [
            ('Front View', 'front', 'white_tshirt_front.jpg'),
            ('Back View', 'back', 'white_tshirt_back.jpg'),
        ],
        'print_area': {'x': 200, 'y': 180, 'width': 400, 'height': 450, 'label': 'Chest'},
    },
    'black-pullover-hoodie': {
        'color': (30, 30, 35),
        'type': 'hoodie',
        'views': [
            ('Front View', 'front', 'black_hoodie_front.jpg'),
            ('Back View', 'back', 'black_hoodie_back.jpg'),
        ],
        'print_area': {'x': 200, 'y': 130, 'width': 400, 'height': 350, 'label': 'Chest'},
    },
    'khaki-baseball-cap': {
        'color': (180, 160, 120),
        'type': 'cap',
        'views': [
            ('Front View', 'front', 'khaki_cap_front.jpg'),
            ('Side View', 'side', 'khaki_cap_side.jpg'),
        ],
        'print_area': {'x': 200, 'y': 120, 'width': 400, 'height': 300, 'label': 'Front Panel'},
    },
}

for product in products:
    config = product_configs.get(product.slug)
    if not config:
        print(f"  Skipping {product.slug} (no config)")
        continue

    print(f"\n  Setting up: {product.name} ({product.slug})")

    # Delete existing views
    product.views.all().delete()

    # Create views and print areas
    for i, (view_name, view_type, filename) in enumerate(config['views']):
        # Generate image
        if config['type'] == 'tshirt':
            img_path = create_tshirt_image(config['color'], filename)
        elif config['type'] == 'hoodie':
            img_path = create_hoodie_image(config['color'], filename)
        elif config['type'] == 'cap':
            img_path = create_cap_image(config['color'], filename)

        view = ProductView.objects.create(
            product=product,
            view_name=view_name,
            view_type=view_type,
            image=img_path,
            ordering=i,
        )
        print(f"    ✓ Created view: {view_name} → {img_path}")

        # Add print area to front view
        if view_type == 'front':
            pa = config['print_area']
            PrintArea.objects.create(
                product_view=view,
                label=pa['label'],
                x=pa['x'],
                y=pa['y'],
                width=pa['width'],
                height=pa['height'],
                max_dpi=300,
                is_default=True,
            )
            print(f"    ✓ Created print area: {pa['label']} ({pa['width']}×{pa['height']})")

print("\n✅ All products configured with images and print areas!")
