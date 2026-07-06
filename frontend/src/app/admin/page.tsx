"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { AdminAnalytics } from "@/types";
import { motion } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Package, Zap, Users, Image, TrendingUp, Clock } from "lucide-react";
import Link from "next/link";

const COLORS = ["#8b5cf6", "#6366f1", "#3b82f6", "#10b981", "#f59e0b", "#ef4444"];

export default function AdminDashboardPage() {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ["admin-analytics"],
    queryFn: async () => {
      const { data } = await api.get<AdminAnalytics>("/products/admin/analytics/");
      return data;
    },
  });

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-32 rounded-xl" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="skeleton h-80 rounded-xl" />
          <div className="skeleton h-80 rounded-xl" />
        </div>
      </div>
    );
  }

  const statCards = [
    {
      label: "Total Products",
      value: analytics?.products.total || 0,
      sub: `${analytics?.products.active || 0} active`,
      icon: <Package className="w-6 h-6" />,
      color: "#8b5cf6",
    },
    {
      label: "Total Renders",
      value: analytics?.renders.total || 0,
      sub: `${analytics?.renders.recent_7d || 0} this week`,
      icon: <Zap className="w-6 h-6" />,
      color: "#6366f1",
    },
    {
      label: "Customizations",
      value: analytics?.customizations.total || 0,
      sub: "all time",
      icon: <Image className="w-6 h-6" />,
      color: "#3b82f6",
    },
    {
      label: "Avg Render Time",
      value: analytics?.renders.avg_time_seconds
        ? `${analytics.renders.avg_time_seconds}s`
        : "N/A",
      sub: "per render",
      icon: <Clock className="w-6 h-6" />,
      color: "#10b981",
    },
  ];

  const statusData = analytics?.renders.by_status
    ? Object.entries(analytics.renders.by_status).map(([name, value]) => ({
        name, value,
      }))
    : [];

  const popularData = analytics?.popular_products?.slice(0, 5) || [];

  return (
    <div className="min-h-screen">
      <section className="py-8 px-4" style={{ background: "var(--bg-secondary)" }}>
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold mb-1">Admin Dashboard</h1>
            <p style={{ color: "var(--text-secondary)" }}>System overview and analytics</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/admin/products" className="btn-secondary text-sm">
              Manage Products
            </Link>
            <Link href="/admin/jobs" className="btn-secondary text-sm">
              Render Jobs
            </Link>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Stat cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statCards.map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="card p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center"
                     style={{ background: `${stat.color}15`, color: stat.color }}>
                  {stat.icon}
                </div>
                <TrendingUp className="w-4 h-4" style={{ color: "var(--success)" }} />
              </div>
              <p className="text-2xl font-bold mb-1">{stat.value}</p>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>{stat.label}</p>
              <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{stat.sub}</p>
            </motion.div>
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Popular Products */}
          <div className="card p-6">
            <h3 className="font-semibold mb-6">Most Customized Products</h3>
            {popularData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={popularData}>
                  <XAxis
                    dataKey="name"
                    tick={{ fill: "#a0a0b8", fontSize: 12 }}
                    axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: "#a0a0b8", fontSize: 12 }}
                    axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#1a1a2e",
                      border: "1px solid rgba(255,255,255,0.06)",
                      borderRadius: "0.5rem",
                      color: "#f0f0f5",
                    }}
                  />
                  <Bar dataKey="customization_count" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center py-12" style={{ color: "var(--text-muted)" }}>
                No data yet
              </p>
            )}
          </div>

          {/* Render Status */}
          <div className="card p-6">
            <h3 className="font-semibold mb-6">Render Status Distribution</h3>
            {statusData.length > 0 ? (
              <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-8">
                <div className="w-full sm:w-1/2">
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={statusData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        dataKey="value"
                        stroke="none"
                      >
                        {statusData.map((_, index) => (
                          <Cell key={index} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          background: "#1a1a2e",
                          border: "1px solid rgba(255,255,255,0.06)",
                          borderRadius: "0.5rem",
                          color: "#f0f0f5",
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-2">
                  {statusData.map((entry, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <div className="w-3 h-3 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                      <span style={{ color: "var(--text-secondary)" }}>{entry.name}</span>
                      <span className="font-medium">{entry.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-center py-12" style={{ color: "var(--text-muted)" }}>
                No render data yet
              </p>
            )}
          </div>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link href="/admin/products" className="card p-5 flex items-center gap-4 group">
            <Package className="w-8 h-8" style={{ color: "var(--accent-primary)" }} />
            <div>
              <h4 className="font-semibold group-hover:text-black transition-colors">Product Management</h4>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Create, edit, configure products</p>
            </div>
          </Link>
          <Link href="/admin/jobs" className="card p-5 flex items-center gap-4 group">
            <Zap className="w-8 h-8" style={{ color: "var(--accent-primary)" }} />
            <div>
              <h4 className="font-semibold group-hover:text-black transition-colors">Render Jobs</h4>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Monitor queue and workers</p>
            </div>
          </Link>
          <Link href="/admin/users" className="card p-5 flex items-center gap-4 group">
            <Users className="w-8 h-8" style={{ color: "var(--accent-primary)" }} />
            <div>
              <h4 className="font-semibold group-hover:text-black transition-colors">User Management</h4>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Roles and permissions</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
