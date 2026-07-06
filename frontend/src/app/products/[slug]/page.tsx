"use client";

import { useParams } from "next/navigation";
import { useProductBySlug } from "@/hooks/useProducts";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Palette, ArrowRight, Eye, ChevronLeft } from "lucide-react";
import { formatPrice, getMediaUrl } from "@/lib/utils";
import Link from "next/link";

export default function ProductDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { data: product, isLoading } = useProductBySlug(slug);
  const [activeViewIdx, setActiveViewIdx] = useState(0);

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div className="skeleton h-[500px] rounded-xl" />
          <div>
            <div className="skeleton h-10 w-3/4 mb-4" />
            <div className="skeleton h-6 w-1/2 mb-8" />
            <div className="skeleton h-32 w-full mb-4" />
            <div className="skeleton h-12 w-48" />
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold mb-4">Product Not Found</h2>
        <Link href="/products" className="btn-primary">
          Back to Catalog
        </Link>
      </div>
    );
  }

  const activeView = product.views[activeViewIdx];
  const printArea = activeView?.print_areas?.[0];

  return (
    <div className="min-h-screen">
      {/* Breadcrumb */}
      <div className="max-w-6xl mx-auto px-4 py-4">
        <Link href="/products" className="text-sm inline-flex items-center gap-1 transition-colors"
              style={{ color: "var(--text-muted)" }}>
          <ChevronLeft className="w-4 h-4" />
          Back to Products
        </Link>
      </div>

      <div className="max-w-6xl mx-auto px-4 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-12">
          {/* Image Gallery */}
          <div>
            <div className="card overflow-hidden mb-4">
              <div className="relative flex items-center justify-center" style={{ background: "var(--bg-secondary)", aspectRatio: "1" }}>
                <AnimatePresence mode="wait">
                  {activeView ? (
                    <motion.div
                      key={activeView.id}
                      className="relative"
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      transition={{ duration: 0.3 }}
                    >
                      <img
                        src={getMediaUrl(activeView.image_url || activeView.image)}
                        alt={activeView.view_name}
                        className="max-h-[460px] max-w-full object-contain"
                      />
                      {/* Print area overlay — positioned as a fraction of the
                          view's real image dimensions, so it stays aligned
                          regardless of source resolution. */}
                      {printArea && activeView.image_width && activeView.image_height && (
                        <div
                          className="absolute border-2 border-dashed rounded-sm pointer-events-none"
                          style={{
                            borderColor: "rgba(0, 0, 0, 0.45)",
                            left: `${(printArea.x / activeView.image_width) * 100}%`,
                            top: `${(printArea.y / activeView.image_height) * 100}%`,
                            width: `${(printArea.width / activeView.image_width) * 100}%`,
                            height: `${(printArea.height / activeView.image_height) * 100}%`,
                            background: "rgba(0, 0, 0, 0.04)",
                          }}
                        >
                          <span className="absolute -top-6 left-0 text-xs font-medium px-2 py-0.5 rounded whitespace-nowrap"
                                style={{ background: "var(--accent-primary)", color: "white" }}>
                            Print Area
                          </span>
                        </div>
                      )}
                    </motion.div>
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Palette className="w-20 h-20" style={{ color: "var(--text-muted)" }} />
                    </div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* View selector */}
            {product.views.length > 1 && (
              <div className="flex gap-3">
                {product.views.map((view, idx) => (
                  <button
                    key={view.id}
                    onClick={() => setActiveViewIdx(idx)}
                    className={`card w-20 h-20 p-2 cursor-pointer transition-all ${
                      idx === activeViewIdx ? "ring-2" : ""
                    }`}
                    style={{
                      outline: idx === activeViewIdx ? "2px solid var(--accent-primary)" : "none",
                      outlineOffset: "2px",
                    }}
                  >
                    <img
                      src={getMediaUrl(view.image_url || view.image)}
                      alt={view.view_name}
                      className="w-full h-full object-contain"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Info */}
          <div className="animate-fade-in">
            {product.category && (
              <span className="badge badge-info mb-4">{product.category.name}</span>
            )}

            <h1 className="text-3xl md:text-4xl font-bold mb-3">{product.name}</h1>

            {product.base_price && (
              <p className="text-2xl font-bold mb-6 gradient-text">
                {formatPrice(product.base_price)}
              </p>
            )}

            <p className="text-base leading-relaxed mb-8"
               style={{ color: "var(--text-secondary)" }}>
              {product.description || "High-quality product ready for your custom design."}
            </p>

            {/* SKU & Tags */}
            {product.sku && (
              <p className="text-sm mb-2" style={{ color: "var(--text-muted)" }}>
                SKU: {product.sku}
              </p>
            )}

            {product.tags && product.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-8">
                {product.tags.map((tag, i) => (
                  <span key={i} className="text-xs px-3 py-1 rounded-full"
                        style={{ background: "var(--bg-card)", color: "var(--text-muted)" }}>
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {/* Available views */}
            <div className="glass rounded-xl p-5 mb-8">
              <h3 className="font-semibold text-sm uppercase tracking-wider mb-3"
                  style={{ color: "var(--text-muted)" }}>
                <Eye className="w-4 h-4 inline mr-2" />
                Available Views
              </h3>
              <div className="flex flex-wrap gap-2">
                {product.views.map((view, idx) => (
                  <button
                    key={view.id}
                    onClick={() => setActiveViewIdx(idx)}
                    className="text-sm px-3 py-1.5 rounded-lg transition-all"
                    style={{
                      background: idx === activeViewIdx
                        ? "rgba(0, 0, 0, 0.06)"
                        : "var(--bg-card)",
                      color: idx === activeViewIdx
                        ? "var(--accent-primary)"
                        : "var(--text-secondary)",
                      fontWeight: idx === activeViewIdx ? 600 : 400,
                    }}
                  >
                    {view.view_name}
                    {view.print_areas.length > 0 && (
                      <span className="ml-1 text-xs opacity-60">
                        ({view.print_areas.length} print area{view.print_areas.length > 1 ? "s" : ""})
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Print area info */}
            {printArea && (
              <div className="glass rounded-xl p-5 mb-8">
                <h3 className="font-semibold text-sm uppercase tracking-wider mb-3"
                    style={{ color: "var(--text-muted)" }}>
                  Print Area Details
                </h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Size:</span>{" "}
                    {printArea.width} × {printArea.height}px
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Max DPI:</span>{" "}
                    {printArea.max_dpi}
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Position:</span>{" "}
                    ({printArea.x}, {printArea.y})
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Label:</span>{" "}
                    {printArea.label}
                  </div>
                </div>
              </div>
            )}

            {/* CTA */}
            <Link
              href={`/products/${slug}/customize`}
              className="btn-primary text-base px-8 py-3.5 inline-flex items-center gap-2 w-full justify-center sm:w-auto"
            >
              <Palette className="w-5 h-5" />
              Customize This Product
              <ArrowRight className="w-5 h-5" />
            </Link>

            {/* Variants */}
            {product.variants.length > 0 && (
              <div className="mt-8">
                <h3 className="font-semibold text-sm uppercase tracking-wider mb-3"
                    style={{ color: "var(--text-muted)" }}>
                  Available Variants
                </h3>
                <div className="flex flex-wrap gap-2">
                  {product.variants.filter(v => v.is_active).map((variant) => (
                    <span key={variant.id} className="text-sm px-3 py-1.5 rounded-lg"
                          style={{ background: "var(--bg-card)", color: "var(--text-secondary)" }}>
                      {variant.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
