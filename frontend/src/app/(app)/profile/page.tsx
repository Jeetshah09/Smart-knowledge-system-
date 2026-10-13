"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { KeyRound, UserRound } from "lucide-react";
import { Button, Card, Input, Label, toast } from "@/components/ui";
import { authService } from "@/services";
import { useAuth } from "@/context/AuthContext";
import { getErrorMessage } from "@/lib/api";
import { useEffect, useState } from "react";

const nameSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
});
const passwordSchema = z
  .object({
    current: z.string().min(1, "Current password is required"),
    next: z.string().min(6, "New password must be at least 6 characters"),
    confirm: z.string(),
  })
  .refine((d) => d.next === d.confirm, {
    message: "Passwords do not match",
    path: ["confirm"],
  });

export default function ProfilePage() {
  const { user, refresh, logout } = useAuth();

  const nameForm = useForm<{ name: string }>({ resolver: zodResolver(nameSchema) });
  const pwForm = useForm({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current: "", next: "", confirm: "" },
  });
  const [savingName, setSavingName] = useState(false);
  const [savingPw, setSavingPw] = useState(false);

  useEffect(() => {
    if (user) nameForm.reset({ name: user.name });
  }, [user, nameForm]);

  const saveName = async (values: { name: string }) => {
    setSavingName(true);
    try {
      await authService.updateProfile({ name: values.name });
      await refresh();
      toast("Profile updated", "success");
    } catch (e) {
      toast(getErrorMessage(e), "error");
    } finally {
      setSavingName(false);
    }
  };

  const savePassword = async (values: { current: string; next: string }) => {
    setSavingPw(true);
    try {
      await authService.changePassword(values.current, values.next);
      pwForm.reset();
      toast("Password changed", "success");
    } catch (e) {
      toast(getErrorMessage(e), "error");
    } finally {
      setSavingPw(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl p-4 md:p-8">
      <h1 className="flex items-center gap-2 text-2xl font-bold">
        <UserRound className="h-6 w-6 text-primary" /> Profile
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">Manage your account details.</p>

      <Card className="mt-6 p-5">
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-secondary text-lg font-semibold text-secondary-foreground">
            {user?.name?.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <p className="font-medium">{user?.name}</p>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
          </div>
        </div>
      </Card>

      <Card className="mt-4 p-5">
        <h2 className="font-semibold">Edit name</h2>
        <form onSubmit={nameForm.handleSubmit(saveName)} className="mt-3 space-y-3">
          <div>
            <Label htmlFor="p-name">Full name</Label>
            <Input id="p-name" {...nameForm.register("name")} />
            {nameForm.formState.errors.name && (
              <p className="mt-1 text-xs text-destructive">{nameForm.formState.errors.name.message}</p>
            )}
          </div>
          <Button type="submit" loading={savingName}>
            Save changes
          </Button>
        </form>
      </Card>

      <Card className="mt-4 p-5">
        <h2 className="flex items-center gap-1.5 font-semibold">
          <KeyRound className="h-4 w-4 text-primary" /> Change password
        </h2>
        <form onSubmit={pwForm.handleSubmit(savePassword)} className="mt-3 space-y-3">
          <div>
            <Label htmlFor="p-current">Current password</Label>
            <Input id="p-current" type="password" {...pwForm.register("current")} />
            {pwForm.formState.errors.current && (
              <p className="mt-1 text-xs text-destructive">{pwForm.formState.errors.current.message}</p>
            )}
          </div>
          <div>
            <Label htmlFor="p-next">New password</Label>
            <Input id="p-next" type="password" {...pwForm.register("next")} />
            {pwForm.formState.errors.next && (
              <p className="mt-1 text-xs text-destructive">{pwForm.formState.errors.next.message}</p>
            )}
          </div>
          <div>
            <Label htmlFor="p-confirm">Confirm new password</Label>
            <Input id="p-confirm" type="password" {...pwForm.register("confirm")} />
            {pwForm.formState.errors.confirm && (
              <p className="mt-1 text-xs text-destructive">{pwForm.formState.errors.confirm.message}</p>
            )}
          </div>
          <Button type="submit" loading={savingPw}>
            Update password
          </Button>
        </form>
      </Card>
    </div>
  );
}
