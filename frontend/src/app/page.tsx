"use client";

import Link from "next/link";
import { motion } from "framer-motion";

export default function HomePage() {
  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4 py-10 sm:py-16">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center w-full max-w-lg mx-auto"
      >
        <h1 className="font-bold mb-4 sm:mb-6 gradient-text tracking-tight"
            style={{ fontSize: "clamp(2.5rem, 8vw, 6rem)", lineHeight: 1.05 }}>
          CustomForge
        </h1>
        <p className="mb-10 sm:mb-14 px-2" style={{ color: "var(--text-secondary)", fontSize: "clamp(1.1rem, 4vw, 2rem)" }}>
          Product Customization System
        </p>

        <div className="flex flex-col sm:flex-row gap-4 sm:gap-5 justify-center items-stretch sm:items-center">
          <Link href="/auth/login"
                className="btn-primary w-full sm:w-auto px-8 sm:px-16 py-4 sm:py-5 text-lg sm:text-xl">
            Log In
          </Link>
          <Link href="/auth/register"
                className="btn-secondary w-full sm:w-auto px-8 sm:px-16 py-4 sm:py-5 text-lg sm:text-xl">
            Sign Up
          </Link>
        </div>

        <p className="mt-6 sm:mt-8 text-sm sm:text-base" style={{ color: "var(--text-muted)" }}>
          New here? Create an account to get started.
        </p>
      </motion.div>
    </div>
  );
}
