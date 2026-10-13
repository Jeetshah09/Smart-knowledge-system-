"use client";

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  BookOpen,
  BrainCircuit,
  Check,
  ChevronLeft,
  ChevronRight,
  Copy,
  FileImage,
  FileText,
  FileType2,
  HelpCircle,
  ListChecks,
  NotebookPen,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  RefreshCw,
  Send,
  Sparkles,
  Square,
  Layers,
  Youtube,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  Skeleton,
  Textarea,
  TypingDots,
  toast,
} from "@/components/ui";
import {
  aiService,
  chatService,
  conversationService,
  notebookService,
  resourceService,
} from "@/services";
import { cn, formatRelative } from "@/lib/utils";
import { getErrorMessage } from "@/lib/api";
import type { Conversation, GeneratedContent, Message, Notebook, Resource } from "@/types";

const TYPE_ICONS: Record<string, typeof FileText> = {
  pdf: FileType2,
  docx: FileText,
  txt: FileText,
  image: FileImage,
  youtube: Youtube,
};

const SUGGESTIONS = [
  "Summarize this document",
  "What are the important points?",
  "Explain this topic simply",
  "Generate 10 MCQs",
  "Create flashcards",
];

const AI_ACTIONS = [
  { key: "summary", label: "Summarize", icon: Layers },
  { key: "key_points", label: "Key Points", icon: Sparkles },
  { key: "faq", label: "FAQ", icon: HelpCircle },
  { key: "quiz", label: "Quiz", icon: ListChecks },
  { key: "flashcards", label: "Flashcards", icon: BrainCircuit },
  { key: "study_notes", label: "Study Notes", icon: NotebookPen },
] as const;

type AiAction = (typeof AI_ACTIONS)[number]["key"];

const GENERATING_MESSAGES = [
  "Generating your content…",
  "Reading through your sources…",
  "Analyzing your materials…",
  "Connecting the dots for you…",
  "Distilling the key ideas…",
  "Crunching the details…",
  "Putting everything together…",
  "Diving deep into your sources…",
  "Working on it — hang tight…",
  "Crafting something useful…",
];

export default function WorkspacePage() {
  return (
    <Suspense>
      <WorkspaceInner />
    </Suspense>
  );
}

