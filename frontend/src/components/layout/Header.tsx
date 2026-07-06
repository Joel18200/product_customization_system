"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import { Sparkles, User, LogOut, LayoutDashboard, Menu, X } from "lucide-react";
import { useState, useEffect } from "react";

export default function Header() {
  const { isAuthenticated, user, logout, hydrate } = useAuthStore();
  const [mobileOpen, setMobileOpen] = useState(false);
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  // Restore session from storage after mount to avoid SSR hydration mismatch.
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <header className="glass sticky top-0 z-50" style={{ borderTop: "none", borderLeft: "none", borderRight: "none" }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center"
                 style={{ background: "#000000" }}>
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold gradient-text">CustomForge</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1">
            <Link href="/products" className="btn-ghost text-sm">
              Products
            </Link>
            {isAuthenticated && (
              <Link href="/dashboard" className="btn-ghost text-sm">
                My Designs
              </Link>
            )}
            {user?.is_staff && (
              <Link href="/admin" className="btn-ghost text-sm">
                <LayoutDashboard className="w-4 h-4 inline mr-1" />
                Admin
              </Link>
            )}
          </nav>

          {/* Auth */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  <User className="w-4 h-4 inline mr-1" />
                  {user?.username || "User"}
                </span>
                <button onClick={handleLogout} className="btn-ghost text-sm">
                  <LogOut className="w-4 h-4 inline mr-1" />
                  Logout
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link href="/auth/login" className="btn-ghost text-sm">
                  Sign In
                </Link>
                <Link href="/auth/register" className="btn-primary text-sm">
                  Get Started
                </Link>
              </div>
            )}
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden btn-ghost"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile Nav */}
        {mobileOpen && (
          <div className="md:hidden pb-4 animate-fade-in">
            <div className="flex flex-col gap-1">
              <Link href="/products" className="btn-ghost text-sm" onClick={() => setMobileOpen(false)}>
                Products
              </Link>
              {isAuthenticated && (
                <Link href="/dashboard" className="btn-ghost text-sm" onClick={() => setMobileOpen(false)}>
                  My Designs
                </Link>
              )}
              {user?.is_staff && (
                <Link href="/admin" className="btn-ghost text-sm" onClick={() => setMobileOpen(false)}>
                  Admin
                </Link>
              )}
              <hr style={{ borderColor: "var(--border-subtle)" }} className="my-2" />
              {isAuthenticated ? (
                <button onClick={() => { handleLogout(); setMobileOpen(false); }} className="btn-ghost text-sm text-left">
                  Logout
                </button>
              ) : (
                <>
                  <Link href="/auth/login" className="btn-ghost text-sm" onClick={() => setMobileOpen(false)}>
                    Sign In
                  </Link>
                  <Link href="/auth/register" className="btn-primary text-sm text-center" onClick={() => setMobileOpen(false)}>
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
