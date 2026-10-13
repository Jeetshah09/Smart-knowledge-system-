"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  BookOpen,
  FolderSearch,
  MoreVertical,
  Pencil,
  Pin,
  PinOff,
  Plus,
  Trash2,
} from "lucide-react";
import { Badge, Button, Card, Dialog, EmptyState, Input, Label, Skeleton, Textarea, toast } from "@/components/ui";
import { notebookService } from "@/services";
import { formatRelative } from "@/lib/utils";
import type { Notebook } from "@/types";

function NotebooksInner() {
  const router = useRouter();
  const params = useSearchParams();
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  // create / edit dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Notebook | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Notebook | null>(null);
  const [menuFor, setMenuFor] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setNotebooks(await notebookService.list());
    } catch {
      toast("Could not load notebooks", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // Allow deep-link ?create=1 (used by dashboard quick action)
  useEffect(() => {
    if (params.get("create") === "1") {
      setEditing(null);
      setTitle("");
      setDescription("");
      setDialogOpen(true);
      router.replace("/notebooks");
    }
  }, [params, router]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return notebooks;
    return notebooks.filter(
      (n) => n.title.toLowerCase().includes(q) || n.description.toLowerCase().includes(q)
    );
  }, [notebooks, query]);

  const openCreate = () => {
    setEditing(null);
    setTitle("");
    setDescription("");
    setDialogOpen(true);
  };

  const openEdit = (nb: Notebook) => {
    setEditing(nb);
    setTitle(nb.title);
    setDescription(nb.description);
    setDialogOpen(true);
    setMenuFor(null);
  };

  const save = async () => {
    if (!title.trim()) {
      toast("Please give the notebook a title", "error");
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        await notebookService.update(editing.id, { title, description });
        toast("Notebook updated", "success");
      } else {
        const created = await notebookService.create({ title, description });
        toast("Notebook created", "success");
        router.push(`/notebooks/${created.id}`);
        return;
      }
      setDialogOpen(false);
      await load();
    } catch (e) {
      toast("Could not save the notebook", "error");
    } finally {
      setSaving(false);
    }
  };

  const togglePin = async (nb: Notebook) => {
    try {
      await notebookService.togglePin(nb.id);
      await load();
    } catch {
      toast("Could not update pin", "error");
    }
    setMenuFor(null);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await notebookService.remove(deleteTarget.id);
      toast("Notebook deleted", "success");
      setDeleteTarget(null);
      await load();
    } catch {
      toast("Could not delete the notebook", "error");
    }
  };

  return (
    <div className="mx-auto max-w-6xl p-4 md:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">My Notebooks</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Each notebook groups resources, chats and generated knowledge for one topic.
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4" /> Create notebook
        </Button>
      </div>

      <div className="mt-6 max-w-sm">
        <Input placeholder="Search notebooks..." value={query} onChange={(e) => setQuery(e.target.value)} />
      </div>

      <div className="mt-6">
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<FolderSearch className="h-8 w-8" />}
            title={query ? "No notebooks match your search" : "No notebooks yet"}
            description={
              query ? "Try a different search term." : "Create your first notebook to start learning."
            }
            action={
              !query && (
                <Button size="sm" onClick={openCreate}>
                  <Plus className="h-4 w-4" /> Create notebook
                </Button>
              )
            }
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((nb) => (
              <Card key={nb.id} className="group relative p-5 transition-shadow hover:shadow-md">
                <div className="flex items-start justify-between">
                  <Link href={`/notebooks/${nb.id}`} className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
                      <BookOpen className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-medium">{nb.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {nb.resource_count ?? 0} resources · {formatRelative(nb.updated_at)}
                      </p>
                    </div>
                  </Link>
                  <div className="relative">
                    <button
                      onClick={() => setMenuFor(menuFor === nb.id ? null : nb.id)}
                      className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted cursor-pointer"
                      aria-label="Notebook actions"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </button>
                    {menuFor === nb.id && (
                      <div className="absolute right-0 top-9 z-10 w-40 rounded-xl border border-border bg-popover p-1 text-popover-foreground shadow-lg">
                        <Link
                          href={`/notebooks/${nb.id}`}
                          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-muted"
                        >
                          <BookOpen className="h-3.5 w-3.5" /> Open
                        </Link>
                        <button
                          onClick={() => openEdit(nb)}
                          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-muted cursor-pointer"
                        >
                          <Pencil className="h-3.5 w-3.5" /> Rename / edit
                        </button>
                        <button
                          onClick={() => togglePin(nb)}
                          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-muted cursor-pointer"
                        >
                          {nb.is_pinned ? <PinOff className="h-3.5 w-3.5" /> : <Pin className="h-3.5 w-3.5" />}
                          {nb.is_pinned ? "Unpin" : "Pin"}
                        </button>
                        <button
                          onClick={() => {
                            setDeleteTarget(nb);
                            setMenuFor(null);
                          }}
                          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-destructive hover:bg-destructive/10 cursor-pointer"
                        >
                          <Trash2 className="h-3.5 w-3.5" /> Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>
                {nb.description && (
                  <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">{nb.description}</p>
                )}
                {nb.is_pinned && (
                  <Badge variant="secondary" className="mt-3">
                    <Pin className="mr-1 h-3 w-3" /> Pinned
                  </Badge>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? "Edit notebook" : "Create notebook"}
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="nb-title">Title</Label>
            <Input
              id="nb-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Machine Learning Basics"
            />
          </div>
          <div>
            <Label htmlFor="nb-desc">Description (optional)</Label>
            <Textarea
              id="nb-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is this notebook about?"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={save} loading={saving}>
              {editing ? "Save changes" : "Create"}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Delete confirm */}
      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete notebook?">
        <p className="text-sm text-muted-foreground">
          <strong className="text-foreground">{deleteTarget?.title}</strong> and all of its
          resources, conversations and generated content will be permanently deleted.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="outline" onClick={() => setDeleteTarget(null)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Delete
          </Button>
        </div>
      </Dialog>
    </div>
  );
}

export default function NotebooksPage() {
  return (
    <Suspense>
      <NotebooksInner />
    </Suspense>
  );
}