function WorkspaceInner() {
  const params = useSearchParams();
  const notebookIdFromUrl = params.get("notebook");
  const conversationIdFromUrl = params.get("conversation");

  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [activeNotebookId, setActiveNotebookId] = useState<string>(notebookIdFromUrl || "");
  const [resources, setResources] = useState<Resource[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(conversationIdFromUrl);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingThread, setLoadingThread] = useState(false);
  const [busyAction, setBusyAction] = useState<AiAction | null>(null);
  const [loadingMessage, setLoadingMessage] = useState(GENERATING_MESSAGES[0]);
  const [result, setResult] = useState<GeneratedContent | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [sourcesOpen, setSourcesOpen] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  /* ---------------- data loading ---------------- */

  useEffect(() => {
    notebookService
      .list()
      .then(setNotebooks)
      .catch(() => toast("Could not load notebooks", "error"));
  }, []);

  const loadNotebookData = useCallback(async (nbId: string) => {
    if (!nbId) return;
    try {
      const [res, convs] = await Promise.all([
        resourceService.listForNotebook(nbId),
        conversationService.list(nbId),
      ]);
      setResources(res);
      setSelected(new Set(res.map((r) => r.id))); // select all by default
      setConversations(convs);
    } catch {
      toast("Could not load notebook data", "error");
    }
  }, []);

  useEffect(() => {
    if (activeNotebookId) void loadNotebookData(activeNotebookId);
  }, [activeNotebookId, loadNotebookData]);

  const loadThread = useCallback(async (convId: string) => {
    setLoadingThread(true);
    try {
      setMessages(await conversationService.messages(convId));
    } catch {
      toast("Could not load messages", "error");
    } finally {
      setLoadingThread(false);
    }
  }, []);

  useEffect(() => {
    if (activeConversationId) void loadThread(activeConversationId);
    else setMessages([]);
  }, [activeConversationId, loadThread]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  /* rotate the loading message while an AI action is running */
  useEffect(() => {
    if (!busyAction) return;
    const id = setInterval(() => {
      setLoadingMessage(
        GENERATING_MESSAGES[Math.floor(Math.random() * GENERATING_MESSAGES.length)]
      );
    }, 4000);
    return () => clearInterval(id);
  }, [busyAction]);

  /* ---------------- chat ---------------- */

  const send = async (text?: string) => {
    const message = (text ?? input).trim();
    if (!message) return;
    if (!activeNotebookId) {
      toast("Select a notebook first", "error");
      return;
    }
    if (selected.size === 0) {
      toast("Select at least one source on the left", "error");
      return;
    }

    setSending(true);
    const optimistic: Message = {
      id: `tmp-${Date.now()}`,
      conversation_id: activeConversationId || "",
      role: "user",
      content: message,
    };
    setMessages((prev) => [...prev, optimistic]);
    setInput("");

    try {
      const data = await chatService.send({
        notebook_id: activeNotebookId,
        message,
        resource_ids: [...selected],
        conversation_id: activeConversationId,
      });
      setActiveConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          conversation_id: data.conversation_id,
          role: "assistant",
          content: data.response,
        },
      ]);
      // refresh conversation list for new title
      conversationService
        .list(activeNotebookId)
        .then(setConversations)
        .catch(() => null);
    } catch (e) {
      setMessages((prev) => prev.filter((m) => m.id !== optimistic.id));
      toast(getErrorMessage(e), "error");
    } finally {
      setSending(false);
    }
  };

  /* ---------------- AI actions ---------------- */

  const runAction = async (action: AiAction) => {
    if (!activeNotebookId || selected.size === 0) {
      toast("Select a notebook and at least one source first", "error");
      return;
    }
    setBusyAction(action);
    setShowResult(true);
    setLoadingMessage(
      GENERATING_MESSAGES[Math.floor(Math.random() * GENERATING_MESSAGES.length)]
    );
    try {
      let gen: GeneratedContent;
      const ids = [...selected];
      if (action === "summary" || action === "key_points") {
        gen = await aiService.summary(activeNotebookId, ids);
      } else if (action === "quiz") {
        gen = await aiService.quiz(activeNotebookId, ids, 10);
      } else if (action === "flashcards") {
        gen = await aiService.flashcards(activeNotebookId, ids, 10);
      } else if (action === "faq") {
        gen = await aiService.faq(activeNotebookId, ids);
      } else {
        gen = await aiService.studyNotes(activeNotebookId, ids);
      }
      setResult(gen);
    } catch (e) {
      toast(getErrorMessage(e), "error");
      setShowResult(false);
    } finally {
      setBusyAction(null);
    }
  };

  const toggleSource = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectedResources = resources.filter((r) => selected.has(r.id));

  /* ---------------- render ---------------- */

  return (
    <div className="flex h-[calc(100vh-49px)] md:h-screen">
      {/* Sources panel */}
      <aside
        className={cn(
          "flex w-72 shrink-0 flex-col border-r border-border bg-card transition-all",
          !sourcesOpen && "md:w-14"
        )}
      >
        <div className="flex items-center justify-between px-3 py-3">
          {sourcesOpen && <h2 className="text-sm font-semibold">Sources</h2>}
          <button
            onClick={() => setSourcesOpen((v) => !v)}
            className="rounded-lg p-1.5 hover:bg-muted cursor-pointer"
            aria-label="Toggle sources panel"
          >
            {sourcesOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
          </button>
        </div>

        {sourcesOpen && (
          <>
            <div className="px-3 pb-2">
              <select
                value={activeNotebookId}
                onChange={(e) => {
                  setActiveNotebookId(e.target.value);
                  setActiveConversationId(null);
                  setResult(null);
                  setShowResult(false);
                }}
                className="w-full rounded-lg border border-input bg-card px-2 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">Select a notebook…</option>
                {notebooks.map((nb) => (
                  <option key={nb.id} value={nb.id}>
                    {nb.title}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex-1 space-y-1 overflow-y-auto px-2 pb-2">
              {resources.length === 0 ? (
                <p className="px-2 py-6 text-center text-xs text-muted-foreground">
                  {activeNotebookId ? (
                    <>
                      No sources yet.{" "}
                      <Link href={`/notebooks/${activeNotebookId}`} className="text-primary hover:underline">
                        Upload resources
                      </Link>
                    </>
                  ) : (
                    "Select a notebook to see its sources."
                  )}
                </p>
              ) : (
                resources.map((r) => {
                  const Icon = TYPE_ICONS[r.type] || FileText;
                  const isSel = selected.has(r.id);
                  return (
                    <button
                      key={r.id}
                      onClick={() => toggleSource(r.id)}
                      className={cn(
                        "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm transition-colors cursor-pointer",
                        isSel ? "bg-primary/10 text-primary" : "hover:bg-muted"
                      )}
                    >
                      <span
                        className={cn(
                          "flex h-4 w-4 shrink-0 items-center justify-center rounded border",
                          isSel ? "border-primary bg-primary text-primary-foreground" : "border-input"
                        )}
                      >
                        {isSel && <Check className="h-3 w-3" />}
                      </span>
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="min-w-0 flex-1 truncate">{r.name}</span>
                      {r.has_content === false && <Badge variant="outline">no text</Badge>}
                    </button>
                  );
                })
              )}
            </div>

            {/* Conversations list */}
            <div className="border-t border-border p-2">
              <p className="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                History
              </p>
              <div className="max-h-40 space-y-0.5 overflow-y-auto">
                {conversations.length === 0 && (
                  <p className="px-2 py-2 text-xs text-muted-foreground">No conversations yet.</p>
                )}
                {conversations.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => {
                      setActiveConversationId(c.id);
                      setShowResult(false);
                    }}
                    className={cn(
                      "flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs cursor-pointer",
                      activeConversationId === c.id ? "bg-secondary text-secondary-foreground" : "hover:bg-muted"
                    )}
                  >
                    <span className="min-w-0 flex-1 truncate">{c.title}</span>
                    <span className="text-[10px] text-muted-foreground">{formatRelative(c.updated_at)}</span>
                  </button>
                ))}
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="mt-1 w-full"
                onClick={() => {
                  setActiveConversationId(null);
                  setMessages([]);
                  setShowResult(false);
                }}
              >
                <Plus className="h-3.5 w-3.5" /> New chat
              </Button>
            </div>
          </>
        )}
      </aside>

      {/* Main chat area */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* AI action bar */}
        <div className="flex flex-wrap items-center gap-1.5 border-b border-border bg-card/50 px-3 py-2">
          {AI_ACTIONS.map((a) => (
            <Button
              key={a.key}
              size="sm"
              variant={busyAction === a.key ? "primary" : "outline"}
              loading={busyAction === a.key}
              onClick={() => runAction(a.key)}
              className="text-xs"
            >
              <a.icon className="h-3.5 w-3.5" /> {a.label}
            </Button>
          ))}
        </div>

        {/* Result panel (summaries / quiz / flashcards) */}
        {(showResult || busyAction) && (
          <div className="border-b border-border bg-muted/30 px-4 py-4">
            <div className="mx-auto max-w-3xl">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-semibold">
                  {AI_ACTIONS.find((a) => a.key === (busyAction ?? result?.type))?.label ?? "Result"}
                </h3>
                <button
                  onClick={() => setShowResult(false)}
                  className="text-xs text-muted-foreground hover:text-foreground cursor-pointer"
                >
                  Close
                </button>
              </div>
              {busyAction ? (
                <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
                  <TypingDots /> {loadingMessage}
                </div>
              ) : (
                result && <ResultView gen={result} />
              )}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl space-y-4 px-4 py-6">
            {loadingThread ? (
              <div className="space-y-3">
                <Skeleton className="h-12" />
                <Skeleton className="h-20" />
              </div>
            ) : messages.length === 0 ? (
              <div className="pt-10 text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                  <Sparkles className="h-7 w-7" />
                </div>
                <h2 className="mt-4 text-xl font-semibold">Ask anything about your sources</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Answers are grounded in the resources you select.
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="rounded-full border border-border bg-card px-3.5 py-1.5 text-sm hover:bg-muted cursor-pointer"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m) => (
                <div
                  key={m.id}
                  className={cn("flex gap-3", m.role === "user" ? "justify-end" : "justify-start")}
                >
                  {m.role === "assistant" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                      <Sparkles className="h-4 w-4" />
                    </div>
                  )}
                  <div
                    className={cn(
                      "max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm",
                      m.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "border border-border bg-card"
                    )}
                  >
                    {m.content}
                    {m.role === "assistant" && (
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(m.content);
                          toast("Copied to clipboard", "success");
                        }}
                        className="ml-2 inline-flex align-middle text-muted-foreground hover:text-foreground cursor-pointer"
                        aria-label="Copy message"
                      >
                        <Copy className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
            {sending && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div className="rounded-2xl border border-border bg-card px-4 py-3">
                  <TypingDots />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Composer */}
        <div className="border-t border-border bg-card/50 px-4 py-3">
          <div className="mx-auto flex max-w-3xl items-end gap-2">
            <Textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send();
                }
              }}
              placeholder="Ask anything about your sources..."
              className="max-h-40 min-h-[44px] flex-1 resize-none"
            />
            <Button onClick={() => send()} loading={sending} size="lg" className="shrink-0">
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="mx-auto mt-1.5 max-w-3xl text-[11px] text-muted-foreground">
            Answering from {selectedResources.length} selected source(s)
            {selectedResources.length > 0 && `: ${selectedResources.map((r) => r.name).join(", ")}`}
          </p>
        </div>
      </div>
    </div>
  );
}

