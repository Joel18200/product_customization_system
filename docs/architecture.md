# Product Customization System — Architecture

## System Overview

A high-performance platform for uploading artwork and visualizing it on real products with realistic fabric rendering.

```
┌──────────────────────────────────────────────────────────────┐
│                         Nginx (Port 80)                       │
│   Reverse proxy, static/media serving, gzip, caching         │
├──────────────────────┬───────────────────────────────────────┤
│   Frontend (3000)    │         Backend (8000)                 │
│   Next.js 15         │         Django + DRF                  │
│   React + TypeScript │         Gunicorn (4 workers)          │
│   TanStack Query     │              │                        │
│   Zustand            │     ┌────────┴────────┐              │
│   Tailwind CSS       │     │                 │              │
│                      │   Celery Worker    Celery Beat       │
│                      │   (4 concurrent)  (scheduler)        │
├──────────────────────┼────────┬──────────────────────────────┤
│                      │  PostgreSQL 16  │    Redis 7          │
│                      │  (main DB)      │  (cache + broker)   │
└──────────────────────┴────────────────┴──────────────────────┘
```

## Rendering Pipeline

```
User Upload → Validation → Print Area Placement → Perspective Transform
                                                        ↓
                                         Fabric Displacement Mapping
                                                        ↓
                                           Realistic Blending
                                                        ↓
                                              Output Image
```

### Stage Details

1. **Validation**: File size, type, dimensions check
2. **Placement**: Scale to fit print area, preserve aspect ratio, apply user transforms
3. **Perspective**: Canny edge detection → contour analysis → homography warp
4. **Displacement**: Sobel gradients → displacement map → cv2.remap
5. **Blending**: Multiply (shadows) + Overlay (highlights) + texture preservation

## Key Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 15 | SSR, routing, React framework |
| State | Zustand | Client state management |
| Server State | TanStack Query | API caching, polling, mutations |
| API | Django REST Framework | REST API with JWT auth |
| Background | Celery + Redis | Async rendering, cleanup tasks |
| Rendering | OpenCV + NumPy | Image processing pipeline |
| Database | PostgreSQL | Data persistence |
| Cache | Redis | Render result caching |
| Proxy | Nginx | Reverse proxy, static serving |
| Deploy | Docker Compose | Multi-service orchestration |
