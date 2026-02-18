/**
 * API Types - Matches backend ChatResponse and StepImage models exactly
 */

// Fallback text structure for when image generation fails
export interface FallbackText {
  action: string;
  method: string;
  caution: string;
  result: string;
}

// Step image from backend - one per treatment step
export interface StepImage {
  step_number: string;
  title: string;
  description: string;
  image_prompt?: string | null;
  image?: string | null;           // Base64 (fallback for local dev)
  image_url?: string | null;       // S3 URL (production)
  s3_key?: string | null;          // S3 key (history regeneration)
  is_composite: boolean;
  panel_index?: number | null;
  image_failed: boolean;
  fallback_text?: FallbackText | null;
}

// Main chat response from backend
export interface ChatResponse {
  answer: string;
  original_query: string;
  detected_language: string;
  topic?: string | null;
  step_images?: StepImage[] | null;
  steps_count: number;
  // Legacy fields
  image?: string | null;
  images?: string[] | null;
}

// Chat request to backend
export interface ChatRequest {
  query: string;
  language?: string;
  generate_images?: boolean;
  conversation_history?: ConversationMessage[];
  thinking_mode?: boolean;
  attachments?: Attachment[];
}

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface Attachment {
  filename: string;
  content_type: string;
  data?: string;  // Base64 encoded (optional if s3_key provided)
  s3_key?: string; // S3 Key for large files
  type: 'pdf' | 'image';
}

// Health check response
export interface HealthResponse {
  status: string;
  version: string;
  model: string;
}

// Auth config response
export interface AuthConfigResponse {
  userPoolId: string;
  clientId: string;
  region: string;
}

// User info
export interface UserInfo {
  user_id: string;
  email: string;
  name: string;
}

// Chat history item
export interface ChatHistoryItem {
  chat_id: string;
  query: string;
  topic: string;
  timestamp: number;
  created_at: string;
  has_images: boolean;
}

export interface ChatDetailResponse {
  chat_id: string;
  query: string;
  response: string;
  images: string[];
  step_images?: StepImage[];
  topic: string;
  language: string;
  timestamp: number;
  created_at: string;
}

// SSE stream event types from /chat/stream endpoint
export type StreamEvent =
  | { type: 'token'; text: string }
  | { type: 'metadata'; topic: string | null; detected_language: string }
  | { type: 'step_images'; data: StepImage[] }
  | { type: 'done' }
  | { type: 'error'; message: string };

