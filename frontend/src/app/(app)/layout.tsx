"use client";

import { AppShell } from "@/components/layout/AppShell";
import { useRequireAuth } from "@/context/AuthContext";
import { Spinner } from "@/components/ui";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useRequireAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }
  if (!user) return null;

  return <AppShell>{children}</AppShell>;
}