/* ---------------- result views ---------------- */

function ResultView({ gen }: { gen: GeneratedContent }) {
  const c = gen.content;

  if (gen.type === "summary") {
    return (
      <div className="space-y-3 text-sm">
        <Card className="p-4">
          <h4 className="font-semibold">Short summary</h4>
          <p className="mt-1 text-muted-foreground">{c.short_summary}</p>
        </Card>
        <Card className="p-4">
          <h4 className="font-semibold">Detailed summary</h4>
          <p className="mt-1 whitespace-pre-wrap text-muted-foreground">{c.detailed_summary}</p>
        </Card>
        {c.key_points && c.key_points.length > 0 && (
          <Card className="p-4">
            <h4 className="font-semibold">Key points</h4>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
              {c.key_points.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    );
  }

  if (gen.type === "quiz" && c.questions) {
    return <QuizView questions={c.questions} />;
  }

  if (gen.type === "flashcards" && c.cards) {
    return <FlashcardsView cards={c.cards} />;
  }

  if (gen.type === "faq" && c.faqs) {
    return (
      <div className="space-y-2">
        {c.faqs.map((f, i) => <FaqItem key={i} question={f.question} answer={f.answer} />)}
      </div>
    );
  }

  if (gen.type === "study_notes") {
    return (
      <div className="space-y-3 text-sm">
        <Card className="p-4">
          <h4 className="font-semibold">{c.title}</h4>
          <p className="mt-1 text-muted-foreground">{c.overview}</p>
        </Card>
        {c.important_concepts && c.important_concepts.length > 0 && (
          <Card className="p-4">
            <h4 className="font-semibold">Important concepts</h4>
            <div className="mt-2 space-y-2">
              {c.important_concepts.map((k, i) => (
                <div key={i}>
                  <p className="font-medium">{k.name}</p>
                  <p className="text-muted-foreground">{k.explanation}</p>
                </div>
              ))}
            </div>
          </Card>
        )}
        {c.key_points && c.key_points.length > 0 && (
          <Card className="p-4">
            <h4 className="font-semibold">Key points</h4>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
              {c.key_points.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
          </Card>
        )}
        {c.conclusion && (
          <Card className="p-4">
            <h4 className="font-semibold">Conclusion</h4>
            <p className="mt-1 text-muted-foreground">{c.conclusion}</p>
          </Card>
        )}
      </div>
    );
  }

  return null;
}

function QuizView({ questions }: { questions: QuizQuestionT[] }) {
  const [idx, setIdx] = useState(0);
  const [picked, setPicked] = useState<string | null>(null);
  const [score, setScore] = useState(0);
  const [done, setDone] = useState(false);

  if (questions.length === 0) return <p className="text-sm text-muted-foreground">No questions generated.</p>;

  if (done) {
    return (
      <Card className="p-6 text-center">
        <p className="text-3xl font-bold">
          {score} / {questions.length}
        </p>
        <p className="mt-1 text-sm text-muted-foreground">Quiz completed</p>
        <Button
          className="mt-4"
          onClick={() => {
            setIdx(0);
            setPicked(null);
            setScore(0);
            setDone(false);
          }}
        >
          <RefreshCw className="h-4 w-4" /> Retry quiz
        </Button>
      </Card>
    );
  }

  const q = questions[idx];
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          Question {idx + 1} of {questions.length}
        </span>
        <span>Score: {score}</span>
      </div>
      <h4 className="mt-2 font-medium">{q.question}</h4>
      <div className="mt-3 space-y-2">
        {q.options.map((opt) => (
          <button
            key={opt}
            onClick={() => picked === null && setPicked(opt)}
            className={cn(
              "flex w-full items-center gap-2 rounded-lg border px-3 py-2 text-left text-sm transition-colors cursor-pointer",
              picked === null && "hover:bg-muted",
              picked !== null && opt === q.correct_answer && "border-green-500 bg-green-500/10",
              picked === opt && opt !== q.correct_answer && "border-destructive bg-destructive/10",
              picked !== null && opt !== q.correct_answer && picked !== opt && "opacity-60"
            )}
          >
            <span className="flex h-5 w-5 items-center justify-center rounded-full border border-border text-[10px]">
              {String.fromCharCode(65 + q.options.indexOf(opt))}
            </span>
            {opt}
          </button>
        ))}
      </div>
      {picked !== null && (
        <div className="mt-3 rounded-lg bg-muted p-3 text-sm">
          <p className="font-medium">
            {picked === q.correct_answer ? "✅ Correct!" : "❌ Incorrect"}
          </p>
          <p className="mt-1 text-muted-foreground">{q.explanation}</p>
        </div>
      )}
      <div className="mt-4 flex justify-end">
        <Button
          size="sm"
          disabled={picked === null}
          onClick={() => {
            if (picked === q.correct_answer) setScore((s) => s + 1);
            if (idx + 1 >= questions.length) setDone(true);
            else {
              setIdx((i) => i + 1);
              setPicked(null);
            }
          }}
        >
          {idx + 1 >= questions.length ? "Finish" : "Next question"}
        </Button>
      </div>
    </Card>
  );
}

function FlashcardsView({ cards }: { cards: FlashcardT[] }) {
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);

  if (cards.length === 0) return <p className="text-sm text-muted-foreground">No cards generated.</p>;

  const card = cards[idx];
  return (
    <div className="text-center">
      <p className="mb-2 text-xs text-muted-foreground">
        Card {idx + 1} of {cards.length} · click the card to flip
      </p>
      <button
        onClick={() => setFlipped((f) => !f)}
        className="flex min-h-44 w-full items-center justify-center rounded-2xl border border-border bg-card p-6 text-left shadow-sm transition-transform hover:scale-[1.01] cursor-pointer"
      >
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-primary">
            {flipped ? "Answer" : "Question"}
          </p>
          <p className="mt-2 whitespace-pre-wrap">{flipped ? card.answer : card.question}</p>
          {flipped && card.explanation && (
            <p className="mt-2 text-sm text-muted-foreground">{card.explanation}</p>
          )}
        </div>
      </button>
      <div className="mt-3 flex items-center justify-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={idx === 0}
          onClick={() => {
            setIdx((i) => i - 1);
            setFlipped(false);
          }}
        >
          <ChevronLeft className="h-4 w-4" /> Prev
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={idx === cards.length - 1}
          onClick={() => {
            setIdx((i) => i + 1);
            setFlipped(false);
          }}
        >
          Next <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function FaqItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);
  return (
    <Card className="overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-3 p-4 text-left text-sm font-medium cursor-pointer"
      >
        {question}
        <ChevronRight className={cn("h-4 w-4 shrink-0 transition-transform", open && "rotate-90")} />
      </button>
      {open && <p className="border-t border-border px-4 py-3 text-sm text-muted-foreground">{answer}</p>}
    </Card>
  );
}

type QuizQuestionT = {
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
};
type FlashcardT = {
  question: string;
  answer: string;
  explanation?: string;
};
