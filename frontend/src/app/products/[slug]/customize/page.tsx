"use client";

import { useParams } from "next/navigation";
import { useProductBySlug } from "@/hooks/useProducts";
import {
  useUploadDesign,
  useStartRender,
  useRenderJobStatus,
} from "@/hooks/useCustomization";
import { useMultiViewRender } from "@/hooks/useMultiViewRender";
import { useCustomizationStore } from "@/stores/customizationStore";
import { useState, useCallback, useEffect, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { getMediaUrl, formatFileSize, downloadFile } from "@/lib/utils";
import {
  Upload, RotateCcw, RotateCw, ZoomIn, ZoomOut, Move,
  Undo2, Redo2, Download, RefreshCw, Share2,
  Image as ImageIcon, Maximize2, Loader2, Check, X,
  ChevronLeft, Eye, SlidersHorizontal,
} from "lucide-react";
import Link from "next/link";
import LiveDesignCanvas from "@/components/studio/LiveDesignCanvas";

export default function CustomizationStudioPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { data: product, isLoading: productLoading } = useProductBySlug(slug);

  const {
    activeView, designUpload, designSettings, mode, settingsByView,
    setActiveView, setDesignUpload, updateSettings,
    setDesignSettings, commitHistory, setMode,
    undo, redo, canUndo, canRedo, resetCustomization,
  } = useCustomizationStore();

  const uploadMutation = useUploadDesign();
  const startRender = useStartRender();
  const {
    byView, start: startMultiRender, reset: resetMulti,
  } = useMultiViewRender();

  const [zoom, setZoom] = useState(1);
  const [mobilePanel, setMobilePanel] = useState(false);
  const [mobileInfoPanel, setMobileInfoPanel] = useState(false);
  const [renderJobId, setRenderJobId] = useState<number | null>(null);
  const handledRenderRef = useRef<number | null>(null);
  const { data: renderJob } = useRenderJobStatus(renderJobId);

  // Render state for the view the user is currently looking at.
  const activeRender = activeView ? byView[activeView.id] : undefined;
  const activeRendering =
    activeRender?.status === "pending" || activeRender?.status === "processing";
  const activeOutput =
    activeRender?.status === "completed" ? activeRender.output : null;

  const isPreparingHd =
    !!renderJobId &&
    renderJob?.status !== "completed" &&
    renderJob?.status !== "failed";

  // ── Issue 2 fix: fully reset all canvas/design state when the product
  // changes, then select the new product's first view. The store is global,
  // so without this the previous product's view/design/position leaks over.
  const lastProductId = useRef<number | null>(null);
  useEffect(() => {
    if (!product || lastProductId.current === product.id) return;
    lastProductId.current = product.id;
    resetCustomization();
    setDesignUpload(null);
    resetMulti();
    if (product.views.length) setActiveView(product.views[0]);
  }, [product, resetCustomization, setDesignUpload, resetMulti, setActiveView]);

  // Slider/transform edits flip back to the live edit canvas so the change is
  // immediately visible.
  const changeSettings = useCallback(
    (partial: Record<string, number>) => {
      updateSettings(partial);
      setMode("edit");
    },
    [updateSettings, setMode]
  );

  // Deliver the HD render once it finishes (side-effects only; ref-guarded).
  useEffect(() => {
    if (!renderJob || renderJob.id === handledRenderRef.current) return;
    if (renderJob.status === "completed" && renderJob.output_image) {
      handledRenderRef.current = renderJob.id;
      downloadFile(
        getMediaUrl(renderJob.output_image as string),
        `customforge-hd-${activeView?.view_type ?? "view"}.png`
      );
      toast.success("HD render downloaded.");
    } else if (renderJob.status === "failed") {
      handledRenderRef.current = renderJob.id;
      toast.error("HD render failed. Please try again.");
    }
  }, [renderJob, activeView]);

  // File upload handler
  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    try {
      const result = await uploadMutation.mutateAsync(file);
      setDesignUpload(result);
      setMode("edit");
      setMobilePanel(false);
      toast.success("Design uploaded — drag, scale or rotate it on the product.");
    } catch {
      toast.error("Failed to upload design");
    }
  }, [uploadMutation, setDesignUpload, setMode]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/png": [".png"], "image/jpeg": [".jpg", ".jpeg"], "image/webp": [".webp"] },
    maxFiles: 1,
    maxSize: 20 * 1024 * 1024,
  });

  // ── Issue 3: Generate Preview renders EVERY view of the product ──
  const handleGeneratePreview = async () => {
    if (!designUpload || !product) {
      toast.error("Please upload a design first.");
      return;
    }
    setMode("result");
    try {
      await startMultiRender(
        product.views,
        designUpload.id,
        settingsByView,
        designSettings
      );
      toast.success("Rendered all views.");
    } catch {
      toast.error("Failed to generate preview");
    }
  };

  // Download HD for the currently-shown view.
  const handleDownload = async () => {
    const jobId = activeRender?.jobId;
    if (!jobId) return;
    try {
      const result = await startRender.mutateAsync({ jobId, renderType: "final" });
      handledRenderRef.current = null;
      setRenderJobId(result.id);
      toast.success("Preparing HD render — it will download when ready.");
    } catch {
      toast.error("Failed to start render");
    }
  };

  if (productLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: "var(--accent-primary)" }} />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold mb-4">Product Not Found</h2>
        <Link href="/products" className="btn-primary">Back to Catalog</Link>
      </div>
    );
  }

  const anyRendering = Object.values(byView).some(
    (s) => s.status === "pending" || s.status === "processing"
  );

  return (
    <div className="h-[calc(100vh-64px)] flex flex-col overflow-hidden"
         style={{ background: "var(--bg-primary)" }}>
      {/* Top Bar */}
      <div className="glass flex items-center justify-between gap-2 px-4 py-2"
           style={{ borderTop: "none", borderLeft: "none", borderRight: "none" }}>
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
          <Link href={`/products/${slug}`} className="btn-ghost p-2 flex-shrink-0">
            <ChevronLeft className="w-4 h-4" />
          </Link>
          <h1 className="font-semibold truncate min-w-0"
              style={{ fontSize: "clamp(0.95rem, 3.5vw, 1.125rem)", lineHeight: 1.2 }}>
            {product.name}
          </h1>
          {anyRendering && (
            <span className="badge badge-warning text-xs flex items-center gap-1 flex-shrink-0">
              <Loader2 className="w-3 h-3 animate-spin" />
              <span className="hidden sm:inline">Rendering all views...</span>
            </span>
          )}
          {!anyRendering && mode === "result" && activeOutput && (
            <span className="badge badge-success text-xs flex items-center gap-1 flex-shrink-0">
              <Check className="w-3 h-3" />
              Ready
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button onClick={handleGeneratePreview} className="btn-primary text-sm px-4 py-1.5 hidden sm:inline-flex items-center"
                  disabled={!designUpload || anyRendering}>
            {anyRendering ? (
              <><Loader2 className="w-4 h-4 inline animate-spin mr-1" /> Rendering</>
            ) : (
              <><Eye className="w-4 h-4 inline mr-1" /> Generate Preview</>
            )}
          </button>
        </div>
      </div>

      {/* Studio Grid */}
      <div className="flex-1 flex overflow-hidden">
        {/* Mobile backdrop for the controls drawer */}
        {mobilePanel && (
          <div
            className="lg:hidden fixed inset-0 top-16 z-30"
            style={{ background: "rgba(0,0,0,0.4)" }}
            onClick={() => setMobilePanel(false)}
          />
        )}

        {/* Mobile backdrop for the summary/export drawer */}
        {mobileInfoPanel && (
          <div
            className="lg:hidden fixed inset-0 top-16 z-30"
            style={{ background: "rgba(0,0,0,0.4)" }}
            onClick={() => setMobileInfoPanel(false)}
          />
        )}

        {/* ── Left Sidebar / mobile drawer ── */}
        <aside
          className={`glass overflow-y-auto z-40 transition-transform duration-300
            fixed top-16 bottom-0 left-0 w-72 max-w-[85vw]
            lg:static lg:top-auto lg:bottom-auto lg:max-w-none lg:translate-x-0 lg:transition-none lg:flex-shrink-0 lg:block
            ${mobilePanel ? "translate-x-0" : "-translate-x-full"}`}
          style={{ borderTop: "none", borderBottom: "none", borderLeft: "none" }}>
          {/* Mobile drawer header */}
          <div className="lg:hidden flex items-center justify-between px-4 pt-4">
            <span className="text-sm font-semibold">Design Controls</span>
            <button onClick={() => setMobilePanel(false)} className="btn-ghost p-1.5">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="p-4 space-y-6">
            {/* Upload Area */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider mb-3"
                  style={{ color: "var(--text-muted)" }}>
                Design Upload
              </h3>
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                  isDragActive ? "scale-[1.02]" : ""
                }`}
                style={{
                  borderColor: isDragActive
                    ? "var(--accent-primary)"
                    : "var(--border-subtle)",
                  background: isDragActive
                    ? "rgba(0, 0, 0, 0.03)"
                    : "transparent",
                }}
              >
                <input {...getInputProps()} />
                {uploadMutation.isPending ? (
                  <Loader2 className="w-8 h-8 mx-auto mb-2 animate-spin"
                           style={{ color: "var(--accent-primary)" }} />
                ) : (
                  <Upload className="w-8 h-8 mx-auto mb-2"
                          style={{ color: "var(--text-muted)" }} />
                )}
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  {isDragActive ? "Drop here" : "Drag & drop or click"}
                </p>
                <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                  PNG, JPEG, WebP (max 20MB)
                </p>
              </div>

              {/* Uploaded design preview */}
              {designUpload && (
                <div className="mt-3 glass rounded-lg p-3">
                  <div className="flex items-center gap-3">
                    <img
                      src={getMediaUrl(designUpload.image)}
                      alt="Design"
                      className="w-12 h-12 rounded object-cover"
                      style={{ background: "var(--bg-secondary)" }}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">{designUpload.original_filename || "Design"}</p>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {designUpload.width}×{designUpload.height} · {formatFileSize(designUpload.file_size)}
                      </p>
                    </div>
                    <button onClick={() => { setDesignUpload(null); resetMulti(); setMode("edit"); }}
                            className="btn-ghost p-1">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Transform Controls */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider mb-3"
                  style={{ color: "var(--text-muted)" }}>
                Transform
              </h3>
              <div className="space-y-4">
                {/* Scale */}
                <div>
                  <label className="text-xs flex justify-between mb-1.5"
                         style={{ color: "var(--text-secondary)" }}>
                    <span>Scale</span>
                    <span>{Math.round((designSettings.scale || 0.9) * 100)}%</span>
                  </label>
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.05"
                    value={designSettings.scale || 0.9}
                    onChange={(e) => changeSettings({ scale: parseFloat(e.target.value) })}
                    className="w-full accent-white"
                  />
                </div>

                {/* Rotation */}
                <div>
                  <label className="text-xs flex justify-between mb-1.5"
                         style={{ color: "var(--text-secondary)" }}>
                    <span>Rotation</span>
                    <span>{designSettings.rotation || 0}°</span>
                  </label>
                  <input
                    type="range"
                    min="-180"
                    max="180"
                    step="1"
                    value={designSettings.rotation || 0}
                    onChange={(e) => changeSettings({ rotation: parseInt(e.target.value) })}
                    className="w-full accent-white"
                  />
                </div>

                {/* Position X */}
                <div>
                  <label className="text-xs flex justify-between mb-1.5"
                         style={{ color: "var(--text-secondary)" }}>
                    <span>Offset X</span>
                    <span>{designSettings.offsetX || 0}px</span>
                  </label>
                  <input
                    type="range"
                    min="-200"
                    max="200"
                    step="5"
                    value={designSettings.offsetX || 0}
                    onChange={(e) => changeSettings({ offsetX: parseInt(e.target.value) })}
                    className="w-full accent-white"
                  />
                </div>

                {/* Position Y */}
                <div>
                  <label className="text-xs flex justify-between mb-1.5"
                         style={{ color: "var(--text-secondary)" }}>
                    <span>Offset Y</span>
                    <span>{designSettings.offsetY || 0}px</span>
                  </label>
                  <input
                    type="range"
                    min="-200"
                    max="200"
                    step="5"
                    value={designSettings.offsetY || 0}
                    onChange={(e) => changeSettings({ offsetY: parseInt(e.target.value) })}
                    className="w-full accent-white"
                  />
                </div>
              </div>

              {/* Quick actions */}
              <div className="flex items-center gap-2 mt-4">
                <button
                  onClick={() => changeSettings({ rotation: (designSettings.rotation || 0) - 90 })}
                  className="btn-secondary p-2 flex-1"
                  title="Rotate Left"
                >
                  <RotateCcw className="w-4 h-4 mx-auto" />
                </button>
                <button
                  onClick={() => changeSettings({ rotation: (designSettings.rotation || 0) + 90 })}
                  className="btn-secondary p-2 flex-1"
                  title="Rotate Right"
                >
                  <RotateCw className="w-4 h-4 mx-auto" />
                </button>
                <button
                  onClick={() => changeSettings({ offsetX: 0, offsetY: 0 })}
                  className="btn-secondary p-2 flex-1"
                  title="Center"
                >
                  <Maximize2 className="w-4 h-4 mx-auto" />
                </button>
              </div>
            </div>

            {/* Undo / Redo */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider mb-3"
                  style={{ color: "var(--text-muted)" }}>
                History
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={undo}
                  disabled={!canUndo()}
                  className="btn-secondary p-2 flex-1 disabled:opacity-30"
                >
                  <Undo2 className="w-4 h-4 mx-auto" />
                </button>
                <button
                  onClick={redo}
                  disabled={!canRedo()}
                  className="btn-secondary p-2 flex-1 disabled:opacity-30"
                >
                  <Redo2 className="w-4 h-4 mx-auto" />
                </button>
                <button
                  onClick={() => { resetCustomization(); resetMulti(); }}
                  className="btn-secondary p-2 flex-1"
                  title="Reset All"
                >
                  <RefreshCw className="w-4 h-4 mx-auto" />
                </button>
              </div>
            </div>
          </div>
        </aside>

        {/* ── Center Canvas ── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* View switcher — shows per-view render status in result mode */}
          <div className="flex items-center justify-center gap-2 py-3 px-4 flex-wrap"
               style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            {product.views.map((view) => {
              const st = byView[view.id]?.status;
              return (
                <button
                  key={view.id}
                  onClick={() => setActiveView(view)}
                  className="text-sm px-4 py-1.5 rounded-lg transition-all flex items-center gap-1.5"
                  style={{
                    background: activeView?.id === view.id
                      ? "rgba(0, 0, 0, 0.06)"
                      : "transparent",
                    color: activeView?.id === view.id
                      ? "var(--accent-primary)"
                      : "var(--text-muted)",
                    fontWeight: activeView?.id === view.id ? 600 : 400,
                  }}
                >
                  {view.view_name}
                  {mode === "result" && st === "completed" && (
                    <Check className="w-3.5 h-3.5" style={{ color: "var(--success)" }} />
                  )}
                  {mode === "result" && (st === "pending" || st === "processing") && (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  )}
                  {mode === "result" && st === "failed" && (
                    <X className="w-3.5 h-3.5" style={{ color: "var(--error)" }} />
                  )}
                </button>
              );
            })}
          </div>

          {/* Canvas area */}
          <div className="flex-1 flex items-center justify-center p-4 overflow-auto"
               style={{ background: "var(--bg-secondary)" }}>
            <div
              className="relative transition-transform duration-200"
              style={{ transform: `scale(${mode === "edit" ? 1 : zoom})` }}
            >
              {mode === "result" ? (
                <div className="relative">
                  {activeOutput ? (
                    <motion.img
                      key={activeOutput}
                      src={activeOutput}
                      alt="Preview"
                      className="max-h-[70vh] max-w-full rounded-lg shadow-2xl"
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.4 }}
                    />
                  ) : activeView ? (
                    <img
                      src={getMediaUrl(activeView.image_url || activeView.image)}
                      alt={activeView.view_name}
                      className="max-h-[70vh] max-w-full rounded-lg opacity-60"
                    />
                  ) : null}

                  {/* per-view progress / failure overlay */}
                  {activeRendering && (
                    <div className="absolute inset-0 flex items-center justify-center rounded-lg"
                         style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(8px)" }}>
                      <div className="text-center">
                        <Loader2 className="w-10 h-10 mx-auto mb-3 animate-spin"
                                 style={{ color: "var(--accent-primary)" }} />
                        <p className="text-sm font-medium">
                          Rendering {activeView?.view_name}…
                        </p>
                      </div>
                    </div>
                  )}
                  {activeRender?.status === "failed" && (
                    <div className="absolute inset-0 flex items-center justify-center rounded-lg"
                         style={{ background: "rgba(0,0,0,0.6)" }}>
                      <p className="text-sm font-medium" style={{ color: "#fff" }}>
                        This view failed to render.
                      </p>
                    </div>
                  )}

                  {designUpload && (
                    <button
                      onClick={() => setMode("edit")}
                      className="btn-secondary absolute top-3 left-3 text-xs px-3 py-1.5 flex items-center gap-1.5"
                      title="Go back to interactive positioning"
                    >
                      <Move className="w-3.5 h-3.5" /> Reposition
                    </button>
                  )}
                </div>
              ) : activeView ? (
                <div className="relative">
                  {designUpload ? (
                    <LiveDesignCanvas
                      key={activeView.id}
                      view={activeView}
                      design={designUpload}
                      settings={designSettings}
                      onLiveChange={setDesignSettings}
                      onCommit={commitHistory}
                    />
                  ) : (
                    <img
                      src={getMediaUrl(activeView.image_url || activeView.image)}
                      alt={activeView.view_name}
                      className="max-h-[70vh] max-w-full rounded-lg"
                    />
                  )}
                </div>
              ) : (
                <div className="w-[500px] h-[500px] flex items-center justify-center rounded-xl"
                     style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
                  <div className="text-center">
                    <ImageIcon className="w-16 h-16 mx-auto mb-3" style={{ color: "var(--text-muted)" }} />
                    <p style={{ color: "var(--text-muted)" }}>No view selected</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Zoom controls */}
          <div className="flex items-center justify-center gap-3 py-2"
               style={{ borderTop: "1px solid var(--border-subtle)" }}>
            <button onClick={() => setZoom(Math.max(0.5, zoom - 0.1))}
                    className="btn-ghost p-1.5">
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-xs w-16 text-center" style={{ color: "var(--text-muted)" }}>
              {Math.round(zoom * 100)}%
            </span>
            <button onClick={() => setZoom(Math.min(2, zoom + 0.1))}
                    className="btn-ghost p-1.5">
              <ZoomIn className="w-4 h-4" />
            </button>
            <button onClick={() => setZoom(1)} className="btn-ghost text-xs">
              Reset
            </button>
          </div>
        </div>

        {/* ── Right Sidebar / mobile drawer ── */}
        <aside
          className={`glass overflow-y-auto z-40 transition-transform duration-300
            fixed top-16 bottom-0 right-0 w-72 max-w-[85vw]
            lg:static lg:top-auto lg:bottom-auto lg:max-w-none lg:translate-x-0 lg:transition-none lg:flex-shrink-0 lg:block
            ${mobileInfoPanel ? "translate-x-0" : "translate-x-full"}`}
          style={{ borderTop: "none", borderBottom: "none", borderRight: "none" }}>
          {/* Mobile drawer header */}
          <div className="lg:hidden flex items-center justify-between px-4 pt-4">
            <span className="text-sm font-semibold">Summary &amp; Export</span>
            <button onClick={() => setMobileInfoPanel(false)} className="btn-ghost p-1.5">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="p-4 space-y-6">
            {/* Summary */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider mb-3"
                  style={{ color: "var(--text-muted)" }}>
                Customization Summary
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span style={{ color: "var(--text-muted)" }}>Product</span>
                  <span className="truncate ml-2">{product.name}</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: "var(--text-muted)" }}>View</span>
                  <span>{activeView?.view_name || "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: "var(--text-muted)" }}>Views</span>
                  <span>{product.views.length}</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: "var(--text-muted)" }}>Design</span>
                  <span className="truncate ml-2">
                    {designUpload?.original_filename || "None"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: "var(--text-muted)" }}>Status</span>
                  {anyRendering ? (
                    <span className="badge badge-warning text-xs">Processing</span>
                  ) : mode === "result" && activeOutput ? (
                    <span className="badge badge-success text-xs">Ready</span>
                  ) : (
                    <span className="badge badge-info text-xs">Not rendered</span>
                  )}
                </div>
              </div>
            </div>

            {/* Design Settings Display */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider mb-3"
                  style={{ color: "var(--text-muted)" }}>
                Design Settings
              </h3>
              <div className="glass rounded-lg p-3 space-y-1.5 text-xs"
                   style={{ fontFamily: "monospace" }}>
                <div className="flex justify-between">
                  <span style={{ color: "var(--text-muted)" }}>scale</span>
                  <span>{designSettings.scale}</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: "var(--text-muted)" }}>rotation</span>
                  <span>{designSettings.rotation}°</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: "var(--text-muted)" }}>offsetX</span>
                  <span>{designSettings.offsetX}px</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: "var(--text-muted)" }}>offsetY</span>
                  <span>{designSettings.offsetY}px</span>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="space-y-2">
              <button
                onClick={handleDownload}
                disabled={!activeOutput || activeRendering || isPreparingHd}
                className="btn-primary w-full text-sm py-2.5 flex items-center justify-center gap-2 disabled:opacity-30"
              >
                {isPreparingHd ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Preparing HD…</>
                ) : (
                  <><Download className="w-4 h-4" /> Download HD ({activeView?.view_name})</>
                )}
              </button>

              {activeOutput && (
                <button
                  onClick={() => downloadFile(activeOutput, `customforge-${activeView?.view_type ?? "view"}.png`)}
                  className="btn-secondary w-full text-sm py-2.5 flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download Preview
                </button>
              )}

              <button
                onClick={() => {
                  if (!activeOutput) {
                    toast.error("Generate a preview first.");
                    return;
                  }
                  navigator.clipboard?.writeText(activeOutput).then(
                    () => toast.success("Preview link copied to clipboard."),
                    () => toast.error("Could not copy link.")
                  );
                }}
                disabled={!activeOutput}
                className="btn-ghost w-full text-sm py-2 flex items-center justify-center gap-2 disabled:opacity-30"
              >
                <Share2 className="w-4 h-4" />
                Copy Preview Link
              </button>
            </div>
          </div>
        </aside>
      </div>

      {/* ── Bottom Toolbar (mobile) ── */}
      <div className="lg:hidden glass flex items-center justify-around px-2 py-2 gap-1"
           style={{ borderBottom: "none", borderLeft: "none", borderRight: "none" }}>
        <button onClick={() => { setMobileInfoPanel(false); setMobilePanel(true); }}
                className="btn-ghost flex flex-col items-center gap-0.5 px-2 py-1"
                title="Design & transform controls">
          <SlidersHorizontal className="w-5 h-5" />
          <span className="text-[10px] leading-none">Design</span>
        </button>
        <button onClick={undo} disabled={!canUndo()}
                className="btn-ghost flex flex-col items-center gap-0.5 px-2 py-1 disabled:opacity-30">
          <Undo2 className="w-5 h-5" />
          <span className="text-[10px] leading-none">Undo</span>
        </button>
        <button onClick={handleGeneratePreview} disabled={!designUpload || anyRendering}
                className="btn-primary px-5 py-2.5 text-sm disabled:opacity-30 flex items-center gap-1.5">
          {anyRendering ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
          Render
        </button>
        <button onClick={redo} disabled={!canRedo()}
                className="btn-ghost flex flex-col items-center gap-0.5 px-2 py-1 disabled:opacity-30">
          <Redo2 className="w-5 h-5" />
          <span className="text-[10px] leading-none">Redo</span>
        </button>
        <button onClick={() => { setMobilePanel(false); setMobileInfoPanel(true); }}
                className="btn-ghost flex flex-col items-center gap-0.5 px-2 py-1"
                title="Summary & export">
          <Download className="w-5 h-5" />
          <span className="text-[10px] leading-none">Export</span>
        </button>
      </div>
    </div>
  );
}
