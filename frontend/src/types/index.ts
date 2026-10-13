export type Resource = {
  id: string;
  notebook_id: string;
  name: string;
  type: "pdf" | "docx" | "txt" | "image" | "youtube";
  file_path?: string | null;
  youtube_url?: string | null;
  file_size?: number | null;
  mime_type?: string | null;
  content?: string;
  content_preview?: string;
  has_content?: boolean;
  processing_status: "uploaded" | "processing" | "completed" | "failed";
  created_at?: string;
  updated_at?: string;
};

export type Notebook = {
  id: string;
  title: string;
  description: string;
  is_pinned: boolean;
  resource_count?: number;
  created_at?: string;
  updated_at?: string;
};

export type Message = {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
};

export type Conversation = {
  id: string;
  notebook_id: string;
  title: string;
  message_count?: number;
  last_message?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type QuizQuestion = {
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
};

export type Flashcard = {
  question: string;
  answer: string;
  explanation?: string;
};

export type GeneratedContent = {
  id: string;
  notebook_id: string;
  resource_ids?: string[];
  type: "summary" | "quiz" | "flashcards" | "faq" | "study_notes";
  title: string;
  content: {
    short_summary?: string;
    detailed_summary?: string;
    key_points?: string[];
    questions?: QuizQuestion[];
    cards?: Flashcard[];
    faqs?: { question: string; answer: string }[];
    title?: string;
    overview?: string;
    important_concepts?: { name: string; explanation: string }[];
    conclusion?: string;
  };
  created_at?: string;
};

export type Prompt = {
  id: string;
  title: string;
  prompt: string;
  model: string;
  temperature: number;
  max_output_tokens: number;
  response?: string | null;
  /** Where the prompt came from: AI Studio or the AI Workspace chat. */
  source?: "studio" | "workspace";
  created_at?: string;
};

export type UserSettings = {
  theme: "light" | "dark" | "system";
  notifications: boolean;
  default_model: string;
  response_style: "concise" | "balanced" | "detailed";
};

export type User = {
  id: string;
  name: string;
  email: string;
  profile_image?: string | null;
  is_active?: boolean;
  created_at?: string;
};

export type DashboardStats = {
  notebook_count: number;
  resource_count: number;
  conversation_count: number;
  generated_content_count: number;
  recent_activity: {
    id: string;
    action: string;
    description: string;
    metadata?: Record<string, unknown>;
    created_at?: string;
  }[];
};

export type ApiEnvelope<T = unknown> = {
  success: boolean;
  message: string;
  data: T;
};
