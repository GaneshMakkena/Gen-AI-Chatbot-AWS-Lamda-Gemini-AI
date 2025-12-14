"use client";

import { useState, useEffect } from "react";
import { History, X, Trash2, MessageSquare, ChevronRight, Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

interface ChatHistoryItem {
    chat_id: string;
    query: string;
    topic: string;
    timestamp: number;
    created_at: string;
    has_images: boolean;
}

interface HistorySidebarProps {
    onSelectChat: (chatId: string) => void;
    isOpen: boolean;
    onClose: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://khucwqfzv4.execute-api.us-east-1.amazonaws.com/production";

export default function HistorySidebar({ onSelectChat, isOpen, onClose }: HistorySidebarProps) {
    const [chats, setChats] = useState<ChatHistoryItem[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    const { isAuthenticated, getToken } = useAuth();

    // Fetch history when sidebar opens
    useEffect(() => {
        if (isOpen && isAuthenticated) {
            fetchHistory();
        }
    }, [isOpen, isAuthenticated]);

    async function fetchHistory() {
        setIsLoading(true);
        setError("");

        try {
            const token = await getToken();
            if (!token) {
                setError("Please log in to view history");
                return;
            }

            const response = await fetch(`${API_URL}/history?limit=20`, {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error("Failed to fetch history");
            }

            const data = await response.json();
            setChats(data.items || []);
        } catch (err: any) {
            setError(err.message || "Failed to load history");
        } finally {
            setIsLoading(false);
        }
    }

    async function handleDelete(chatId: string, e: React.MouseEvent) {
        e.stopPropagation();

        try {
            const token = await getToken();
            if (!token) return;

            await fetch(`${API_URL}/history/${chatId}`, {
                method: "DELETE",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });

            // Remove from local state
            setChats(prev => prev.filter(chat => chat.chat_id !== chatId));
        } catch (err) {
            console.error("Failed to delete chat:", err);
        }
    }

    function formatDate(timestamp: number) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) return "Today";
        if (days === 1) return "Yesterday";
        if (days < 7) return `${days} days ago`;
        return date.toLocaleDateString();
    }

    if (!isOpen) return null;

    return (
        <>
            {/* Overlay */}
            <div
                className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                onClick={onClose}
            />

            {/* Sidebar */}
            <div className={`fixed top-0 left-0 h-full w-80 bg-white dark:bg-slate-900 shadow-2xl z-50 transform transition-transform duration-300 ${isOpen ? "translate-x-0" : "-translate-x-full"}`}>
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-slate-700">
                    <div className="flex items-center gap-2">
                        <History className="w-5 h-5 text-cyan-500" />
                        <h2 className="font-semibold text-gray-900 dark:text-white">Chat History</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto h-[calc(100%-64px)]">
                    {!isAuthenticated ? (
                        <div className="p-6 text-center">
                            <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                            <p className="text-gray-500 dark:text-gray-400">
                                Sign in to view your chat history
                            </p>
                        </div>
                    ) : isLoading ? (
                        <div className="flex items-center justify-center p-8">
                            <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
                        </div>
                    ) : error ? (
                        <div className="p-6 text-center">
                            <p className="text-red-500">{error}</p>
                            <button
                                onClick={fetchHistory}
                                className="mt-2 text-cyan-500 hover:underline"
                            >
                                Try again
                            </button>
                        </div>
                    ) : chats.length === 0 ? (
                        <div className="p-6 text-center">
                            <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                            <p className="text-gray-500 dark:text-gray-400">
                                No chat history yet
                            </p>
                            <p className="text-sm text-gray-400 mt-1">
                                Your conversations will appear here
                            </p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-100 dark:divide-slate-800">
                            {chats.map((chat) => (
                                <div
                                    key={chat.chat_id}
                                    onClick={() => onSelectChat(chat.chat_id)}
                                    className="p-4 hover:bg-gray-50 dark:hover:bg-slate-800 cursor-pointer transition-colors group"
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                                {chat.query}
                                            </p>
                                            <div className="flex items-center gap-2 mt-1">
                                                {chat.topic && (
                                                    <span className="text-xs px-2 py-0.5 bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 rounded-full">
                                                        {chat.topic}
                                                    </span>
                                                )}
                                                {chat.has_images && (
                                                    <span className="text-xs text-gray-400">📷</span>
                                                )}
                                            </div>
                                            <p className="text-xs text-gray-400 mt-1">
                                                {formatDate(chat.timestamp)}
                                            </p>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <button
                                                onClick={(e) => handleDelete(chat.chat_id, e)}
                                                className="p-1.5 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                                                title="Delete chat"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                            <ChevronRight className="w-4 h-4 text-gray-300" />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
