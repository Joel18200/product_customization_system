/**
 * TanStack Query hooks for products API.
 */
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Product, ProductListItem, PaginatedResponse, Category } from "@/types";

export function useProducts(params?: {
  page?: number;
  search?: string;
  category?: string;
  ordering?: string;
}) {
  return useQuery({
    queryKey: ["products", params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set("page", String(params.page));
      if (params?.search) searchParams.set("search", params.search);
      if (params?.category) searchParams.set("category_slug", params.category);
      if (params?.ordering) searchParams.set("ordering", params.ordering);
      const { data } = await api.get<PaginatedResponse<ProductListItem>>(
        `/products/?${searchParams.toString()}`
      );
      return data;
    },
  });
}

export function useProduct(id: number | null) {
  return useQuery({
    queryKey: ["product", id],
    queryFn: async () => {
      const { data } = await api.get<Product>(`/products/${id}/`);
      return data;
    },
    enabled: !!id,
  });
}

export function useProductBySlug(slug: string | null) {
  return useQuery({
    queryKey: ["product", "slug", slug],
    queryFn: async () => {
      const { data } = await api.get<Product>(`/products/slug/${slug}/`);
      return data;
    },
    enabled: !!slug,
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: async () => {
      const { data } = await api.get<Category[]>("/products/categories/");
      return data;
    },
  });
}
