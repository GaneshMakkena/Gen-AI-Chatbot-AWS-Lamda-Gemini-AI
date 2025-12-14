"use client";

import { useState, useEffect, useCallback, useRef } from "react";

interface UseSpeechRecognitionOptions {
    onResult?: (transcript: string) => void;
    onError?: (error: string) => void;
    continuous?: boolean;
    language?: string;
}

interface UseSpeechRecognitionReturn {
    isListening: boolean;
    isSupported: boolean;
    hasPermission: boolean | null;
    transcript: string;
    startListening: () => Promise<void>;
    stopListening: () => void;
    requestPermission: () => Promise<boolean>;
}

// Declare SpeechRecognition types
interface SpeechRecognitionEvent {
    resultIndex: number;
    results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent {
    error: string;
    message: string;
}

export function useSpeechRecognition(
    options: UseSpeechRecognitionOptions = {}
): UseSpeechRecognitionReturn {
    const { onResult, onError, continuous = false, language = "en-US" } = options;

    const [isListening, setIsListening] = useState(false);
    const [isSupported, setIsSupported] = useState(false);
    const [hasPermission, setHasPermission] = useState<boolean | null>(null);
    const [transcript, setTranscript] = useState("");

    const recognitionRef = useRef<any>(null);

    // Check browser support on mount
    useEffect(() => {
        const SpeechRecognition =
            (window as any).SpeechRecognition ||
            (window as any).webkitSpeechRecognition;

        setIsSupported(!!SpeechRecognition);

        if (SpeechRecognition) {
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = continuous;
            recognitionRef.current.interimResults = true;
            recognitionRef.current.lang = language;

            recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
                let finalTranscript = "";
                let interimTranscript = "";

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const result = event.results[i];
                    if (result.isFinal) {
                        finalTranscript += result[0].transcript;
                    } else {
                        interimTranscript += result[0].transcript;
                    }
                }

                const currentTranscript = finalTranscript || interimTranscript;
                setTranscript(currentTranscript);

                if (finalTranscript && onResult) {
                    onResult(finalTranscript);
                }
            };

            recognitionRef.current.onerror = (event: SpeechRecognitionErrorEvent) => {
                console.error("Speech recognition error:", event.error);
                setIsListening(false);

                if (event.error === "not-allowed") {
                    setHasPermission(false);
                }

                if (onError) {
                    onError(event.error);
                }
            };

            recognitionRef.current.onend = () => {
                setIsListening(false);
            };
        }

        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
        };
    }, [continuous, language, onResult, onError]);

    // Request microphone permission
    const requestPermission = useCallback(async (): Promise<boolean> => {
        try {
            // Request microphone access - this triggers the browser permission dialog
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Stop the stream immediately - we just needed to request permission
            stream.getTracks().forEach(track => track.stop());

            setHasPermission(true);
            return true;
        } catch (error) {
            console.error("Microphone permission denied:", error);
            setHasPermission(false);
            return false;
        }
    }, []);

    // Start listening
    const startListening = useCallback(async () => {
        if (!isSupported) {
            if (onError) {
                onError("Speech recognition not supported in this browser");
            }
            return;
        }

        // Request permission if not already granted
        if (hasPermission === null || hasPermission === false) {
            const granted = await requestPermission();
            if (!granted) {
                if (onError) {
                    onError("Microphone permission denied. Please allow microphone access.");
                }
                return;
            }
        }

        try {
            setTranscript("");
            recognitionRef.current?.start();
            setIsListening(true);
        } catch (error) {
            console.error("Failed to start speech recognition:", error);
            setIsListening(false);
        }
    }, [isSupported, hasPermission, requestPermission, onError]);

    // Stop listening
    const stopListening = useCallback(() => {
        if (recognitionRef.current) {
            recognitionRef.current.stop();
        }
        setIsListening(false);
    }, []);

    return {
        isListening,
        isSupported,
        hasPermission,
        transcript,
        startListening,
        stopListening,
        requestPermission,
    };
}

// Text-to-Speech utility
export function speakText(text: string, lang: string = "en-US"): Promise<void> {
    return new Promise((resolve, reject) => {
        if (!("speechSynthesis" in window)) {
            reject(new Error("Text-to-speech not supported"));
            return;
        }

        // Cancel any ongoing speech
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        utterance.onend = () => resolve();
        utterance.onerror = (event) => reject(new Error(event.error));

        window.speechSynthesis.speak(utterance);
    });
}
