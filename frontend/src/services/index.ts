"use client";

import { api, unwrap } from "@/lib/api";
import type {
  Conversation,
  DashboardStats,
  GeneratedContent,
  Message,
  Notebook,
  Prompt,
  QuizQuestion,
  Resource,
  User,
  UserSettings,
} from "@/types";

/* ---------------- Auth ---------------- */

export const authService = {
  async register(name: string, email: string, password: string) {
    const data = await unwrap<{ user: User; access_token: string }>(
      api.post("/auth/register", { name, email, password })
    );
    return data;
  },
  async login(email: string, password: string) {
    const data = await unwrap<{ user: User; access_token: string }>(
      api.post("/auth/login", { email, password })
    );
    return data;
  },
  logout() {
    return api.post("/auth/logout").catch(() => null);
  },
  async me() {
    const data = await unwrap<{ user: User }>(api.get("/auth/me"));
    return data.user;
  },
  async updateProfile(payload: { name?: string; profile_image?: string | null }) {
    const data = await unwrap<{ user: User }>(api.put("/auth/me", payload));
    return data.user;
  },
  async changePassword(current_password: string, new_password: string) {
    await api.post("/auth/change-password", { current_password, new_password });
  },
};

/* ---------------- Notebooks ---------------- */

export const notebookService = {
  async list() {
    const data = await unwrap<{ notebooks: Notebook[] }>(api.get("/notebooks"));
    return data.notebooks;
  },
  async get(id: string) {
    const data = await unwrap<{ notebook: Notebook }>(api.get(`/notebooks/${id}`));
    return data.notebook;
  },
  async create(payload: { title: string; description?: string }) {
    const data = await unwrap<{ notebook: Notebook }>(api.post("/notebooks", payload));
    return data.notebook;
  },
  async update(id: string, payload: { title?: string; description?: string }) {
    const data = await unwrap<{ notebook: Notebook }>(api.put(`/notebooks/${id}`, payload));
    return data.notebook;
  },
  async togglePin(id: string) {
    const data = await unwrap<{ is_pinned: boolean }>(api.patch(`/notebooks/${id}/pin`));
    return data.is_pinned;
  },
  async remove(id: string) {
    await api.delete(`/notebooks/${id}`);
  },
};

/* ---------------- Resources ---------------- */

