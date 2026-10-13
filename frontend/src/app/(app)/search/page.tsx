"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, FileText, MessageSquare, Search as SearchIcon, Sparkles } from "lucide-react";
import { Badge, Card, EmptyState, Input, Skeleton, toast } from "@/components/ui";
import { searchService } from "@/services";
import { formatRelative } from "@/lib/utils";
import type { Conversation, Notebook, Prompt, Resource } from "@/types";

type Results = {
  notebooks: Notebook[];
  resources: Resource[];
  conversations: Conversation[];
  prompts: Prompt[];
};

const EMPTY: Results = { notebooks: [], resources: [], conversations: [], prompts: [] };

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Results | null>(null);
  const [searching, setSearching] = useState(false);

  // Debounced search
  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setResults(null);
      return;
    }
    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        setResults(await searchService.global(q));
      } catch {
        toast("Search failed", "error");
      } finally {
        setSearching(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [query]);

  const total = results
    ? results.notebooks.length + results.resources.length + results.conversations.length + results.prompts.length
    : 0;

  return (
    <div className="mx-auto max-w-4xl p-4 md:p-8">
      <h1 className="text-2xl font-bold">Search</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Find anything across your notebooks, resources, conversations and prompts.
      </p>

      <div className="relative mt-6">
        <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search everything..."
          className="pl-9"
        />
      </div>

      <div className="mt-6 space-y-6">
        {searching && <Skeleton className="h-24" />}

        {!searching && results && total === 0 && (
          <EmptyState
            icon={<SearchIcon className="h-8 w-8" />}
            title={`No results for "${query}"`}
            description="Try a different search term."
          />
        )}

        {results && results.notebooks.length > 0 && (
          <section>
            <h2 className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
              <BookOpen className="h-4 w-4 text-primary" /> Notebooks
            </h2>
            <div className="space-y-2">
              {results.notebooks.map((n) => (
                <Link key={n.id} href={`/notebooks/${n.id}`}>
                  <Card className="p-3 hover:bg-muted/50">
                    <p className="text-sm font-medium">{n.title}</p>
                    {n.description && (
                      <p className="truncate text-xs text-muted-foreground">{n.description}</p>
                    )}
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        )}

        {results && results.resources.length > 0 && (
          <section>
            <h2 className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
              <FileText className="h-4 w-4 text-primary" /> Resources
            </h2>
            <div className="space-y-2">
              {results.resources.map((r) => (
                <Link key={r.id} href={`/notebooks/${r.notebook_id}`}>
                  <Card className="p-3 hover:bg-muted/50">
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-medium">{r.name}</p>
                      <Badge variant="outline">{r.type}</Badge>
                    </div>
                    {r.content_preview && (
                      <p className="truncate text-xs text-muted-foreground">{r.content_preview}</p>
                    )}
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        )}

        {results && results.conversations.length > 0 && (
          <section>
            <h2 className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
              <MessageSquare className="h-4 w-4 text-primary" /> Conversations
            </h2>
            <div className="space-y-2">
              {results.conversations.map((c) => (
                <Link key={c.id} href={`/workspace?notebook=${c.notebook_id}&conversation=${c.id}`}>
                  <Card className="p-3 hover:bg-muted/50">
                    <p className="truncate text-sm font-medium">{c.title}</p>
                    <p className="text-xs text-muted-foreground">{formatRelative(c.updated_at)}</p>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        )}

        {results && results.prompts.length > 0 && (
          <section>
            <h2 className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
              <Sparkles className="h-4 w-4 text-primary" /> Prompts
            </h2>
            <div className="space-y-2">
              {results.prompts.map((p) => (
                <Link key={p.id} href="/studio">
                  <Card className="p-3 hover:bg-muted/50">
                    <p className="truncate text-sm font-medium">{p.title}</p>
                    <p className="truncate text-xs text-muted-foreground">{p.prompt}</p>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
