"use client";

import { useEffect, useState } from "react";
import { Copy, Play, Save, Sparkles, Trash2, Wand2 } from "lucide-react";
import { Button, Card, EmptyState, Input, Label, Skeleton, Textarea, toast } from "@/components/ui";
import { promptService } from "@/services";
import { getErrorMessage } from "@/lib/api";
import { formatRelative, modelDisplayName } from "@/lib/utils";
import type { Prompt } from "@/types";

// Provider-neutral model aliases; the backend resolves them server-side.
const MODELS = ["fast", "balanced", "advanced", "turbo"];

const EXAMPLES = [
  "Explain Artificial Intelligence for a beginner.",
  "Create 10 MCQs about Machine Learning.",
  "Write a short essay on the importance of data structures.",
];

export default function StudioPage() {
  const [promptText, setPromptText] = useState("");
  const [title, setTitle] = useState("");
  const [model, setModel] = useState(MODELS[0]);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1000);

  const [response, setResponse] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [history, setHistory] = useState<Prompt[] | null>(null);

  const loadHistory = () => {
    promptService
      .list()
      .then(setHistory)
      .catch(() => setHistory([]));
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const run = async () => {
    if (!promptText.trim()) {
      toast("Write a prompt first", "error");
      return;
    }
    setGenerating(true);
    setResponse(null);
    try {
      const saved = await promptService.create({
        title: title.trim() || promptText.trim().slice(0, 60),
        prompt: promptText,
        model,
        temperature,
        max_output_tokens: maxTokens,
      });
      // Show the saved prompt in history immediately - execution can be slow
      // (rate limits / model fallbacks), and the row must not appear "lost".
      loadHistory();
      const executed = await promptService.execute(saved.id, {
        temperature,
        max_output_tokens: maxTokens,
      });
      setResponse(executed.response || "(empty response)");
      loadHistory();
    } catch (e) {
      // Surface the real cause (expired session, rate limit, backend down)
      // instead of a generic message - otherwise failures look identical.
      toast(getErrorMessage(e), "error");
    } finally {
      setGenerating(false);
    }
  };

  const saveOnly = async () => {
    if (!promptText.trim()) {
      toast("Write a prompt first", "error");
      return;
    }
    setSaving(true);
    try {
      await promptService.create({
        title: title.trim() || promptText.trim().slice(0, 60),
        prompt: promptText,
        model,
        temperature,
        max_output_tokens: maxTokens,
      });
      toast("Prompt saved", "success");
      loadHistory();
    } catch (e) {
      toast(getErrorMessage(e), "error");
    } finally {
      setSaving(false);
    }
  };

  const executeSaved = async (p: Prompt) => {
    setPromptText(p.prompt);
    setTitle(p.title);
    setModel(p.model);
    setTemperature(p.temperature);
    setMaxTokens(p.max_output_tokens);
    setGenerating(true);
    setResponse(null);
    try {
      const executed = await promptService.execute(p.id);
      setResponse(executed.response || "(empty response)");
      loadHistory();
    } catch (e) {
      toast(getErrorMessage(e), "error");
    } finally {
      setGenerating(false);
    }
  };

  const removeSaved = async (p: Prompt) => {
    try {
      await promptService.remove(p.id);
      setHistory((prev) => (prev ? prev.filter((x) => x.id !== p.id) : prev));
      toast("Prompt deleted", "success");
    } catch (e) {
      toast(getErrorMessage(e), "error");
    }
  };

  return (
    <div className="mx-auto max-w-6xl p-4 md:p-8">
      <div className="flex items-center gap-2">
        <Wand2 className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">AI Studio</h1>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        A prompt playground — experiment with instructions and settings, then save what works.
      </p>

      <div className="mt-6 grid gap-6 lg:grid-cols-5">
        {/* Left: editor */}
        <div className="space-y-4 lg:col-span-3">
          <Card className="p-4">
            <Label htmlFor="p-title">Title (optional)</Label>
            <Input
              id="p-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. MCQ generator"
            />
            <div className="mt-3">
              <Label htmlFor="p-text">Prompt</Label>
              <Textarea
                id="p-text"
                rows={8}
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                placeholder="Write your prompt here..."
              />
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => setPromptText(ex)}
                  className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground hover:bg-muted cursor-pointer"
                >
                  {ex}
                </button>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <Label>Model</Label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full rounded-lg border border-input bg-card px-2 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {MODELS.map((m) => (
                <option key={m} value={m}>
                  {modelDisplayName(m)}
                </option>
              ))}
            </select>

            <div className="mt-4">
              <Label>
                Temperature: <span className="text-primary">{temperature.toFixed(1)}</span>
              </Label>
              <input
                type="range"
                min={0}
                max={2}
                step={0.1}
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-[var(--primary)]"
              />
              <p className="mt-1 text-xs text-muted-foreground">Lower = focused, higher = creative</p>
            </div>

            <div className="mt-4">
              <Label>
                Max output tokens: <span className="text-primary">{maxTokens}</span>
              </Label>
              <input
                type="range"
                min={256}
                max={8192}
                step={256}
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full accent-[var(--primary)]"
              />
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              <Button onClick={run} loading={generating}>
                <Play className="h-4 w-4" /> Generate
              </Button>
              <Button variant="outline" onClick={saveOnly} loading={saving}>
                <Save className="h-4 w-4" /> Save prompt
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setPromptText("");
                  setResponse(null);
                }}
              >
                <Trash2 className="h-4 w-4" /> Clear
              </Button>
            </div>
          </Card>
        </div>

        {/* Right: response + history */}
        <div className="space-y-4 lg:col-span-2">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-1.5 text-sm font-semibold">
                <Sparkles className="h-4 w-4 text-primary" /> Response
              </h2>
              {response && (
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(response);
                    toast("Copied", "success");
                  }}
                  className="text-muted-foreground hover:text-foreground cursor-pointer"
                  aria-label="Copy response"
                >
                  <Copy className="h-4 w-4" />
                </button>
              )}
            </div>
            <div className="mt-3 min-h-48 whitespace-pre-wrap text-sm">
              {generating ? (
                <p className="animate-pulse text-muted-foreground">Generating…</p>
              ) : response ? (
                response
              ) : (
                <p className="text-muted-foreground">
                  The AI response will appear here. Configure the settings and click Generate.
                </p>
              )}
            </div>
          </Card>

          <Card className="p-4">
            <h2 className="text-sm font-semibold">
              Prompt history{history && history.length > 0 ? ` (${history.length})` : ""}
            </h2>
            <div className="mt-3 space-y-2">
              {history === null ? (
                <Skeleton className="h-20" />
              ) : history.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No saved prompts yet — prompts you run here and in the AI Workspace are stored here.
              </p>
              ) : (
                history.slice(0, 8).map((p) => (
                  <div key={p.id} className="rounded-lg border border-border p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">
                          {p.title}
                          {p.source === "workspace" && (
                            <span className="ml-1.5 inline-block rounded-full border border-border px-1.5 py-0.5 align-middle text-[10px] font-normal text-muted-foreground">
                              workspace
                            </span>
                          )}
                        </p>
                        <p className="text-[11px] text-muted-foreground">
                          {modelDisplayName(p.model)} · temp {p.temperature} · {formatRelative(p.created_at)}
                          {p.response ? " · executed" : ""}
                        </p>
                      </div>
                      <div className="flex shrink-0 gap-1">
                        <Button size="sm" variant="ghost" onClick={() => executeSaved(p)} title="Run again">
                          <Play className="h-3.5 w-3.5" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => removeSaved(p)} title="Delete">
                          <Trash2 className="h-3.5 w-3.5 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))
              )}
              {history !== null && history.length > 8 && (
                <p className="pt-1 text-[11px] text-muted-foreground">
                  Showing the latest 8 of {history.length} saved prompts — older ones are still in the database.
                </p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
