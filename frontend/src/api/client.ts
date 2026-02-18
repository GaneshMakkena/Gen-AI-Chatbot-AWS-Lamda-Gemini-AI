/**
 * API Client for MediBot Backend
 * Handles all HTTP requests with proper timeout handling
 */

import type { ChatRequest, ChatResponse, HealthResponse } from '../types/api';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://khucwqfzv4.execute-api.us-east-1.amazonaws.com/production';

// Timeout: 310 seconds (exceeds Lambda 300s limit)
const REQUEST_TIMEOUT_MS = 310000;

class ApiError extends Error {
    status: number;
    code?: string;

    constructor(
        message: string,
        status: number,
        code?: string
    ) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.code = code;
    }
}

async function fetchWithTimeout(
    url: string,
    options: RequestInit,
    timeoutMs: number = REQUEST_TIMEOUT_MS
): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
        });
        return response;
    } finally {
        clearTimeout(timeoutId);
    }
}

export async function healthCheck(): Promise<HealthResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
    }, 10000); // 10s timeout for health check

    if (!response.ok) {
        throw new ApiError('Health check failed', response.status);
    }

    return response.json();
}

export async function sendChatMessage(
    request: ChatRequest,
    authToken?: string
): Promise<ChatResponse> {
    const headers: HeadersInit = {
        'Content-Type': 'application/json',
    };

    if (authToken) {
        headers['Authorization'] = authToken;
    }

    const response = await fetchWithTimeout(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        let errorMessage = 'Failed to get response from AI';

        try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
        } catch {
            // Use default message
        }

        if (response.status === 429) {
            throw new ApiError('Too many requests. Please wait a moment.', 429, 'RATE_LIMITED');
        }
        if (response.status === 408 || response.status === 504) {
            throw new ApiError('Request timed out. Please try again.', response.status, 'TIMEOUT');
        }

        throw new ApiError(errorMessage, response.status);
    }

    const data = await response.json();

    // Validate JSON integrity before returning
    if (!data || typeof data.answer !== 'string') {
        throw new ApiError('Invalid response format from server', 500, 'INVALID_RESPONSE');
    }

    return data;
}

/**
 * Send a chat message with Server-Sent Event streaming.
 * Tokens are delivered incrementally via the onToken callback.
 */
export async function sendChatMessageStream(
    request: ChatRequest,
    callbacks: {
        onToken: (text: string) => void;
        onMetadata?: (topic: string | null, detectedLanguage: string) => void;
        onStepImages?: (images: unknown[]) => void;
        onDone?: () => void;
        onError?: (message: string) => void;
    },
    authToken?: string
): Promise<void> {
    const headers: HeadersInit = {
        'Content-Type': 'application/json',
    };
    if (authToken) {
        headers['Authorization'] = authToken;
    }

    const response = await fetchWithTimeout(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const errorMessage = 'Failed to start streaming response';
        callbacks.onError?.(errorMessage);
        throw new ApiError(errorMessage, response.status);
    }

    const reader = response.body?.getReader();
    if (!reader) {
        throw new ApiError('No readable stream', 500);
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Parse SSE lines
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            let currentEvent = '';
            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    currentEvent = line.slice(7).trim();
                } else if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    try {
                        const parsed = JSON.parse(data);
                        switch (currentEvent) {
                            case 'token':
                                callbacks.onToken(parsed.text || '');
                                break;
                            case 'metadata':
                                callbacks.onMetadata?.(parsed.topic, parsed.detected_language);
                                break;
                            case 'step_images':
                                callbacks.onStepImages?.(parsed);
                                break;
                            case 'done':
                                callbacks.onDone?.();
                                break;
                            case 'error':
                                callbacks.onError?.(parsed.message || 'Unknown error');
                                break;
                        }
                    } catch {
                        // Skip unparseable lines
                    }
                    currentEvent = '';
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}

export { ApiError };
// Profile Types
export interface Condition {
    name: string;
    diagnosed_date?: string;
    notes?: string;
}

export interface Medication {
    name: string;
    dosage: string;
    frequency?: string;
}

export interface KeyFact {
    fact: string;
    source: string;
    date?: string;
}

export interface HealthProfile {
    user_id: string;
    conditions: Condition[];
    medications: Medication[];
    allergies: string[];
    blood_type: string;
    age?: number;
    gender: string;
    key_facts: KeyFact[];
}

export interface ProfileUpdateRequest {
    conditions?: string[];
    medications?: { name: string; dosage: string }[];
    allergies?: string[];
    age?: number;
    gender?: string;
    blood_type?: string;
}

// History Types
export interface ChatHistoryItem {
    chat_id: string;
    query: string;
    topic: string;
    timestamp: number;
    created_at: string;
    has_images: boolean;
}

export interface ChatHistoryResponse {
    items: ChatHistoryItem[];
    count: number;
}

// Profile API
export async function getHealthProfile(token: string): Promise<HealthProfile> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/profile`, {
        method: 'GET',
        headers: {
            'Authorization': token,
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        throw new Error('Failed to fetch profile');
    }

    return response.json();
}

export async function updateHealthProfile(token: string, data: ProfileUpdateRequest): Promise<HealthProfile> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/profile`, {
        method: 'PUT',
        headers: {
            'Authorization': token,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        throw new Error('Failed to update profile');
    }

    return response.json();
}

// History API
export async function getChatHistory(token: string): Promise<ChatHistoryResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/history`, {
        method: 'GET',
        headers: {
            'Authorization': token,
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        throw new Error('Failed to fetch history');
    }

    return response.json();
}

// Upload API
export interface PresignedUrlResponse {
    upload_url: string;
    s3_key: string;
}

export async function getPresignedUrl(token: string, filename: string, contentType: string): Promise<PresignedUrlResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/upload/presigned-url`, {
        method: 'POST',
        headers: {
            'Authorization': token,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename, content_type: contentType }),
    });

    if (!response.ok) {
        throw new Error('Failed to get upload URL');
    }

    return response.json();
}

export async function uploadFileToS3(uploadUrl: string, file: File): Promise<void> {
    const response = await fetch(uploadUrl, {
        method: 'PUT',
        headers: {
            'Content-Type': file.type
        },
        body: file
    });

    if (!response.ok) {
        throw new Error('Failed to upload file to S3');
    }
}

import type { ChatDetailResponse } from '../types/api';

export async function getChat(token: string, chatId: string): Promise<ChatDetailResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/history/${chatId}`, {
        method: 'GET',
        headers: {
            'Authorization': token,
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        throw new Error('Failed to fetch chat details');
    }

    return response.json();
}
