"use client";

import { useEffect, useState } from "react";
import { Menu } from "lucide-react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Toaster } from "@/components/ui";

export function AppShell({ children }: { children: React.ReactNode }) {
  // `open` only drives the desktop sidebar (expanded / collapsed).
  const [open, setOpen] = useState(true);
  // The mobile drawer must start CLOSED: while open it is a full-screen
  // fixed overlay (z-40) that swallows every click on the page, which is why
  // "Save prompt" / "Generate" silently did nothing on narrow screens.
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  // Close the drawer after navigating, so page content is reachable again.
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <div className="flex min-h-screen">
      <Sidebar
        open={open}
        onToggle={() => setOpen((v) => !v)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile topbar */}
        <div className="flex items-center gap-3 border-b border-border bg-card px-4 py-3 md:hidden">
          <button
            onClick={() => setMobileOpen(true)}
            className="rounded-lg p-1.5 hover:bg-muted cursor-pointer"
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </button>
          <span className="font-semibold text-sm">AI Knowledge</span>
        </div>
        <main className="flex-1 min-w-0">{children}</main>
      </div>
      <Toaster />
    </div>
  );
}
