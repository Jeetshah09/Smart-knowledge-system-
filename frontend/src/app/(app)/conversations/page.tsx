"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MessageSquare, Pencil, Trash2 } from "lucide-react";
import { Button, Card, Dialog, EmptyState, Input, Label, Skeleton, toast } from "@/components/ui";
import { conversationService, notebookService } from "@/services";
import { formatRelative } from "@/lib/utils";
import type { Conversation, Notebook } from "@/types";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[] | null>(null);
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [query, setQuery] = useState("");
  const [renaming, setRenaming] = useState<Conversation | null>(null);
  const [newTitle, setNewTitle] = useState("");

  useEffect(() => {
    conversationService
      .list()
      .then(setConversations)
      .catch(() => {
        setConversations([]);
        toast("Could not load conversations", "error");
      });
    notebookService.list().then(setNotebooks).catch(() => null);
  }, []);

  const notebookTitle = (id: string) => notebooks.find((n) => n.id === id)?.title ?? "Notebook";

  const filtered = (conversations ?? []).filter(
    (c) =>
      c.title.toLowerCase().includes(query.toLowerCase()) ||
      (c.last_message ?? "").toLowerCase().includes(query.toLowerCase())
  );

  const rename = async () => {
    if (!renaming || !newTitle.trim()) return;
    try {
      await conversationService.rename(renaming.id, newTitle.trim());
      setConversations((prev) =>
        (prev ?? []).map((c) => (c.id === renaming.id ? { ...c, title: newTitle.trim() } : c))
      );
      toast("Conversation renamed", "success");
      setRenaming(null);
    } catch {
      toast("Could not rename conversation", "error");
    }
  };

  const remove = async (c: Conversation) => {
    try {
      await conversationService.remove(c.id);
      setConversations((prev) => (prev ?? []).filter((x) => x.id !== c.id));
      toast("Conversation deleted", "success");
    } catch {
      toast("Could not delete conversation", "error");
    }
  };

  return (
    <div className="mx-auto max-w-4xl p-4 md:p-8">
      <h1 className="text-2xl font-bold">Conversations</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Every chat with your resources is saved here.
      </p>

      <div className="mt-6 max-w-sm">
        <Input placeholder="Search conversations..." value={query} onChange={(e) => setQuery(e.target.value)} />
      </div>

      <div className="mt-6 space-y-3">
        {conversations === null ? (
          <Skeleton className="h-24" />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<MessageSquare className="h-8 w-8" />}
            title={query ? "No conversations match your search" : "No conversations yet"}
            description="Start a conversation with your knowledge in the AI Workspace."
            action={
              <Link href="/workspace">
                <Button size="sm">Open AI Workspace</Button>
              </Link>
            }
          />
        ) : (
          filtered.map((c) => (
            <Card key={c.id} className="flex items-center gap-3 p-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <MessageSquare className="h-5 w-5" />
              </div>
              <Link href={`/workspace?notebook=${c.notebook_id}&conversation=${c.id}`} className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{c.title}</p>
                <p className="truncate text-xs text-muted-foreground">{c.last_message || "No messages"}</p>
                <p className="mt-0.5 text-[11px] text-muted-foreground">
                  {notebookTitle(c.notebook_id)} · {c.message_count ?? 0} messages ·{" "}
                  {formatRelative(c.updated_at)}
                </p>
              </Link>
              <div className="flex shrink-0 gap-1">
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => {
                    setRenaming(c);
                    setNewTitle(c.title);
                  }}
                  title="Rename"
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button size="icon" variant="ghost" onClick={() => remove(c)} title="Delete">
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>

      <Dialog open={!!renaming} onClose={() => setRenaming(null)} title="Rename conversation">
        <div className="space-y-4">
          <div>
            <Label htmlFor="c-title">Title</Label>
            <Input id="c-title" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setRenaming(null)}>
              Cancel
            </Button>
            <Button onClick={rename}>Save</Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
