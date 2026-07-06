"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { CustomizationJob } from "@/types";
import { motion } from "framer-motion";
import { formatRelativeTime } from "@/lib/utils";
import { RefreshCw, Loader2, CheckCircle, XCircle, Clock } from "lucide-react";

export default function AdminJobsPage() {
  const { data: jobs, isLoading, refetch } = useQuery({
    queryKey: ["admin-render-jobs"],
    queryFn: async () => {
      const { data } = await api.get<{ results: CustomizationJob[] }>(
        "/products/customization-jobs/?page_size=50"
      );
      return data.results;
    },
    refetchInterval: 5000,
  });

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle className="w-4 h-4" style={{ color: "var(--success)" }} />;
      case "failed": return <XCircle className="w-4 h-4" style={{ color: "var(--error)" }} />;
      case "processing": return <Loader2 className="w-4 h-4 animate-spin" style={{ color: "var(--warning)" }} />;
      default: return <Clock className="w-4 h-4" style={{ color: "var(--text-muted)" }} />;
    }
  };

  return (
    <div className="min-h-screen">
      <section className="py-8 px-4" style={{ background: "var(--bg-secondary)" }}>
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h1 className="text-2xl font-bold">Render Jobs</h1>
          <button onClick={() => refetch()} className="btn-secondary text-sm flex items-center gap-2 self-start sm:self-auto">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: "var(--bg-secondary)" }}>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>ID</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>Status</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>Created</th>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-muted)" }}>Output</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  [...Array(5)].map((_, i) => (
                    <tr key={i}><td colSpan={4} className="px-4 py-3"><div className="skeleton h-8" /></td></tr>
                  ))
                ) : !jobs?.length ? (
                  <tr>
                    <td colSpan={4} className="text-center py-12" style={{ color: "var(--text-muted)" }}>
                      No render jobs yet
                    </td>
                  </tr>
                ) : (
                  jobs.map((job, i) => (
                    <motion.tr
                      key={job.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.02 }}
                      style={{ borderTop: "1px solid var(--border-subtle)" }}
                      className="hover:bg-white/[0.02]"
                    >
                      <td className="px-4 py-3 font-medium">#{job.id}</td>
                      <td className="px-4 py-3">
                        <span className="flex items-center gap-2">
                          {statusIcon(job.status)}
                          {job.status}
                        </span>
                      </td>
                      <td className="px-4 py-3" style={{ color: "var(--text-muted)" }}>
                        {formatRelativeTime(job.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        {job.output_image ? (
                          <span className="badge badge-success text-xs">Has output</span>
                        ) : (
                          <span style={{ color: "var(--text-muted)" }}>—</span>
                        )}
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
