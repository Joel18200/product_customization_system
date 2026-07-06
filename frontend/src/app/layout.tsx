"use client";

import "./globals.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { useState } from "react";
import Header from "@/components/layout/Header";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <html lang="en">
      <head>
        <title>CustomForge — Product Customization Platform</title>
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1, viewport-fit=cover"
        />
        <meta
          name="description"
          content="Design and customize products with realistic rendering. Upload your artwork and see it come to life on real products."
        />
      </head>
      <body className="antialiased min-h-screen">
        <QueryClientProvider client={queryClient}>
          <Header />
          <main>{children}</main>
          <Toaster
            theme="light"
            position="bottom-right"
            toastOptions={{
              style: {
                background: "var(--bg-card)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-primary)",
              },
            }}
          />
        </QueryClientProvider>
      </body>
    </html>
  );
}
