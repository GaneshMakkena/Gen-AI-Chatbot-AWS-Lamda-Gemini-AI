"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Mic, MicOff, Globe, Stethoscope, Heart, Loader2, Image as ImageIcon, ChevronLeft, ChevronRight, PlusCircle, User, LogIn, LogOut, Volume2, History, Paperclip } from "lucide-react";
import Link from "next/link";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { useAuth } from "@/contexts/AuthContext";
import { useSpeechRecognition, speakText } from "@/hooks/useSpeechRecognition";
import HistorySidebar from "@/components/HistorySidebar";
import FileAttachments, { AttachedFile, validateFiles, createAttachedFile } from "@/components/FileAttachments";

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types
interface StepImage {
  step_number: string;
  title: string;
  description: string;
  image_prompt?: string;
  image?: string;  // Base64 (fallback)
  image_url?: string;  // S3 URL (preferred)
}

interface MessageAttachment {
  filename: string;
  type: "pdf" | "image";
  url?: string;  // S3 URL for download
  preview?: string;  // Base64 preview for images
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  stepImages?: StepImage[];
  stepsCount?: number;
  topic?: string;
  timestamp: Date;
  attachments?: MessageAttachment[];  // File attachments
}

interface Language {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
}

const LANGUAGES: Language[] = [
  { code: "en", name: "English", nativeName: "English", flag: "🇺🇸" },
  { code: "te", name: "Telugu", nativeName: "తెలుగు", flag: "🇮🇳" },
  { code: "hi", name: "Hindi", nativeName: "हिन्दी", flag: "🇮🇳" },
];

