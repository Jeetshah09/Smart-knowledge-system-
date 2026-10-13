"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Bot,
  Compass,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Settings,
  Sun,
  User as UserIcon,
} from "lucide-react";
import { cn, formatRelative } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/notebooks", label: "My Notebooks", icon: BookOpen },
  { href: "/workspace", label: "AI Workspace", icon: Bot },
  { href: "/studio", label: "AI Studio", icon: Compass },
  { href: "/search", label: "Search", icon: Search },
  { href: "/conversations", label: "Conversations", icon: MessageSquare },
];

const FOOTER_NAV = [
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/profile", label: "Profile", icon: UserIcon },
];

export function Sidebar({
  open,
  onToggle,
  mobileOpen,
  onMobileClose,
}: {
  open: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();

  const content = (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <Bot className="h-5 w-5" />
        </div>
        {open && (
          <span className="text-sm font-semibold leading-tight">
            AI Knowledge
            <span className="block text-[11px] font-normal text-muted-foreground">Management System</span>
          </span>
        )}
      </div>

      <nav className="flex-1 space-y-1 px-2">
        {NAV.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground",
                !open && "justify-center px-2"
              )}
              title={item.label}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {open && <span>{item.label}</span>}
            </Link>
          );
        })}

        <div className="my-3 border-t border-border" />

        {FOOTER_NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground",
                !open && "justify-center px-2"
              )}
              title={item.label}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {open && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-3">
        <div className={cn("flex items-center gap-2", !open && "flex-col")}>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary text-xs font-semibold text-secondary-foreground">
            {user?.name?.slice(0, 2).toUpperCase() || "?"}
          </div>
          {open && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium">{user?.name}</p>
              <p className="truncate text-[11px] text-muted-foreground">
                {user?.email}
              </p>
            </div>
          )}
        </div>
        <div className={cn("mt-2 flex gap-1", !open && "flex-col items-center")}>
          <button
            onClick={toggle}
            className="flex h-8 flex-1 items-center justify-center gap-1.5 rounded-lg text-xs text-muted-foreground hover:bg-muted cursor-pointer"
            title="Toggle theme"
          >
            {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
            {open && (theme === "dark" ? "Light mode" : "Dark mode")}
          </button>
          <button
            onClick={logout}
            className="flex h-8 flex-1 items-center justify-center gap-1.5 rounded-lg text-xs text-muted-foreground hover:bg-muted hover:text-destructive cursor-pointer"
            title="Logout"
          >
            <LogOut className="h-3.5 w-3.5" />
            {open && "Logout"}
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop */}
      <aside
        className={cn(
          "hidden md:block shrink-0 border-r border-border bg-card transition-all duration-200",
          open ? "w-60" : "w-16"
        )}
      >
        <button
          onClick={onToggle}
          className="absolute left-60 top-5 z-10 hidden -translate-x-1/2 rounded-full border border-border bg-card p-1 shadow-sm hover:bg-muted cursor-pointer md:block"
          style={{ left: open ? "15rem" : "4rem" }}
          aria-label="Toggle sidebar"
        >
          {open ? <PanelLeftClose className="h-3.5 w-3.5" /> : <PanelLeftOpen className="h-3.5 w-3.5" />}
        </button>
        <div className="h-full">{content}</div>
      </aside>

      {/* Mobile drawer - only rendered while explicitly opened */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={onMobileClose} />
          <aside className="absolute left-0 top-0 h-full w-64 border-r border-border bg-card">
            {content}
          </aside>
        </div>
      )}
    </>
  );
}
