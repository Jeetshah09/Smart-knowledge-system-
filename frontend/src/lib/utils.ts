export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

export function formatDate(iso?: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

export function formatRelative(iso?: string | null): string {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return formatDate(iso);
}

/**
 * Friendly, provider-neutral model labels. The app speaks in aliases
 * ("fast", "balanced", …); real provider model IDs stay server-side.
 */
const MODEL_DISPLAY_NAMES: Record<string, string> = {
  fast: "Fast (Default)",
  balanced: "Balanced",
  advanced: "Advanced",
  turbo: "Turbo",
};

export function modelDisplayName(model?: string | null): string {
  if (!model) return "AI";
  return MODEL_DISPLAY_NAMES[model] ?? "AI";
}

export function formatSize(bytes?: number | null): string {
  if (!bytes && bytes !== 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
