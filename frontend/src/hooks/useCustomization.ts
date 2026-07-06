/**
 * TanStack Query hooks for customization API.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { CustomizationJob, RenderJob, DesignUpload } from "@/types";

export function useUploadDesign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("image", file);
      const { data } = await api.post<DesignUpload>(
        "/products/design-uploads/",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["design-uploads"] });
    },
  });
}

export function useCreateCustomization() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      design: number;
      product_view: number;
      design_settings?: Record<string, number>;
    }) => {
      const { data: result } = await api.post<CustomizationJob>(
        "/products/customization-jobs/",
        data
      );
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customizations"] });
    },
  });
}

export function useUpdateCustomization() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      design_settings,
    }: {
      id: number;
      design_settings: Record<string, number>;
    }) => {
      const { data } = await api.patch<CustomizationJob>(
        `/products/customization-jobs/${id}/`,
        { design_settings }
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["customization", data.id],
      });
    },
  });
}

export function useCustomizationJob(id: number | null) {
  return useQuery({
    queryKey: ["customization", id],
    queryFn: async () => {
      const { data } = await api.get<CustomizationJob>(
        `/products/customization-jobs/${id}/`
      );
      return data;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const job = query.state.data;
      if (job && (job.status === "pending" || job.status === "processing")) {
        return 2000; // Poll every 2 seconds while rendering
      }
      return false;
    },
  });
}

export function useStartRender() {
  return useMutation({
    mutationFn: async ({
      jobId,
      renderType = "final",
    }: {
      jobId: number;
      renderType?: string;
    }) => {
      const { data } = await api.post<RenderJob>(
        `/products/customization-jobs/${jobId}/render/`,
        { render_type: renderType }
      );
      return data;
    },
  });
}

export function useRenderJobStatus(id: number | null) {
  return useQuery({
    queryKey: ["render-job", id],
    queryFn: async () => {
      const { data } = await api.get<RenderJob>(
        `/products/render-jobs/${id}/status/`
      );
      return data;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const job = query.state.data;
      if (job && (job.status === "queued" || job.status === "processing")) {
        return 1500;
      }
      return false;
    },
  });
}

export function useMyCustomizations(page = 1) {
  return useQuery({
    queryKey: ["customizations", "mine", page],
    queryFn: async () => {
      const { data } = await api.get(
        `/products/customization-jobs/?page=${page}`
      );
      return data;
    },
  });
}
