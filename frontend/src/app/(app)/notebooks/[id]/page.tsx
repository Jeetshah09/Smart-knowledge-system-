"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Bot,
  FileImage,
  FileText,
  FileType2,
  Loader2,
  MessageSquare,
  Pencil,
  Plus,
  Trash2,
  Upload,
  Youtube,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  Dialog,
  EmptyState,
  Input,
  Label,
  Skeleton,
  Textarea,
  toast,
} from "@/components/ui";
import { aiService, conversationService, notebookService, resourceService } from "@/services";
import { getErrorMessage } from "@/lib/api";
import { formatRelative, formatSize } from "@/lib/utils";
import type { Conversation, GeneratedContent, Notebook, Resource } from "@/types";

const TYPE_ICONS: Record<string, typeof FileText> = {
  pdf: FileType2,
  docx: FileText,
  txt: FileText,
  image: FileImage,
  youtube: Youtube,
};

export default function NotebookDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);

  const [notebook, setNotebook] = useState<Notebook | null>(null);
  const [resources, setResources] = useState<Resource[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [generated, setGenerated] = useState<GeneratedContent[]>([]);
  const [loading, setLoading] = useState(true);

  const [editOpen, setEditOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

  const [ytOpen, setYtOpen] = useState(false);
  const [ytUrl, setYtUrl] = useState("");
  const [ytBusy, setYtBusy] = useState(false);

  const [uploading, setUploading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [nb, res, convs, gen] = await Promise.all([
        notebookService.get(id),
        resourceService.listForNotebook(id),
        conversationService.list(id),
        aiService.listForNotebook(id),
      ]);
      setNotebook(nb);
      setResources(res);
      setConversations(convs);
      setGenerated(gen);
      setTitle(nb.title);
      setDescription(nb.description);
    } catch {
      toast("Notebook not found", "error");
      router.replace("/notebooks");
    } finally {
      setLoading(false);
    }
  }, [id, router]);

  useEffect(() => {
    void load();
  }, [load]);

  const onPickFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    setUploading(true);
    let okCount = 0;
    for (const file of Array.from(files)) {
      try {
        await resourceService.upload(id, file);
        okCount++;
      } catch (e) {
        toast(`Failed to upload ${file.name}`, "error");
      }
    }
    setUploading(false);
    if (okCount) toast(`${okCount} resource(s) uploaded and processed`, "success");
    await load();
  };

  const addYouTube = async () => {
    if (!ytUrl.trim()) return;
    setYtBusy(true);
    try {
      const r = await resourceService.addYouTube(id, ytUrl.trim());
      toast(
        r.processing_status === "completed"
          ? "YouTube video added with transcript"
          : "Video added — no transcript was available for it",
        r.processing_status === "completed" ? "success" : "info"
      );
      setYtOpen(false);
      setYtUrl("");
      await load();
    } catch (e) {
      toast(getErrorMessage(e), "error");
    } finally {
      setYtBusy(false);
    }
  };

  const deleteResource = async (r: Resource) => {
    try {
      await resourceService.remove(r.id);
      setResources((prev) => prev.filter((x) => x.id !== r.id));
      toast("Resource deleted", "success");
    } catch {
      toast("Could not delete the resource", "error");
    }
  };

  const saveEdit = async () => {
    setSaving(true);
    try {
      await notebookService.update(id, { title, description });
      toast("Notebook updated", "success");
      setEditOpen(false);
      await load();
    } catch {
      toast("Could not update the notebook", "error");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl p-4 md:p-8">
        <Skeleton className="h-10 w-72" />
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <Skeleton className="h-72 lg:col-span-2" />
          <Skeleton className="h-72" />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl p-4 md:p-8">
      <Link
        href="/notebooks"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> All notebooks
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold">{notebook?.title}</h1>
          {notebook?.description && (
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{notebook.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}>
            <Pencil className="h-4 w-4" /> Edit
          </Button>
          <Link href={`/workspace?notebook=${id}`}>
            <Button size="sm">
              <Bot className="h-4 w-4" /> Open AI Workspace
            </Button>
          </Link>
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        {/* Resources */}
        <div className="lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">Learning resources ({resources.length})</h2>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => setYtOpen(true)}>
                <Youtube className="h-4 w-4" /> YouTube URL
              </Button>
              <Button size="sm" onClick={() => fileInput.current?.click()} loading={uploading}>
                <Upload className="h-4 w-4" /> Upload
              </Button>
              <input
                ref={fileInput}
                type="file"
                multiple
                accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.webp"
                className="hidden"
                onChange={(e) => onPickFiles(e.target.files)}
              />
            </div>
          </div>

          {resources.length === 0 ? (
            <EmptyState
              icon={<Upload className="h-8 w-8" />}
              title="No resources yet"
              description="Upload a PDF, DOCX, TXT or image, or add a YouTube video to start learning."
              action={
                <Button size="sm" onClick={() => fileInput.current?.click()}>
                  <Plus className="h-4 w-4" /> Upload resource
                </Button>
              }
            />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {resources.map((r) => {
                const Icon = TYPE_ICONS[r.type] || FileText;
                return (
                  <Card key={r.id} className="flex items-start gap-3 p-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{r.name}</p>
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {r.type.toUpperCase()} · {formatSize(r.file_size) || "—"} ·{" "}
                        {formatRelative(r.created_at)}
                      </p>
                      <div className="mt-2">
                        {r.processing_status === "completed" && r.has_content && (
                          <Badge variant="success">Processed</Badge>
                        )}
                        {r.processing_status === "completed" && !r.has_content && (
                          <Badge variant="secondary">Saved (no text)</Badge>
                        )}
                        {r.processing_status === "failed" && (
                          <Badge variant="warning">No text extracted</Badge>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => deleteResource(r)}
                      className="rounded-lg p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive cursor-pointer"
                      aria-label={`Delete ${r.name}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </Card>
                );
              })}
            </div>
          )}

          {/* Generated content */}
          <h2 className="mb-3 mt-8 font-semibold">Generated content</h2>
          {generated.length === 0 ? (
            <EmptyState
              icon={<Loader2 className="h-8 w-8 opacity-30" />}
              title="Nothing generated yet"
              description="Open the AI Workspace and use the action buttons to generate summaries, quizzes and more."
            />
          ) : (
            <div className="space-y-3">
              {generated.slice(0, 6).map((g) => (
                <Card key={g.id} className="p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <Badge variant="default">{g.type.replace("_", " ")}</Badge>
                      <p className="mt-1.5 text-sm font-medium">{g.title}</p>
                    </div>
                    <Link href={`/workspace?notebook=${id}`} className="text-xs text-primary hover:underline">
                      View in workspace
                    </Link>
                  </div>
                  {"short_summary" in g.content && g.content.short_summary && (
                    <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{g.content.short_summary}</p>
                  )}
                  <p className="mt-2 text-[11px] text-muted-foreground">{formatRelative(g.created_at)}</p>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Conversations */}
        <div>
          <h2 className="mb-3 font-semibold">Conversations</h2>
          {conversations.length === 0 ? (
            <EmptyState
              icon={<MessageSquare className="h-8 w-8" />}
              title="No conversations yet"
              description="Start a conversation with your knowledge in the AI Workspace."
              action={
                <Link href={`/workspace?notebook=${id}`}>
                  <Button size="sm">
                    <Bot className="h-4 w-4" /> Start chatting
                  </Button>
                </Link>
              }
            />
          ) : (
            <Card className="divide-y divide-border">
              {conversations.map((c) => (
                <Link
                  key={c.id}
                  href={`/workspace?notebook=${id}&conversation=${c.id}`}
                  className="block p-3 hover:bg-muted/50"
                >
                  <p className="truncate text-sm font-medium">{c.title}</p>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">
                    {c.last_message || "No messages"}
                  </p>
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    {c.message_count ?? 0} messages · {formatRelative(c.updated_at)}
                  </p>
                </Link>
              ))}
            </Card>
          )}
        </div>
      </div>

      {/* Edit dialog */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)} title="Edit notebook">
        <div className="space-y-4">
          <div>
            <Label htmlFor="nb-title">Title</Label>
            <Input id="nb-title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="nb-desc">Description</Label>
            <Textarea id="nb-desc" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setEditOpen(false)}>
              Cancel
            </Button>
            <Button onClick={saveEdit} loading={saving}>
              Save
            </Button>
          </div>
        </div>
      </Dialog>

      {/* YouTube dialog */}
      <Dialog open={ytOpen} onClose={() => setYtOpen(false)} title="Add YouTube video">
        <div className="space-y-4">
          <div>
            <Label htmlFor="yt-url">YouTube URL</Label>
            <Input
              id="yt-url"
              value={ytUrl}
              onChange={(e) => setYtUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
            />
          </div>
          <p className="text-xs text-muted-foreground">
            The backend will try to fetch the video transcript. If none is available, the video is
            still added and you can ask general questions about it.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setYtOpen(false)}>
              Cancel
            </Button>
            <Button onClick={addYouTube} loading={ytBusy}>
              Add video
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
