"use client";

import { useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { LogIn, Loader2, Eye, EyeOff, ChevronLeft } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

export default function LoginPage() {
  const { login, isLoading, error, clearError } = useAuthStore();
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({ username: "", password: "" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      await login(form);
      toast.success("Welcome back!");
      router.push("/products");
    } catch {
      // Error handled by store
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <Link href="/" className="btn-ghost text-sm inline-flex items-center gap-1 mb-4">
          <ChevronLeft className="w-4 h-4" /> Back
        </Link>
        <div className="card p-6 sm:p-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold mb-2">Welcome Back</h1>
            <p style={{ color: "var(--text-secondary)" }} className="text-sm">
              Sign in to access your customizations
            </p>
          </div>

          {error && (
            <div className="mb-6 p-3 rounded-lg text-sm"
                 style={{ background: "rgba(239, 68, 68, 0.1)", color: "var(--error)" }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
                Username
              </label>
              <input
                type="text"
                className="input"
                placeholder="Enter your username"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  className="input pr-10"
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                  style={{ color: "var(--text-muted)" }}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-3 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <><LogIn className="w-5 h-5" /> Sign In</>
              )}
            </button>
          </form>

          <p className="text-center text-sm mt-6" style={{ color: "var(--text-muted)" }}>
            Don&apos;t have an account?{" "}
            <Link href="/auth/register" className="font-medium"
                  style={{ color: "var(--accent-primary)" }}>
              Create one
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}

