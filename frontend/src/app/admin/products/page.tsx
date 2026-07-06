"use client";

import { useProducts } from "@/hooks/useProducts";
import { useState } from "react";
import { motion } from "framer-motion";
import { formatPrice, formatDate } from "@/lib/utils";
import { Plus, Search, Edit, Trash2, Eye } from "lucide-react";
import Link from "next/link";

export default function AdminProductsPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useProducts({ page, search: search || undefined });

  return (
    <div className="min-h-screen">
      <section className="py-8 px-4" style={{ background: "var(--bg-secondary)" }}>
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h1 className="text-2xl font-bold">Product Management</h1>
          <button className="btn-primary text-sm flex items-center gap-2 self-start sm:self-auto">
            <Plus className="w-4 h-4" /> Add Product
          </button>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4"
                  style={{ color: "var(--text-muted)" }} />
          <input type="text" className="input pl-10" placeholder="Search products..."
                 value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>

        {/* Table */}
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: "var(--bg-secondary)" }}>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>Product</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>SKU</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>Category</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>Price</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>Views</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>Status</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>Created</th>
                  <th className="text-right px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  [...Array(5)].map((_, i) => (
                    <tr key={i}><td colSpan={8} className="px-4 py-3"><div className="skeleton h-8" /></td></tr>
                  ))
                ) : data?.results.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-12" style={{ color: "var(--text-muted)" }}>
                      No products found
                    </td>
                  </tr>
                ) : (
                  data?.results.map((product, i) => (
                    <motion.tr
                      key={product.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.03 }}
                      style={{ borderTop: "1px solid var(--border-subtle)" }}
                      className="hover:bg-white/[0.02] transition-colors"
                    >
                      <td className="px-4 py-3 font-medium">{product.name}</td>
                      <td className="px-4 py-3" style={{ color: "var(--text-muted)" }}>{product.sku || "—"}</td>
                      <td className="px-4 py-3">{product.category_name || "—"}</td>
                      <td className="px-4 py-3">{formatPrice(product.base_price)}</td>
                      <td className="px-4 py-3">{product.view_count}</td>
                      <td className="px-4 py-3">
                        <span className={`badge text-xs ${product.is_active ? "badge-success" : "badge-error"}`}>
                          {product.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-4 py-3" style={{ color: "var(--text-muted)" }}>
                        {formatDate(product.created_at)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Link href={`/products/${product.slug}`} className="btn-ghost p-1.5">
                            <Eye className="w-4 h-4" />
                          </Link>
                          <button className="btn-ghost p-1.5">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button className="btn-ghost p-1.5" style={{ color: "var(--error)" }}>
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
