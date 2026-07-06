# API Reference

All endpoints are prefixed with `/api/`.

Interactive documentation available at:
- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **OpenAPI Schema**: `/api/schema/`

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register/` | Register new user |
| POST | `/auth/login/` | JWT token pair |
| POST | `/auth/refresh/` | Refresh access token |
| GET | `/auth/profile/` | Current user profile |
| PATCH | `/auth/profile/` | Update profile |
| GET | `/auth/users/` | List users (admin) |

## Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/` | List products (paginated, searchable) |
| POST | `/products/` | Create product (admin) |
| GET | `/products/<id>/` | Product detail |
| PUT | `/products/<id>/` | Update product (admin) |
| DELETE | `/products/<id>/` | Delete product (admin) |
| GET | `/products/slug/<slug>/` | Product by slug |

### Query Parameters (GET /products/)
- `search` — Full-text search (name, description, SKU)
- `category` — Filter by category ID
- `category_slug` — Filter by category slug
- `min_price` / `max_price` — Price range
- `ordering` — Sort: `name`, `-name`, `base_price`, `-base_price`, `created_at`, `-created_at`
- `page` / `page_size` — Pagination

## Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/categories/` | List categories |
| POST | `/products/categories/` | Create (admin) |
| GET/PUT/DELETE | `/products/categories/<id>/` | CRUD |

## Product Views

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/views/` | List all views |
| POST | `/products/views/` | Create view (admin) |
| GET | `/products/<product_id>/views/` | Views for product |
| GET/PUT/DELETE | `/products/views/<id>/` | CRUD |

## Print Areas

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/print-areas/` | List areas |
| POST | `/products/print-areas/` | Create (admin) |
| GET/PUT/DELETE | `/products/print-areas/<id>/` | CRUD |

## Design Uploads

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/design-uploads/` | List uploads |
| POST | `/products/design-uploads/` | Upload design (multipart) |
| GET/PUT/DELETE | `/products/design-uploads/<id>/` | CRUD |

## Customization Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/customization-jobs/` | List jobs |
| POST | `/products/customization-jobs/` | Create & render |
| GET | `/products/customization-jobs/<id>/` | Job detail |
| PATCH | `/products/customization-jobs/<id>/` | Update settings & re-render |
| DELETE | `/products/customization-jobs/<id>/` | Delete |

## Rendering

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/products/customization-jobs/<id>/render/` | Start render |
| GET | `/products/render-jobs/<id>/status/` | Check status |
| GET | `/products/render-jobs/<id>/download/` | Download URL |

## Versioning

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/customization-jobs/<id>/versions/` | List versions |
| POST | `/products/customization-jobs/<id>/versions/` | Restore version |

## Sharing

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/share/<uuid>/` | View shared |
| POST | `/products/customization-jobs/<id>/share/` | Toggle share |

## Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/admin/analytics/` | Dashboard analytics |
| GET | `/products/assets/` | List assets |
| POST | `/products/assets/` | Upload asset |
