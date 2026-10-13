import Link from "next/link";
import {
  ArrowRight,
  Bot,
  BookOpen,
  BrainCircuit,
  FileQuestion,
  GraduationCap,
  Layers,
  ListChecks,
  Youtube,
} from "lucide-react";

const FEATURES = [
  {
    icon: Bot,
    title: "AI Chat",
    description: "Ask questions about your documents and get clear, grounded answers.",
  },
  {
    icon: Layers,
    title: "Smart Summaries",
    description: "Turn long documents into short and detailed summaries with key points.",
  },
  {
    icon: ListChecks,
    title: "Quiz Generator",
    description: "Generate multiple-choice quizzes with explanations to test yourself.",
  },
  {
    icon: BrainCircuit,
    title: "Flashcards",
    description: "Create flip-style flashcards from any learning material.",
  },
  {
    icon: Youtube,
    title: "YouTube Learning",
    description: "Add YouTube videos as resources and learn from their transcripts.",
  },
  {
    icon: FileQuestion,
    title: "AI Studio",
    description: "A prompt playground with model, temperature and token controls.",
  },
];

const STEPS = [
  { icon: BookOpen, title: "Create a Notebook", text: "Organize each subject or project into its own notebook." },
  { icon: GraduationCap, title: "Add Learning Resources", text: "Upload PDFs, DOCX, TXT, images or paste a YouTube URL." },
  { icon: Bot, title: "Ask the AI", text: "Chat with your resources and get answers grounded in your content." },
  { icon: ListChecks, title: "Generate Knowledge", text: "Summaries, quizzes, flashcards, FAQs and study notes." },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Nav */}
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <Bot className="h-5 w-5" />
            </div>
            <span className="font-semibold">AI Knowledge</span>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              Log in
            </Link>
            <Link
              href="/register"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_50%_at_50%_0%,--theme(--color-primary/12%),transparent)]" />
        <div className="mx-auto max-w-6xl px-4 py-24 text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
            <BrainCircuit className="h-3.5 w-3.5 text-primary" /> Powered by Advanced AI
          </span>
          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-bold tracking-tight sm:text-6xl">
            Your Personal{" "}
            <span className="bg-gradient-to-r from-primary to-sky-500 bg-clip-text text-transparent">
              AI Knowledge
            </span>{" "}
            Assistant
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
            Upload your learning resources, ask questions, understand complex topics and turn
            information into interactive knowledge.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 font-medium text-primary-foreground shadow-sm hover:opacity-90"
            >
              Get Started <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-6 py-3 font-medium hover:bg-muted"
            >
              Explore Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-center text-3xl font-bold">Everything you need to learn faster</h2>
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 font-semibold">{f.title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-border bg-card/50">
        <div className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="text-center text-3xl font-bold">How it works</h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((s, i) => (
              <div key={s.title} className="relative rounded-2xl border border-border bg-card p-6">
                <span className="absolute right-4 top-4 text-4xl font-bold text-muted-foreground/20">
                  {i + 1}
                </span>
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
                  <s.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 font-semibold">{s.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{s.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-8 text-sm text-muted-foreground sm:flex-row">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4" /> AI Smart Knowledge Management System
          </div>
          <p>B.Tech Minor Project · FastAPI · MongoDB · Next.js · AI-Powered</p>
        </div>
      </footer>
    </div>
  );
}
