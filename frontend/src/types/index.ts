/**
 * TypeScript interfaces for the Product Customization System.
 */

// ── Categories ──

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  parent: number | null;
  image: string | null;
  ordering: number;
  is_active: boolean;
  product_count: number;
  children: Category[];
}

// ── Products ──

export interface ProductListItem {
  id: number;
  name: string;
  slug: string;
  description: string;
  category: number | null;
  category_name: string | null;
  sku: string;
  base_price: string | null;
  thumbnail: string | null;
  thumbnail_url: string | null;
  is_active: boolean;
  view_count: number;
  created_at: string;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string;
  category: Category | null;
  sku: string;
  base_price: string | null;
  tags: string[];
  thumbnail: string | null;
  is_active: boolean;
  views: ProductViewType[];
  variants: ProductVariant[];
  created_at: string;
  updated_at: string;
}

export interface ProductVariant {
  id: number;
  product: number;
  name: string;
  sku: string;
  color: string;
  size: string;
  price_override: string | null;
  is_active: boolean;
}

// ── Product Views ──

export interface PrintArea {
  id: number;
  product_view: number;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  max_dpi: number;
  is_default: boolean;
}

export interface ProductViewType {
  id: number;
  product: number;
  view_name: string;
  view_type: "front" | "back" | "left" | "right" | "custom";
  image: string;
  image_url: string | null;
  image_width: number | null;
  image_height: number | null;
  rotation_metadata: Record<string, unknown>;
  ordering: number;
  print_areas: PrintArea[];
}

// ── Design Uploads ──

export interface DesignUpload {
  id: number;
  user: number | null;
  image: string;
  original_filename: string;
  file_size: number;
  width: number | null;
  height: number | null;
  mime_type: string;
  thumbnail: string | null;
  thumbnail_url: string | null;
  uploaded_at: string;
  status: "pending" | "processing" | "completed" | "failed";
}

// ── Customization ──

export interface DesignSettings {
  scale?: number;
  rotation?: number;
  offsetX?: number;
  offsetY?: number;
}

export interface CustomizationJob {
  id: number;
  user: number | null;
  design: number | DesignUpload;
  product_view: number | ProductViewType;
  design_settings: DesignSettings;
  output_image: string | null;
  status: "pending" | "processing" | "completed" | "failed";
  share_token: string;
  is_public: boolean;
  versions?: CustomizationVersion[];
  render_jobs?: RenderJob[];
  created_at: string;
  updated_at: string;
}

export interface CustomizationVersion {
  id: number;
  job: number;
  version_number: number;
  design_settings: DesignSettings;
  snapshot_image: string | null;
  created_at: string;
}

// ── Render Jobs ──

export interface RenderJob {
  id: number;
  customization: number;
  render_type: "preview" | "final" | "thumbnail";
  quality: number;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  output_image: string | null;
  render_metadata: Record<string, unknown>;
  error_message: string;
  queued_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration: number | null;
}

// ── API Responses ──

export interface PaginatedResponse<T> {
  count: number;
  page: number;
  page_size?: number;
  total_pages?: number;
  results: T[];
}

export interface AdminAnalytics {
  products: {
    total: number;
    active: number;
  };
  renders: {
    total: number;
    recent_7d: number;
    by_status: Record<string, number>;
    avg_time_seconds: number | null;
  };
  customizations: {
    total: number;
  };
  uploads: {
    total: number;
    recent_7d: number;
  };
  popular_products: Array<{
    id: number;
    name: string;
    customization_count: number;
  }>;
}

// ── Auth ──

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  date_joined: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
}
