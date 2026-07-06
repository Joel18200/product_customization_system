/**
 * Shared utility functions.
 */
import { clsx, type ClassValue } from "clsx";

/**
 * Merge class names with clsx (Tailwind-friendly).
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/**
 * Format price for display.
 */
export function formatPrice(price: string | number | null): string {
  if (price === null || price === undefined) return "N/A";
  const num = typeof price === "string" ? parseFloat(price) : price;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num);
}

/**
 * Format file size for display.
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Format date for display.
 */
export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * Format relative time (e.g., "2 hours ago").
 */
export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return formatDate(dateStr);
}

/**
 * Get full media URL from a path returned by the API.
 *
 * Handles three cases robustly:
 *  - Absolute URLs (http/https) are returned unchanged.
 *  - Root-relative paths ("/media/...") are resolved against the API origin
 *    (so they never get a duplicated "/media/" prefix).
 *  - Bare relative paths ("product_views/x.jpg") are prefixed with the media base.
 */
export function getMediaUrl(path: string | null): string {
  if (!path) return "/placeholder.png";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;

  const mediaBase =
    process.env.NEXT_PUBLIC_MEDIA_URL ||
    (typeof window !== "undefined"
      ? `${window.location.protocol}//${window.location.hostname}:8000/media/`
      : "http://localhost:8000/media/");
  // Origin without the trailing "/media/" segment.
  const origin = mediaBase.replace(/\/media\/?$/, "");

  if (path.startsWith("/")) {
    return `${origin}${path}`;
  }
  return `${mediaBase.replace(/\/$/, "")}/${path}`;
}

/**
 * Download a (possibly cross-origin) file to disk.
 *
 * Uses a blob + object URL so the browser actually saves the file rather than
 * navigating to it (the native `download` attribute is ignored for
 * cross-origin URLs). Falls back to opening in a new tab if the fetch is
 * blocked (e.g. missing CORS headers).
 */
export async function downloadFile(
  url: string,
  filename: string
): Promise<void> {
  try {
    const res = await fetch(url, { mode: "cors" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objectUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(objectUrl);
  } catch {
    window.open(url, "_blank", "noopener,noreferrer");
  }
}

/**
 * Debounce a function call.
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Truncate text with ellipsis.
 */
export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + "...";
}
