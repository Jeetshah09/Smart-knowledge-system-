"use client";

import Link from "next/link";
import { useState } from "react";
import { Bot, MailCheck } from "lucide-react";
import { Button, Input, Label } from "@/components/ui";

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const [email, setEmail] = useState("");

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center gap-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
            <Bot className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold">Reset your password</h1>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          {sent ? (
            <div className="text-center">
              <MailCheck className="mx-auto h-10 w-10 text-primary" />
              <p className="mt-3 font-medium">Instructions sent</p>
              <p className="mt-1 text-sm text-muted-foreground">
                If an account exists for <strong>{email}</strong>, password reset instructions
                would be emailed. For this minor-project build, please contact the administrator
                to reset your password.
              </p>
              <Link href="/login" className="mt-4 inline-block text-sm font-medium text-primary hover:underline">
                Back to login
              </Link>
            </div>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                setSent(true);
              }}
            >
              <div className="mb-4">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                />
              </div>
              <Button type="submit" className="w-full">
                Send reset instructions
              </Button>
              <p className="mt-4 text-center text-sm text-muted-foreground">
                Remembered it?{" "}
                <Link href="/login" className="font-medium text-primary hover:underline">
                  Log in
                </Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
