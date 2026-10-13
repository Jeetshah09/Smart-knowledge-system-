"use client";

import { useEffect, useState } from "react";
import { Bell, Bot, Moon, Palette, UserCog } from "lucide-react";
import { Button, Card, Label, Skeleton, toast } from "@/components/ui";
import { settingsService } from "@/services";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { modelDisplayName } from "@/lib/utils";
import type { UserSettings } from "@/types";

// Provider-neutral model aliases; the backend resolves them server-side.
const MODELS = ["fast", "balanced", "advanced", "turbo"];

export default function SettingsPage() {
  const { logout } = useAuth();
  const { setTheme } = useTheme();
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    settingsService
      .get()
      .then(setSettings)
      .catch(() => toast("Could not load settings", "error"));
  }, []);

  const save = async (patch: Partial<UserSettings>) => {
    setSaving(true);
    try {
      const updated = await settingsService.update(patch);
      setSettings(updated);
      if (patch.theme) setTheme(patch.theme);
      toast("Settings saved", "success");
    } catch {
      toast("Could not save settings", "error");
    } finally {
      setSaving(false);
    }
  };

  if (!settings) {
    return (
      <div className="mx-auto max-w-2xl p-4 md:p-8">
        <Skeleton className="h-40" />
        <Skeleton className="mt-4 h-40" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl p-4 md:p-8">
      <h1 className="flex items-center gap-2 text-2xl font-bold">
        <Palette className="h-6 w-6 text-primary" /> Settings
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">Customize your experience.</p>

      {/* Appearance */}
      <Card className="mt-6 p-5">
        <h2 className="font-semibold">Appearance</h2>
        <div className="mt-3 flex gap-2">
          {(["light", "dark", "system"] as const).map((t) => (
            <button
              key={t}
              onClick={() => save({ theme: t })}
              className={`flex flex-1 flex-col items-center gap-1.5 rounded-xl border p-4 text-sm capitalize cursor-pointer ${
                settings.theme === t ? "border-primary bg-primary/5 text-primary" : "border-border hover:bg-muted"
              }`}
            >
              <Moon className="h-4 w-4" />
              {t}
            </button>
          ))}
        </div>
      </Card>

      {/* Notifications */}
      <Card className="mt-4 p-5">
        <h2 className="flex items-center gap-1.5 font-semibold">
          <Bell className="h-4 w-4 text-primary" /> Notifications
        </h2>
        <label className="mt-3 flex items-center justify-between">
          <span className="text-sm">Enable notifications</span>
          <input
            type="checkbox"
            checked={settings.notifications}
            onChange={(e) => save({ notifications: e.target.checked })}
            className="h-5 w-9 cursor-pointer appearance-none rounded-full bg-muted transition-colors checked:bg-primary relative before:absolute before:top-0.5 before:left-0.5 before:h-4 before:w-4 before:rounded-full before:bg-white before:transition-transform checked:before:translate-x-4"
          />
        </label>
      </Card>

      {/* AI preferences */}
      <Card className="mt-4 p-5">
        <h2 className="flex items-center gap-1.5 font-semibold">
          <Bot className="h-4 w-4 text-primary" /> AI preferences
        </h2>
        <div className="mt-3 space-y-4">
          <div>
            <Label>Default model</Label>
            <select
              value={settings.default_model}
              onChange={(e) => save({ default_model: e.target.value })}
              className="w-full rounded-lg border border-input bg-card px-2 py-2 text-sm"
            >
              {MODELS.map((m) => (
                <option key={m} value={m}>
                  {modelDisplayName(m)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Response style</Label>
            <div className="flex gap-2">
              {(["concise", "balanced", "detailed"] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => save({ response_style: s })}
                  className={`flex-1 rounded-lg border px-3 py-2 text-sm capitalize cursor-pointer ${
                    settings.response_style === s
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border hover:bg-muted"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Account */}
      <Card className="mt-4 p-5">
        <h2 className="flex items-center gap-1.5 font-semibold">
          <UserCog className="h-4 w-4 text-primary" /> Account
        </h2>
        <div className="mt-3 space-y-3">
          <Button variant="outline" onClick={logout}>
            Log out
          </Button>
          <p className="text-xs text-muted-foreground">
            To delete your account and data, contact the administrator (see README).
          </p>
        </div>
      </Card>
    </div>
  );
}
