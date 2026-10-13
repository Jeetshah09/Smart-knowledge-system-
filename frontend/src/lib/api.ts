"use client";

import axios, { AxiosError } from "axios";
import type { ApiEnvelope } from "@/types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const TOKEN_KEY = "askms_token";

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 180000, // AI generations can take a while (backend retries + fallbacks)
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem(TOKEN_KEY);
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

/** Hide AI provider branding before showing backend messages to users. */
function sanitizeProviderBranding(message: string): string {
  if (/api[_ ]?key/i.test(message)) {
    return "The AI service is not configured yet. Please try again later.";
  }
  return message.replace(/google\s+gemini|gemini|google/gi, "AI");
}

/** Extract a readable message from any backend/axios error. */
export function getErrorMessage(error: unknown): string {
  let msg: string;
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as
      | { detail?: string | Array<{ msg?: string; loc?: (string | number)[] }>; message?: string }
      | undefined;
    if (typeof data?.detail === "string") msg = data.detail;
    else if (Array.isArray(data?.detail) && data.detail.length > 0) {
      // FastAPI validation error: surface the first problem, e.g. "email: value is not a valid email address"
      const first = data.detail[0];
      const field = Array.isArray(first.loc) ? String(first.loc[first.loc.length - 1]) : "input";
      msg = `${field}: ${first.msg ?? "invalid value"}`;
    } else if (typeof data?.message === "string") msg = data.message;
    else if (error.code === "ECONNABORTED")
      msg = "The AI took too long to respond. Please try again in a moment.";
    else if (!error.response)
      msg = "Cannot reach the server. Is the backend running on port 8000?";
    else msg = "Something went wrong. Please try again.";
  } else {
    msg = "Something went wrong. Please try again.";
  }
  return sanitizeProviderBranding(msg);
}

/** Unwrap the backend {success, message, data} envelope. */
export async function unwrap<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  const response = await promise;
  return response.data.data;
}
