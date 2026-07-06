"use client";

import { useState } from "react";
import { useProducts, useCategories } from "@/hooks/useProducts";
import { Search, Filter, ChevronLeft, ChevronRight, Palette } from "lucide-react";
import { motion } from "framer-motion";
import { formatPrice, getMediaUrl } from "@/lib/utils";
import Link from "next/link";

export default function ProductCatalogPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);

  const { data: products, isLoading } = useProducts({
    page,
    search: search || undefined,
    category: category || undefined,
  });
  const { data: categories } = useCategories();

  return (
    <div className="min-h-screen">
      {/* Hero banner */}
      <section className="relative py-10 sm:py-16 px-4" style={{ background: "var(--bg-secondary)" }}>
        <div className="max-w-6xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl font-bold mb-3">Product Catalog</h1>
          <p style={{ color: "var(--text-secondary)" }} className="text-base sm:text-lg">
            Choose a product to customize with your design
          </p>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar: Categories */}
          <aside className="lg:w-64 shrink-0">
            <div className="glass rounded-xl p-5 sticky top-20">
              <h3 className="font-semibold text-sm uppercase tracking-wider"
                  style={{ color: "var(--text-muted)", marginBottom: "1.25rem" }}>
                <Filter className="w-4 h-4 inline mr-2" />
                Categories
              </h3>
              <div className="flex flex-col gap-1">
                <button
                  onClick={() => { setCategory(""); setPage(1); }}
                  className={`text-left px-3 py-2 rounded-lg text-sm transition-all ${
                    !category ? "font-semibold" : ""
                  }`}
                  style={{
                    background: !category ? "#000000" : "transparent",
                    color: !category ? "#ffffff" : "var(--text-secondary)",
                  }}
                >
                  All Products
                </button>
                {categories?.map((cat) => (
                  <div key={cat.id}>
                    <button
                      onClick={() => { setCategory(cat.slug); setPage(1); }}
                      className={`text-left px-3 py-2 rounded-lg text-sm w-full transition-all ${
                        category === cat.slug ? "font-semibold" : ""
                      }`}
                      style={{
                        background: category === cat.slug ? "#000000" : "transparent",
                        color: category === cat.slug ? "#ffffff" : "var(--text-secondary)",
                      }}
                    >
                      {cat.name}
                      <span className="ml-2 text-xs opacity-50">({cat.product_count})</span>
                    </button>
                    {cat.children?.map((child) => (
                      <button
                        key={child.id}
                        onClick={() => { setCategory(child.slug); setPage(1); }}
                        className={`text-left pl-8 pr-3 py-1.5 rounded-lg text-sm w-full transition-all ${
                          category === child.slug ? "font-semibold" : ""
                        }`}
                        style={{
                          background: category === child.slug ? "#000000" : "transparent",
                          color: category === child.slug ? "#ffffff" : "var(--text-muted)",
                        }}
                      >
                        {child.name}
                      </button>
                    ))}
                  </div>
                ))}
              </div>

              {/* Sort */}
            </div>
          </aside>

          {/* Main content */}
          <div className="flex-1">
            {/* Search bar */}
            <div className="relative mb-8">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5"
                      style={{ color: "var(--text-muted)" }} />
              <input
                type="text"
                placeholder="Search products..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                className="input pl-12 text-base"
                style={{ paddingLeft: "3rem" }}
              />
            </div>

            {/* Results count */}
            {products && (
              <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
                Showing {products.results.length} of {products.count} products
              </p>
            )}

            {/* Product grid */}
            {isLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="card">
                    <div className="skeleton h-64" />
                    <div className="p-5">
                      <div className="skeleton h-5 w-3/4 mb-3" />
                      <div className="skeleton h-4 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : products?.results.length === 0 ? (
              <div className="text-center py-20">
                <Palette className="w-16 h-16 mx-auto mb-4" style={{ color: "var(--text-muted)" }} />
                <h3 className="text-xl font-semibold mb-2">No Products Found</h3>
                <p style={{ color: "var(--text-secondary)" }}>
                  Try adjusting your search or filters
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {products?.results.map((product, i) => {
                  const shrinkImage =
                    product.name.includes("OTTO CAP 5 Panel") ||
                    product.name.includes("OTTO CAP Sun Visor");
                  return (
                  <motion.div
                    key={product.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: i * 0.05 }}
                  >
                    <Link href={`/products/${product.slug}`}>
                      <div className="card group cursor-pointer">
                        <div className={`relative h-64 overflow-hidden flex items-center justify-center ${shrinkImage ? "p-0" : ""}`}
                             style={{ background: "var(--bg-secondary)" }}>
                          {product.thumbnail_url ? (
                            <img
                              src={getMediaUrl(product.thumbnail_url)}
                              alt={product.name}
                              className={`transition-transform duration-500 group-hover:scale-110 ${
                                shrinkImage
                                  ? "w-full  h-full   object-cover"
                                  : "w-full h-full object-cover"
                              }`}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <Palette className="w-12 h-12" style={{ color: "var(--text-muted)" }} />
                            </div>
                          )}
                          {/* Hover overlay */}
                          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                               style={{ background: "rgba(0,0,0,0.5)" }}>
                            <span className="btn-primary text-sm">Customize</span>
                          </div>
                        </div>
                        <div className="p-5">
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <h3 className="font-semibold text-base mb-1 group-hover:text-black transition-colors">
                                {product.name}
                              </h3>
                              {product.category_name && (
                                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                                  {product.category_name}
                                </span>
                              )}
                            </div>
                            {product.base_price && (
                              <span className="font-semibold text-sm"
                                    style={{ color: "var(--accent-primary)" }}>
                                {formatPrice(product.base_price)}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-3">
                            <span className="text-xs px-2 py-0.5 rounded-full"
                                  style={{ background: "rgba(0, 0, 0, 0.05)", color: "var(--accent-primary)" }}>
                              {product.view_count} view{product.view_count !== 1 ? "s" : ""}
                            </span>
                          </div>
                        </div>
                      </div>
                    </Link>
                  </motion.div>
                  );
                })}
              </div>
            )}

            {/* Pagination */}
            {products && products.total_pages && products.total_pages > 1 && (
              <div className="flex items-center justify-center gap-4 mt-12">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page <= 1}
                  className="btn-secondary px-3 py-2 disabled:opacity-30"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  Page {page} of {products.total_pages}
                </span>
                <button
                  onClick={() => setPage(Math.min(products.total_pages!, page + 1))}
                  disabled={page >= (products.total_pages || 1)}
                  className="btn-secondary px-3 py-2 disabled:opacity-30"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
