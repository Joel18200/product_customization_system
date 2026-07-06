"use client";

import { useMyCustomizations } from "@/hooks/useCustomization";
import type { CustomizationJob } from "@/types";
import { useAuthStore } from "@/stores/authStore";
import { motion } from "framer-motion";
import { getMediaUrl, formatRelativeTime } from "@/lib/utils";
import { Palette, ExternalLink, Image as ImageIcon } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const { isAuthenticated, user } = useAuthStore();
  const router = useRouter();
  const { data, isLoading } = useMyCustomizations();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, router]);

  const customizations = data?.results || [];

  return (
    <div className="min-h-screen">
      <section className="py-12 px-4" style={{ background: "var(--bg-secondary)" }}>
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-2">My Designs</h1>
          <p style={{ color: "var(--text-secondary)" }}>
            Welcome back{user?.first_name ? `, ${user.first_name}` : ""}! Here are your saved customizations.
          </p>
        </div>
      </section>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="card"><div className="skeleton h-48" /><div className="p-4"><div className="skeleton h-5 w-3/4" /></div></div>
            ))}
          </div>
        ) : customizations.length === 0 ? (
          <div className="text-center py-20">
            <Palette className="w-16 h-16 mx-auto mb-4" style={{ color: "var(--text-muted)" }} />
            <h3 className="text-xl font-semibold mb-2">No Customizations Yet</h3>
            <p className="mb-6" style={{ color: "var(--text-secondary)" }}>
              Start by browsing products and creating your first design.
            </p>
            <Link href="/products" className="btn-primary">Browse Products</Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {customizations.map((job: CustomizationJob, i: number) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="card group"
              >
                <div className="h-48 overflow-hidden" style={{ background: "var(--bg-secondary)" }}>
                  {job.output_image ? (
                    <img
                      src={getMediaUrl(job.output_image as string | null)}
                      alt={`Customization #${job.id}`}
                      className="w-full h-full object-contain p-4"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <ImageIcon className="w-12 h-12" style={{ color: "var(--text-muted)" }} />
                    </div>
                  )}
                </div>
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">Customization #{job.id}</span>
                    <span className={`badge text-xs badge-${job.status === "completed" ? "success" : job.status === "failed" ? "error" : "warning"}`}>
                      {job.status}
                    </span>
                  </div>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    {formatRelativeTime(job.created_at)}
                  </p>
                  {job.output_image && (
                    <a
                      href={getMediaUrl(job.output_image as string | null)}
                      download
                      className="btn-secondary text-xs w-full mt-3 py-1.5 flex items-center justify-center gap-1"
                    >
                      <ExternalLink className="w-3 h-3" /> Download
                    </a>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
