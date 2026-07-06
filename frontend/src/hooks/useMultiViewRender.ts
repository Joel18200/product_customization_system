/**
 * useMultiViewRender — renders a design onto EVERY view of a product.
 *
 * On start(), it creates one customization job per view (same design +
 * transform settings) and tracks each view's status/output independently, so
 * the studio can show a rendered result for Front / Back / Left / Right, with
 * per-view progress. Jobs that don't complete synchronously are polled.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import api from "@/lib/api";
import { getMediaUrl } from "@/lib/utils";
import type { DesignSettings } from "@/types";

export type ViewRenderStatus = "pending" | "processing" | "completed" | "failed";

export interface ViewRender {
  jobId: number | null;
  status: ViewRenderStatus;
  output: string | null; // resolved media URL
}

interface ViewLike {
  id: number;
}

export function useMultiViewRender() {
  const [byView, setByView] = useState<Record<number, ViewRender>>({});
  const ref = useRef<Record<number, ViewRender>>({});
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const commit = useCallback((next: Record<number, ViewRender>) => {
    ref.current = next;
    setByView(next);
  }, []);

  const patch = useCallback(
    (viewId: number, p: Partial<ViewRender>) => {
      commit({ ...ref.current, [viewId]: { ...ref.current[viewId], ...p } });
    },
    [commit]
  );

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => stop, [stop]);

  const reset = useCallback(() => {
    stop();
    commit({});
  }, [stop, commit]);

  const start = useCallback(
    async (
      views: ViewLike[],
      designId: number,
      settingsByView: Record<number, DesignSettings>,
      fallback: DesignSettings
    ) => {
      stop();
      const init: Record<number, ViewRender> = {};
      views.forEach((v) => {
        init[v.id] = { jobId: null, status: "pending", output: null };
      });
      commit(init);

      // Create one job per view, each with THAT view's own transform.
      await Promise.all(
        views.map(async (v) => {
          try {
            const { data } = await api.post("/products/customization-jobs/", {
              design: designId,
              product_view: v.id,
              design_settings: settingsByView[v.id] ?? fallback,
            });
            patch(v.id, {
              jobId: data.id,
              status: data.status,
              output: data.output_image ? getMediaUrl(data.output_image) : null,
            });
          } catch {
            patch(v.id, { status: "failed" });
          }
        })
      );

      // Poll any jobs that didn't finish synchronously (Celery path).
      const stillPending = Object.values(ref.current).some(
        (s) => s.jobId && s.status !== "completed" && s.status !== "failed"
      );
      if (stillPending) {
        intervalRef.current = setInterval(async () => {
          let pending = false;
          await Promise.all(
            Object.entries(ref.current).map(async ([vid, st]) => {
              if (!st.jobId || st.status === "completed" || st.status === "failed")
                return;
              try {
                const { data } = await api.get(
                  `/products/customization-jobs/${st.jobId}/`
                );
                if (data.status === "completed" && data.output_image) {
                  patch(Number(vid), {
                    status: "completed",
                    output: getMediaUrl(data.output_image),
                  });
                } else if (data.status === "failed") {
                  patch(Number(vid), { status: "failed" });
                } else {
                  pending = true;
                }
              } catch {
                pending = true;
              }
            })
          );
          if (!pending) stop();
        }, 2000);
      }
    },
    [stop, commit, patch]
  );

  const values = Object.values(byView);
  const isRendering =
    values.length > 0 &&
    values.some((s) => s.status === "pending" || s.status === "processing");
  const allDone =
    values.length > 0 &&
    values.every((s) => s.status === "completed" || s.status === "failed");

  return { byView, start, reset, isRendering, allDone };
}