// Step Images Gallery Component
function StepImagesGallery({ steps }: { steps: StepImage[] }) {
  const [currentStep, setCurrentStep] = useState(0);

  // Filter steps that have either image_url or base64 image
  const validSteps = steps.filter(s => s.image_url || s.image);

  if (validSteps.length === 0) return null;

  // Helper to get image source - prefer S3 URL over base64
  const getImageSrc = (step: StepImage): string => {
    if (step.image_url) return step.image_url;
    if (step.image) return `data:image/png;base64,${step.image}`;
    return '';
  };

  const goNext = () => setCurrentStep((prev) => (prev + 1) % validSteps.length);
  const goPrev = () => setCurrentStep((prev) => (prev - 1 + validSteps.length) % validSteps.length);

  return (
    <div className="mt-4 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-slate-800 dark:to-slate-700 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <ImageIcon className="w-5 h-5 text-primary" />
          <span className="font-semibold text-gray-800 dark:text-white">
            Visual Step-by-Step Guide
          </span>
        </div>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          Step {currentStep + 1} of {validSteps.length}
        </span>
      </div>

      {/* Current Step Image */}
      <div className="relative">
        <img
          src={getImageSrc(validSteps[currentStep])}
          alt={`Step ${validSteps[currentStep].step_number}: ${validSteps[currentStep].title}`}
          className="w-full rounded-lg shadow-lg"
          style={{ maxHeight: '400px', objectFit: 'contain' }}
        />

        {/* Navigation Arrows */}
        {validSteps.length > 1 && (
          <>
            <button
              onClick={goPrev}
              className="absolute left-2 top-1/2 -translate-y-1/2 p-2 bg-white/90 dark:bg-slate-800/90 rounded-full shadow-lg hover:bg-white dark:hover:bg-slate-700 transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={goNext}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-white/90 dark:bg-slate-800/90 rounded-full shadow-lg hover:bg-white dark:hover:bg-slate-700 transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </>
        )}
      </div>

      {/* Step Title and Description */}
      <div className="mt-3 p-3 bg-white dark:bg-slate-900 rounded-lg">
        <h4 className="font-bold text-primary">
          Step {validSteps[currentStep].step_number}: {validSteps[currentStep].title}
        </h4>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          {validSteps[currentStep].description}
        </p>
      </div>

      {/* Step Indicators */}
      {validSteps.length > 1 && (
        <div className="flex justify-center gap-2 mt-3">
          {validSteps.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentStep(idx)}
              className={`w-3 h-3 rounded-full transition-all ${idx === currentStep
                ? "bg-primary scale-110"
                : "bg-gray-300 dark:bg-slate-600 hover:bg-gray-400"
                }`}
            />
          ))}
        </div>
      )}

      {/* Thumbnail Strip */}
      {validSteps.length > 2 && (
        <div className="flex gap-2 mt-3 overflow-x-auto pb-2">
          {validSteps.map((step, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentStep(idx)}
              className={`flex-shrink-0 rounded-lg overflow-hidden border-2 transition-all ${idx === currentStep
                ? "border-primary ring-2 ring-primary/30"
                : "border-transparent opacity-70 hover:opacity-100"
                }`}
            >
              <img
                src={`data:image/png;base64,${step.image}`}
                alt={`Step ${step.step_number}`}
                className="w-16 h-16 object-cover"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Guest users are limited to this many messages
const GUEST_MESSAGE_LIMIT = 4;

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<Language>(LANGUAGES[0]);
  const [showLanguageMenu, setShowLanguageMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showHistorySidebar, setShowHistorySidebar] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginModalMessage, setLoginModalMessage] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [fileError, setFileError] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auth context
  const { user, isAuthenticated, logout, getToken } = useAuth();

  // Voice recognition with microphone permission
  const {
    isListening,
    isSupported: voiceSupported,
    hasPermission: micPermission,
    transcript,
    startListening,
    stopListening,
    requestPermission
  } = useSpeechRecognition({
    language: selectedLanguage.code === "te" ? "te-IN" :
      selectedLanguage.code === "hi" ? "hi-IN" : "en-US",
    onResult: (text) => {
      setInput(text);
    },
    onError: (error) => {
      console.error("Voice error:", error);
    }
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Build conversation history for context
  const getConversationHistory = () => {
    return messages.slice(-6).map(msg => ({
      role: msg.role,
      content: msg.content
    }));
  };

  // Handle sending a message
  const handleSend = async () => {
    if ((!input.trim() && attachedFiles.length === 0) || isLoading) return;

    // Check guest message limit
    const userMessageCount = messages.filter(m => m.role === "user").length;
    if (!isAuthenticated && userMessageCount >= GUEST_MESSAGE_LIMIT) {
      setLoginModalMessage(`You've reached the ${GUEST_MESSAGE_LIMIT} message limit for guest users. Create a free account to continue chatting with unlimited messages!`);
      setShowLoginModal(true);
      return;
    }

    // Build message attachments from attached files
    const messageAttachments: MessageAttachment[] = attachedFiles.map(f => ({
      filename: f.file.name,
      type: f.type,
      preview: f.preview,  // Keep preview for images
    }));

    // User content - just the text, don't prepend file info
    const userContent = input.trim() || (attachedFiles.length > 0 ? "Please analyze these files." : "");

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userContent,
      timestamp: new Date(),
      attachments: messageAttachments.length > 0 ? messageAttachments : undefined,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Get auth token if logged in
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      // Convert files to base64 for API
      const attachments = await Promise.all(
        attachedFiles.map(async (af) => {
          const arrayBuffer = await af.file.arrayBuffer();
          const base64 = btoa(
            new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), "")
          );
          return {
            filename: af.file.name,
            content_type: af.file.type,
            data: base64,
            type: af.type,
          };
        })
      );

      // Clear attached files before sending (so UI updates)
      const currentFiles = [...attachedFiles];
      setAttachedFiles([]);
      currentFiles.forEach(f => {
        if (f.preview) URL.revokeObjectURL(f.preview);
      });

      const response = await axios.post(
        `${API_BASE_URL}/chat`,
        {
          query: input.trim() || "Please analyze the attached files.",
          language: selectedLanguage.name,
          generate_images: attachments.length === 0, // Don't generate images if files attached
          conversation_history: getConversationHistory(),
          attachments: attachments.length > 0 ? attachments : undefined,
        },
        { headers }
      );

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.data.answer,
        stepImages: response.data.step_images,
        stepsCount: response.data.steps_count,
        topic: response.data.topic,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I apologize, but I encountered an error processing your request. Please try again, and if the issue persists, try refreshing the page.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Toggle voice recording using Web Speech API
  const toggleRecording = async () => {
    if (isListening) {
      stopListening();
    } else {
      await startListening();
    }
  };

  // Handle New Chat
  const handleNewChat = () => {
    setMessages([]);
    setInput("");
  };

  // Handle selecting a chat from history
  const handleSelectChat = async (chatId: string) => {
    try {
      const token = await getToken();
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/history/${chatId}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (response.ok) {
        const chat = await response.json();
        // Load the chat into messages
        setMessages([
          {
            id: "1",
            role: "user",
            content: chat.query,
            timestamp: new Date(chat.timestamp),
          },
          {
            id: "2",
            role: "assistant",
            content: chat.response,
            topic: chat.topic,
            timestamp: new Date(chat.timestamp),
          }
        ]);
        setShowHistorySidebar(false);
      }
    } catch (err) {
      console.error("Failed to load chat:", err);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* History Sidebar */}
      <HistorySidebar
        isOpen={showHistorySidebar}
        onClose={() => setShowHistorySidebar(false)}
        onSelectChat={handleSelectChat}
      />

      {/* Header */}
      <header className="gradient-hero text-white shadow-lg sticky top-0 z-50">
        <div className="container-responsive py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Title */}
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                <Stethoscope className="w-7 h-7" />
              </div>
              <div>
                <h1 className="text-xl md:text-2xl font-bold">MediBot</h1>
                <p className="text-xs md:text-sm text-white/80">AI Medical Assistant</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {/* History Button - Show for all users, prompt login for guests */}
              <button
                onClick={() => {
                  if (isAuthenticated) {
                    setShowHistorySidebar(true);
                  } else {
                    setLoginModalMessage("Sign in to view your chat history and get personalized medical advice.");
                    setShowLoginModal(true);
                  }
                }}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
                title="Chat History"
              >
                <History className="w-5 h-5" />
                <span className="hidden sm:inline">History</span>
              </button>

              {/* New Chat Button */}
              {messages.length > 0 && (
                <button
                  onClick={handleNewChat}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition-colors animate-fade-in"
                  title="Start New Chat"
                >
                  <PlusCircle className="w-5 h-5" />
                  <span className="hidden sm:inline">New Chat</span>
                </button>
              )}

              {/* Language Selector */}
              <div className="relative">
                <button
                  onClick={() => setShowLanguageMenu(!showLanguageMenu)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
                >
                  <Globe className="w-5 h-5" />
                  <span className="hidden sm:inline">{selectedLanguage.flag} {selectedLanguage.nativeName}</span>
                  <span className="sm:hidden">{selectedLanguage.flag}</span>
                </button>

                {showLanguageMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-xl overflow-hidden animate-fade-in z-50">
                    {LANGUAGES.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => {
                          setSelectedLanguage(lang);
                          setShowLanguageMenu(false);
                        }}
                        className={`w-full px-4 py-3 text-left flex items-center gap-3 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors ${selectedLanguage.code === lang.code ? "bg-blue-50 dark:bg-slate-700" : ""
                          }`}
                      >
                        <span className="text-xl">{lang.flag}</span>
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">{lang.name}</div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">{lang.nativeName}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* User Auth Button */}
              {isAuthenticated ? (
                <div className="relative">
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
                  >
                    <div className="w-8 h-8 rounded-full bg-cyan-500 flex items-center justify-center text-white font-semibold">
                      {user?.name?.charAt(0).toUpperCase() || "U"}
                    </div>
                    <span className="hidden sm:inline">{user?.name}</span>
                  </button>

                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-xl overflow-hidden animate-fade-in z-50">
                      <div className="px-4 py-3 border-b border-gray-200 dark:border-slate-700">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">{user?.name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{user?.email}</p>
                      </div>
                      <Link
                        href="/profile"
                        onClick={() => setShowUserMenu(false)}
                        className="w-full px-4 py-3 text-left flex items-center gap-3 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors text-gray-700 dark:text-gray-300"
                      >
                        <Heart className="w-4 h-4" />
                        Health Profile
                      </Link>
                      <button
                        onClick={() => {
                          logout();
                          setShowUserMenu(false);
                        }}
                        className="w-full px-4 py-3 text-left flex items-center gap-3 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors text-red-600 dark:text-red-400"
                      >
                        <LogOut className="w-4 h-4" />
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <Link
                  href="/login"
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
                >
                  <LogIn className="w-5 h-5" />
                  <span className="hidden sm:inline">Sign In</span>
                </Link>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col container-responsive py-4">
        {/* Empty State */}
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center px-4 animate-fade-in">
            <div className="w-24 h-24 rounded-full gradient-primary flex items-center justify-center mb-6 shadow-lg">
              <Heart className="w-12 h-12 text-white animate-bounce-subtle" />
            </div>
            <h2 className="text-2xl md:text-3xl font-bold text-gray-800 dark:text-white mb-3">
              Welcome to MediBot
            </h2>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mb-8">
              Your AI-powered medical assistant with <strong>step-by-step visual instructions</strong>.
              Ask me about symptoms, first aid procedures, or any health questions.
            </p>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
              {[
                "How do I perform CPR?",
                "What are signs of dehydration?",
                "How to treat minor burns?",
                "First aid for choking",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-left hover:border-primary hover:shadow-md transition-all text-sm"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.length > 0 && (
          <div className="flex-1 overflow-y-auto space-y-4 pb-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}
              >
                <div
                  className={`max-w-[90%] md:max-w-[80%] px-4 py-3 ${message.role === "user" ? "message-user" : "message-assistant"
                    }`}
                >
                  {/* File attachments in message */}
                  {message.attachments && message.attachments.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-2">
                      {message.attachments.map((att, idx) => (
                        <div
                          key={idx}
                          className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs ${att.type === "pdf"
                            ? "bg-red-100/50 text-red-700 dark:bg-red-900/30 dark:text-red-300"
                            : "bg-blue-100/50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                            }`}
                        >
                          {att.type === "pdf" ? (
                            <span>📄</span>
                          ) : att.preview ? (
                            <img src={att.preview} alt="" className="w-5 h-5 rounded object-cover" />
                          ) : (
                            <span>🖼️</span>
                          )}
                          <span className="max-w-[100px] truncate">{att.filename}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {message.role === "assistant" ? (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p>{message.content}</p>
                  )}

                  {/* Step-by-Step Images Gallery */}
                  {message.stepImages && message.stepImages.length > 0 && (
                    <StepImagesGallery steps={message.stepImages} />
                  )}
                </div>
              </div>
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex justify-start animate-fade-in">
                <div className="message-assistant px-6 py-4">
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                    <span className="text-gray-600 dark:text-gray-400">
                      Researching and generating visual guide...
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Input Area */}
      <div className="sticky bottom-0 bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-700 shadow-lg">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.webp"
          multiple
          className="hidden"
          onChange={(e) => {
            const files = Array.from(e.target.files || []);
            if (files.length === 0) return;

            const result = validateFiles(attachedFiles, files);
            if (!result.valid) {
              setFileError(result.error || "Invalid files");
              setTimeout(() => setFileError(""), 3000);
            }
            if (result.acceptedFiles.length > 0) {
              setAttachedFiles(prev => [...prev, ...result.acceptedFiles]);
            }
            e.target.value = ""; // Reset input
          }}
        />

        {/* Attached files display */}
        <FileAttachments
          files={attachedFiles}
          onRemove={(id) => {
            const file = attachedFiles.find(f => f.id === id);
            if (file?.preview) URL.revokeObjectURL(file.preview);
            setAttachedFiles(prev => prev.filter(f => f.id !== id));
          }}
        />

        {/* File error message */}
        {fileError && (
          <div className="px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm text-center">
            {fileError}
          </div>
        )}

        <div className="container-responsive py-4">
          <div className="flex items-center gap-2 md:gap-3">
            {/* Attach Files Button (+) */}
            <button
              onClick={() => {
                if (isAuthenticated) {
                  fileInputRef.current?.click();
                } else {
                  setLoginModalMessage("Sign in to attach files and get AI-powered analysis.");
                  setShowLoginModal(true);
                }
              }}
              className="p-3 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:from-emerald-600 hover:to-teal-600 transition-all shadow-md"
              title="Attach files (PDFs, images)"
            >
              <PlusCircle className="w-5 h-5" />
            </button>

            {/* Voice Input Button */}
            <div className="relative">
              {/* Warning tooltip on hover for unsupported browsers */}
              {!voiceSupported && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-amber-500 text-white text-xs rounded-lg whitespace-nowrap shadow-lg pointer-events-none opacity-0 hover:opacity-100 transition-opacity">
                  ⚠️ Voice not supported. Use Chrome/Edge.
                </div>
              )}
              <button
                onClick={toggleRecording}
                disabled={!voiceSupported}
                className={`p-3 rounded-full transition-all ${isListening
                  ? "bg-red-500 text-white animate-pulse"
                  : voiceSupported
                    ? "bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-700"
                    : "bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 cursor-not-allowed"
                  }`}
                title={!voiceSupported ? "Voice input not supported. Use Chrome/Edge." : isListening ? "Stop recording" : "Start voice input"}
              >
                {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>
            </div>

            {/* Text Input */}
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={attachedFiles.length > 0 ? "Ask about these files..." : `Ask a medical question in ${selectedLanguage.name}...`}
                className="w-full px-4 py-3 rounded-xl bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                disabled={isLoading}
              />
            </div>

            {/* Send Button */}
            <button
              onClick={handleSend}
              disabled={(!input.trim() && attachedFiles.length === 0) || isLoading}
              className="p-3 rounded-full gradient-primary text-white disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transition-all"
              title="Send message"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>

          {/* Disclaimer */}
          <p className="text-xs text-center text-gray-500 dark:text-gray-500 mt-2">
            ⚕️ This AI provides educational health information with visual guides. Always consult a healthcare professional for medical advice.
          </p>
        </div>
      </div>

      {/* Login Modal for Guest Users */}
      {
        showLoginModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-fade-in">
              <div className="text-center mb-6">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center mx-auto mb-4">
                  <User className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  Sign In Required
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  {loginModalMessage}
                </p>
              </div>

              <div className="flex flex-col gap-3">
                <Link
                  href="/login"
                  className="w-full py-3 px-4 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white rounded-xl font-medium text-center transition-all"
                >
                  Sign In
                </Link>
                <Link
                  href="/signup"
                  className="w-full py-3 px-4 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 rounded-xl font-medium text-center transition-colors"
                >
                  Create Free Account
                </Link>
                <button
                  onClick={() => setShowLoginModal(false)}
                  className="w-full py-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-sm transition-colors"
                >
                  Maybe Later
                </button>
              </div>

              <p className="text-xs text-center text-gray-400 mt-4">
                ✨ Free accounts get unlimited messages, chat history, and personalized health memory
              </p>
            </div>
          </div>
        )}
    </div>
  );
}
