"use client";

import { useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { UserPlus, Loader2, ChevronLeft } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

export default function RegisterPage() {
  const { register, isLoading, error, clearError } = useAuthStore();
  const router = useRouter();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    password_confirm: "",
    first_name: "",
    last_name: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      await register(form);
      toast.success("Account created! Please sign in.");
      router.push("/auth/login");
    } catch {
      // Error handled by store
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
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
            <h1 className="text-2xl font-bold mb-2">Create Account</h1>
            <p style={{ color: "var(--text-secondary)" }} className="text-sm">
              Start customizing products today
            </p>
          </div>

          {error && (
            <div className="mb-6 p-3 rounded-lg text-sm"
                 style={{ background: "rgba(239, 68, 68, 0.1)", color: "var(--error)" }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
                  First Name
                </label>
                <input type="text" className="input" placeholder="John"
                       value={form.first_name}
                       onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
                  Last Name
                </label>
                <input type="text" className="input" placeholder="Doe"
                       value={form.last_name}
                       onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
                Username *
              </label>
              <input type="text" className="input" placeholder="johndoe" required
                     value={form.username}
                     onChange={(e) => setForm({ ...form, username: e.target.value })} />
            </div>

            <div>
              <label className="text-sm font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
                Email *
              </label>
              <input type="email" className="input" placeholder="john@example.com" required
                     value={form.email}
                     onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>

            <div>
              <label className="text-sm font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
                Password *
              </label>
              <input type="password" className="input" placeholder="Min 8 characters" required
                     value={form.password}
                     onChange={(e) => setForm({ ...form, password: e.target.value })} />
            </div>

            <div>
              <label className="text-sm font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
                Confirm Password *
              </label>
              <input type="password" className="input" placeholder="Re-enter password" required
                     value={form.password_confirm}
                     onChange={(e) => setForm({ ...form, password_confirm: e.target.value })} />
            </div>

            <button type="submit" disabled={isLoading}
                    className="btn-primary w-full py-3 flex items-center justify-center gap-2">
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <><UserPlus className="w-5 h-5" /> Create Account</>
              )}
            </button>
          </form>

          <p className="text-center text-sm mt-6" style={{ color: "var(--text-muted)" }}>
            Already have an account?{" "}
            <Link href="/auth/login" className="font-medium"
                  style={{ color: "var(--accent-primary)" }}>
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}

