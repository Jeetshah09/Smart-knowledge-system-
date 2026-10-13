"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  Bot,
  FileText,
  MessageSquare,
  Plus,
  Sparkles,
  Upload,
} from "lucide-react";
import { Button, Card, EmptyState, Skeleton, toast } from "@/components/ui";
import { dashboardService, notebookService } from "@/services";
import { useAuth } from "@/context/AuthContext";
import { formatRelative } from "@/lib/utils";
import type { DashboardStats, Notebook } from "@/types";

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([dashboardService.stats(), notebookService.list()])
      .then(([s, n]) => {
        setStats(s);
        setNotebooks(n);
      })
      .catch(() => toast("Could not load dashboard data", "error"))
      .finally(() => setLoading(false));
  }, []);

  const cards = [
    { label: "Notebooks", value: stats?.notebook_count ?? 0, icon: BookOpen, href: "/notebooks" },
    { label: "Resources", value: stats?.resource_count ?? 0, icon: FileText, href: "/notebooks" },
    { label: "Conversations", value: stats?.conversation_count ?? 0, icon: MessageSquare, href: "/conversations" },
    { label: "Generated content", value: stats?.generated_content_count ?? 0, icon: Sparkles, href: "/notebooks" },
  ];

  return (
    <div className="mx-auto max-w-6xl p-4 md:p-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Welcome back, {user?.name?.split(" ")[0]}!</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Here is what is happening in your knowledge workspace.
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/notebooks?create=1">
            <Button size="sm">
              <Plus className="h-4 w-4" /> New notebook
            </Button>
          </Link>
          <Link href="/workspace">
            <Button size="sm" variant="outline">
              <Bot className="h-4 w-4" /> AI Workspace
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) =>
          loading ? (
            <Skeleton key={c.label} className="h-28" />
          ) : (
            <Link key={c.label} href={c.href}>
              <Card className="p-5 transition-shadow hover:shadow-md">
                <div className="flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <c.icon className="h-5 w-5" />
                  </div>
                </div>
                <p className="mt-3 text-2xl font-bold">{c.value}</p>
                <p className="text-sm text-muted-foreground">{c.label}</p>
              </Card>
            </Link>
          )
        )}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        {/* Recent notebooks */}
        <div className="lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">Recent notebooks</h2>
            <Link href="/notebooks" className="text-sm text-primary hover:underline">
              View all
            </Link>
          </div>
          {loading ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
            </div>
          ) : notebooks.length === 0 ? (
            <EmptyState
              icon={<BookOpen className="h-8 w-8" />}
              title="No notebooks yet"
              description="Create your first notebook to start learning."
              action={
                <Link href="/notebooks?create=1">
                  <Button size="sm">
                    <Plus className="h-4 w-4" /> Create notebook
                  </Button>
                </Link>
              }
            />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {notebooks.slice(0, 4).map((nb) => (
                <Link key={nb.id} href={`/notebooks/${nb.id}`}>
                  <Card className="h-full p-5 transition-shadow hover:shadow-md">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
                        <BookOpen className="h-5 w-5" />
                      </div>
                      <div className="min-w-0">
                        <p className="truncate font-medium">{nb.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {nb.resource_count ?? 0} resources · {formatRelative(nb.updated_at)}
                        </p>
                      </div>
                    </div>
                    {nb.description && (
                      <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">{nb.description}</p>
                    )}
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recent activity */}
        <div>
          <h2 className="mb-3 font-semibold">Recent activity</h2>
          <Card className="divide-y divide-border">
            {loading ? (
              <div className="p-4">
                <Skeleton className="h-16" />
              </div>
            ) : !stats?.recent_activity?.length ? (
              <div className="p-6 text-center text-sm text-muted-foreground">
                <Upload className="mx-auto mb-2 h-6 w-6 opacity-50" />
                Your activity will appear here.
              </div>
            ) : (
              stats.recent_activity.slice(0, 7).map((a) => (
                <div key={a.id} className="flex items-start gap-3 p-3">
                  <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted text-xs">
                    {a.action.includes("chat") ? "💬" : a.action.includes("notebook") ? "📒" : a.action.includes("resource") ? "📄" : "✨"}
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm">{a.description || a.action}</p>
                    <p className="text-[11px] text-muted-foreground">{formatRelative(a.created_at)}</p>
                  </div>
                </div>
              ))
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
