/**
 * Customization state management with Zustand.
 *
 * Transforms are stored INDEPENDENTLY PER VIEW (settingsByView[viewId]) so
 * moving/scaling/rotating a design on the Front view never affects the Side or
 * Back view. `designSettings` is a convenience mirror of the ACTIVE view's
 * transform; reads elsewhere in the app keep working unchanged.
 *
 * Undo/redo history is likewise tracked per view.
 */
import { create } from "zustand";
import type { DesignSettings, ProductViewType, DesignUpload } from "@/types";

interface HistoryEntry {
  settings: DesignSettings;
  timestamp: number;
}

interface ViewHistory {
  entries: HistoryEntry[];
  index: number;
}

interface CustomizationState {
  activeProductViewId: number | null;
  activeView: ProductViewType | null;
  designUpload: DesignUpload | null;

  // Per-view transforms + a mirror of the active view's transform.
  settingsByView: Record<number, DesignSettings>;
  designSettings: DesignSettings;

  jobId: number | null;
  isRendering: boolean;
  renderProgress: number;
  previewUrl: string | null;
  mode: "edit" | "result";

  // Per-view undo/redo history.
  historyByView: Record<number, ViewHistory>;

  setActiveView: (view: ProductViewType) => void;
  setDesignUpload: (upload: DesignUpload | null) => void;
  updateSettings: (settings: Partial<DesignSettings>) => void;
  setDesignSettings: (settings: Partial<DesignSettings>) => void;
  commitHistory: () => void;
  setJobId: (id: number | null) => void;
  setRendering: (rendering: boolean, progress?: number) => void;
  setPreviewUrl: (url: string | null) => void;
  setMode: (mode: "edit" | "result") => void;

  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;

  resetCustomization: () => void;
}

const DEFAULT_SETTINGS: DesignSettings = {
  scale: 0.9,
  rotation: 0,
  offsetX: 0,
  offsetY: 0,
};

const sameSettings = (a?: DesignSettings, b?: DesignSettings) =>
  !!a && !!b &&
  a.scale === b.scale &&
  a.rotation === b.rotation &&
  a.offsetX === b.offsetX &&
  a.offsetY === b.offsetY;

export const useCustomizationStore = create<CustomizationState>((set, get) => ({
  activeProductViewId: null,
  activeView: null,
  designUpload: null,
  settingsByView: {},
  designSettings: { ...DEFAULT_SETTINGS },
  jobId: null,
  isRendering: false,
  renderProgress: 0,
  previewUrl: null,
  mode: "edit",
  historyByView: {},

  setActiveView: (view) => {
    const { settingsByView, historyByView } = get();
    const current = settingsByView[view.id] ?? { ...DEFAULT_SETTINGS };
    const history =
      historyByView[view.id] ?? {
        entries: [{ settings: { ...current }, timestamp: Date.now() }],
        index: 0,
      };
    set({
      activeView: view,
      activeProductViewId: view.id,
      // Load THIS view's own transform into the active mirror.
      designSettings: { ...current },
      settingsByView: { ...settingsByView, [view.id]: { ...current } },
      historyByView: { ...historyByView, [view.id]: history },
    });
  },

  setDesignUpload: (upload) => set({ designUpload: upload }),

  // Edit that records an undo step (slider/button changes).
  updateSettings: (partial) => {
    const { activeProductViewId, settingsByView, historyByView, designSettings } = get();
    const updated = { ...designSettings, ...partial };
    if (activeProductViewId == null) {
      set({ designSettings: updated });
      return;
    }
    const h = historyByView[activeProductViewId] ?? { entries: [], index: -1 };
    const entries = h.entries.slice(0, h.index + 1);
    entries.push({ settings: { ...updated }, timestamp: Date.now() });
    set({
      designSettings: updated,
      settingsByView: { ...settingsByView, [activeProductViewId]: updated },
      historyByView: {
        ...historyByView,
        [activeProductViewId]: { entries, index: entries.length - 1 },
      },
    });
  },

  // Live edit WITHOUT touching history — used for continuous canvas gestures.
  // Call commitHistory() when the gesture ends.
  setDesignSettings: (partial) => {
    const { activeProductViewId, settingsByView, designSettings } = get();
    const updated = { ...designSettings, ...partial };
    set({
      designSettings: updated,
      settingsByView:
        activeProductViewId == null
          ? settingsByView
          : { ...settingsByView, [activeProductViewId]: updated },
    });
  },

  // Snapshot the active view's current settings into ITS history.
  commitHistory: () => {
    const { activeProductViewId, historyByView, designSettings } = get();
    if (activeProductViewId == null) return;
    const h = historyByView[activeProductViewId] ?? { entries: [], index: -1 };
    if (sameSettings(h.entries[h.index]?.settings, designSettings)) return;
    const entries = h.entries.slice(0, h.index + 1);
    entries.push({ settings: { ...designSettings }, timestamp: Date.now() });
    set({
      historyByView: {
        ...historyByView,
        [activeProductViewId]: { entries, index: entries.length - 1 },
      },
    });
  },

  setJobId: (id) => set({ jobId: id }),
  setRendering: (rendering, progress = 0) =>
    set({ isRendering: rendering, renderProgress: progress }),
  setPreviewUrl: (url) => set({ previewUrl: url }),
  setMode: (mode) => set({ mode }),

  undo: () => {
    const { activeProductViewId, historyByView, settingsByView } = get();
    if (activeProductViewId == null) return;
    const h = historyByView[activeProductViewId];
    if (!h || h.index <= 0) return;
    const index = h.index - 1;
    const settings = { ...h.entries[index].settings };
    set({
      designSettings: settings,
      settingsByView: { ...settingsByView, [activeProductViewId]: settings },
      historyByView: { ...historyByView, [activeProductViewId]: { ...h, index } },
    });
  },

  redo: () => {
    const { activeProductViewId, historyByView, settingsByView } = get();
    if (activeProductViewId == null) return;
    const h = historyByView[activeProductViewId];
    if (!h || h.index >= h.entries.length - 1) return;
    const index = h.index + 1;
    const settings = { ...h.entries[index].settings };
    set({
      designSettings: settings,
      settingsByView: { ...settingsByView, [activeProductViewId]: settings },
      historyByView: { ...historyByView, [activeProductViewId]: { ...h, index } },
    });
  },

  canUndo: () => {
    const { activeProductViewId, historyByView } = get();
    if (activeProductViewId == null) return false;
    const h = historyByView[activeProductViewId];
    return !!h && h.index > 0;
  },
  canRedo: () => {
    const { activeProductViewId, historyByView } = get();
    if (activeProductViewId == null) return false;
    const h = historyByView[activeProductViewId];
    return !!h && h.index < h.entries.length - 1;
  },

  // Full reset (Reset All button and product change).
  resetCustomization: () =>
    set({
      settingsByView: {},
      designSettings: { ...DEFAULT_SETTINGS },
      historyByView: {},
      previewUrl: null,
      jobId: null,
      isRendering: false,
      renderProgress: 0,
      mode: "edit",
    }),
}));