export const resourceService = {
  async listForNotebook(notebookId: string) {
    const data = await unwrap<{ resources: Resource[] }>(
      api.get(`/notebooks/${notebookId}/resources`)
    );
    return data.resources;
  },
  async get(id: string) {
    const data = await unwrap<{ resource: Resource }>(api.get(`/resources/${id}`));
    return data.resource;
  },
  async upload(notebookId: string, file: File) {
    const form = new FormData();
    form.append("file", file);
    const data = await unwrap<{ resource: Resource; message?: string }>(
      api.post(`/resources/upload?notebook_id=${notebookId}`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
    );
    return data.resource;
  },
  async addYouTube(notebookId: string, url: string) {
    const data = await unwrap<{ resource: Resource; message?: string }>(
      api.post("/resources/youtube", { notebook_id: notebookId, url })
    );
    return data.resource;
  },
  async remove(id: string) {
    await api.delete(`/resources/${id}`);
  },
};

/* ---------------- Chat & conversations ---------------- */

export const chatService = {
  async send(payload: {
    notebook_id: string;
    message: string;
    resource_ids: string[];
    conversation_id?: string | null;
  }) {
    const data = await unwrap<{
      conversation_id: string;
      response: string;
      resources_used: number;
    }>(api.post("/chat", payload));
    return data;
  },
};

export const conversationService = {
  async list(notebookId?: string) {
    const data = await unwrap<{ conversations: Conversation[] }>(
      api.get("/conversations", { params: notebookId ? { notebook_id: notebookId } : {} })
    );
    return data.conversations;
  },
  async get(id: string) {
    const data = await unwrap<{ conversation: Conversation }>(api.get(`/conversations/${id}`));
    return data.conversation;
  },
  async messages(id: string) {
    const data = await unwrap<{ messages: Message[] }>(
      api.get(`/conversations/${id}/messages`)
    );
    return data.messages;
  },
  async rename(id: string, title: string) {
    const data = await unwrap<{ conversation: Conversation }>(
      api.patch(`/conversations/${id}`, { title })
    );
    return data.conversation;
  },
  async remove(id: string) {
    await api.delete(`/conversations/${id}`);
  },
};

/* ---------------- AI generation ---------------- */

export const aiService = {
  async summary(notebookId: string, resourceIds: string[]) {
    const data = await unwrap<{ generated_content: GeneratedContent }>(
      api.post("/ai/summary", { notebook_id: notebookId, resource_ids: resourceIds })
    );
    return data.generated_content;
  },
  async quiz(notebookId: string, resourceIds: string[], numberOfQuestions = 10) {
    const data = await unwrap<{ generated_content: GeneratedContent }>(
      api.post("/ai/quiz", {
        notebook_id: notebookId,
        resource_ids: resourceIds,
        number_of_questions: numberOfQuestions,
      })
    );
    return data.generated_content;
  },
  async flashcards(notebookId: string, resourceIds: string[], numberOfCards = 10) {
    const data = await unwrap<{ generated_content: GeneratedContent }>(
      api.post("/ai/flashcards", {
        notebook_id: notebookId,
        resource_ids: resourceIds,
        number_of_cards: numberOfCards,
      })
    );
    return data.generated_content;
  },
  async faq(notebookId: string, resourceIds: string[]) {
    const data = await unwrap<{ generated_content: GeneratedContent }>(
      api.post("/ai/faq", { notebook_id: notebookId, resource_ids: resourceIds })
    );
    return data.generated_content;
  },
  async studyNotes(notebookId: string, resourceIds: string[]) {
    const data = await unwrap<{ generated_content: GeneratedContent }>(
      api.post("/ai/study-notes", { notebook_id: notebookId, resource_ids: resourceIds })
    );
    return data.generated_content;
  },
  async listForNotebook(notebookId: string) {
    const data = await unwrap<{ items: GeneratedContent[] }>(
      api.get(`/ai/notebook/${notebookId}`)
    );
    return data.items;
  },
};

/* ---------------- Prompts (AI Studio) ---------------- */

export const promptService = {
  async list() {
    const data = await unwrap<{ prompts: Prompt[] }>(api.get("/prompts"));
    return data.prompts;
  },
  async create(payload: {
    title: string;
    prompt: string;
    model: string;
    temperature: number;
    max_output_tokens: number;
  }) {
    const data = await unwrap<{ prompt: Prompt }>(api.post("/prompts", payload));
    return data.prompt;
  },
  async remove(id: string) {
    await api.delete(`/prompts/${id}`);
  },
  async execute(id: string, overrides?: { temperature?: number; max_output_tokens?: number }) {
    const data = await unwrap<{ prompt: Prompt }>(
      api.post(`/prompts/${id}/execute`, overrides ?? {})
    );
    return data.prompt;
  },
};

/* ---------------- Search / settings / dashboard ---------------- */

export const searchService = {
  async global(q: string) {
    const data = await unwrap<{
      notebooks: Notebook[];
      resources: Resource[];
      conversations: Conversation[];
      prompts: Prompt[];
    }>(api.get("/search", { params: { q } }));
    return data;
  },
};

export const settingsService = {
  async get() {
    const data = await unwrap<{ settings: UserSettings }>(api.get("/settings"));
    return data.settings;
  },
  async update(payload: Partial<UserSettings>) {
    const data = await unwrap<{ settings: UserSettings }>(api.put("/settings", payload));
    return data.settings;
  },
};

export const dashboardService = {
  async stats() {
    return unwrap<DashboardStats>(api.get("/dashboard/stats"));
  },
};

export type { QuizQuestion };
