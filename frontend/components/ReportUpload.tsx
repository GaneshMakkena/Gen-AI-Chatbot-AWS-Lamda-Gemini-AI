"use client";

import { useState, useRef, useEffect } from "react";
import { Upload, FileText, X, Loader2, AlertCircle, CheckCircle, Heart, Pill, AlertTriangle, Info } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

interface ReportUploadProps {
    onAnalysisComplete: (analysis: string) => void;
    isOpen: boolean;
    onClose: () => void;
}

interface ExtractedInfo {
    conditions: string[];
    medications: Array<{ name: string; dosage: string }>;
    allergies: string[];
    age: number | null;
    gender: string | null;
    blood_type: string | null;
    key_facts: string[];
    summary: string;
    report_type: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://khucwqfzv4.execute-api.us-east-1.amazonaws.com/production";

const ALLOWED_TYPES = ["application/pdf", "image/jpeg", "image/png", "image/jpg"];
const MAX_SIZE = 10 * 1024 * 1024; // 10MB

export default function ReportUpload({ onAnalysisComplete, isOpen, onClose }: ReportUploadProps) {
    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState("");
    const [uploadProgress, setUploadProgress] = useState(0);
    const [step, setStep] = useState<"upload" | "review" | "saved">("upload");
    const [extractedInfo, setExtractedInfo] = useState<ExtractedInfo | null>(null);
    const [fileKey, setFileKey] = useState("");

    const fileInputRef = useRef<HTMLInputElement>(null);
    const { isAuthenticated, getToken } = useAuth();

    // Reset state when modal closes
    useEffect(() => {
        if (!isOpen) {
            setFile(null);
            setError("");
            setUploadProgress(0);
            setIsUploading(false);
            setIsAnalyzing(false);
            setIsSaving(false);
            setStep("upload");
            setExtractedInfo(null);
            setFileKey("");
        }
    }, [isOpen]);

    function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
        const selectedFile = e.target.files?.[0];
        if (!selectedFile) return;

        // Validate file type
        if (!ALLOWED_TYPES.includes(selectedFile.type)) {
            setError("Please select a PDF or image file (JPG, PNG)");
            return;
        }

        // Validate file size
        if (selectedFile.size > MAX_SIZE) {
            setError("File size must be less than 10MB");
            return;
        }

        setFile(selectedFile);
        setError("");
    }

    async function handleUploadAndAnalyze() {
        if (!file || !isAuthenticated) return;

        setIsUploading(true);
        setError("");
        setUploadProgress(0);

        try {
            const token = await getToken();
            if (!token) {
                setError("Please log in to upload reports");
                return;
            }

            // Step 1: Get presigned URL
            const urlResponse = await fetch(`${API_URL}/upload-report`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    filename: file.name,
                    content_type: file.type
                })
            });

            if (!urlResponse.ok) {
                throw new Error("Failed to get upload URL");
            }

            const { upload_url, file_key } = await urlResponse.json();
            setFileKey(file_key);
            setUploadProgress(25);

            // Step 2: Upload file to S3
            const uploadResponse = await fetch(upload_url, {
                method: "PUT",
                headers: {
                    "Content-Type": file.type
                },
                body: file
            });

            if (!uploadResponse.ok) {
                throw new Error("Failed to upload file");
            }

            setUploadProgress(50);
            setIsUploading(false);
            setIsAnalyzing(true);

            // Step 3: Call /analyze-report to use Gemini multimodal
            const analyzeResponse = await fetch(`${API_URL}/analyze-report`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ file_key })
            });

            setUploadProgress(75);

            if (!analyzeResponse.ok) {
                const errorData = await analyzeResponse.json();
                throw new Error(errorData.detail || "Analysis failed");
            }

            const result = await analyzeResponse.json();

            if (!result.success) {
                throw new Error(result.error || "Analysis failed");
            }

            setUploadProgress(100);
            setExtractedInfo(result.extracted);
            setStep("review");
            setIsAnalyzing(false);

        } catch (err: any) {
            setError(err.message || "Upload failed");
            setIsUploading(false);
            setIsAnalyzing(false);
        }
    }

    async function handleConfirmAndSave() {
        if (!extractedInfo || !fileKey) return;

        setIsSaving(true);
        setError("");

        try {
            const token = await getToken();
            if (!token) {
                setError("Please log in");
                return;
            }

            // Call /confirm-analysis to save to health profile
            const response = await fetch(`${API_URL}/confirm-analysis`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    file_key: fileKey,
                    extracted: extractedInfo
                })
            });

            if (!response.ok) {
                throw new Error("Failed to save to profile");
            }

            setStep("saved");

            // Create a summary message for the chat
            const summaryMessage = `📋 **Report Analyzed: ${file?.name}**\n\n${extractedInfo.summary}\n\n${extractedInfo.conditions.length > 0
                    ? `**Conditions noted:** ${extractedInfo.conditions.join(", ")}\n`
                    : ""
                }${extractedInfo.medications.length > 0
                    ? `**Medications noted:** ${extractedInfo.medications.map(m => m.name).join(", ")}\n`
                    : ""
                }\n✅ This information has been saved to your health profile for personalized advice.`;

            onAnalysisComplete(summaryMessage);

            // Close modal after brief delay
            setTimeout(() => {
                onClose();
            }, 2000);

        } catch (err: any) {
            setError(err.message || "Save failed");
        } finally {
            setIsSaving(false);
        }
    }

    function handleDrop(e: React.DragEvent) {
        e.preventDefault();
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile) {
            setFile(droppedFile);
            setError("");
        }
    }

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-fade-in max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                        {step === "upload" && "Upload Medical Report"}
                        {step === "review" && "Review Extracted Info"}
                        {step === "saved" && "Saved to Profile!"}
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                {/* Error */}
                {error && (
                    <div className="flex items-center gap-2 p-3 mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400">
                        <AlertCircle className="w-5 h-5 flex-shrink-0" />
                        <span className="text-sm">{error}</span>
                    </div>
                )}

                {/* Step 1: Upload */}
                {step === "upload" && (
                    <>
                        {/* Drop Zone */}
                        <div
                            onDrop={handleDrop}
                            onDragOver={(e) => e.preventDefault()}
                            onClick={() => fileInputRef.current?.click()}
                            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${file
                                    ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20"
                                    : "border-gray-300 dark:border-slate-600 hover:border-cyan-400 dark:hover:border-cyan-500"
                                }`}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".pdf,.jpg,.jpeg,.png"
                                onChange={handleFileSelect}
                                className="hidden"
                            />

                            {file ? (
                                <div className="flex flex-col items-center gap-2">
                                    <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                                        <FileText className="w-6 h-6 text-emerald-600" />
                                    </div>
                                    <p className="font-medium text-gray-900 dark:text-white">{file.name}</p>
                                    <p className="text-sm text-gray-500">
                                        {(file.size / 1024 / 1024).toFixed(2)} MB
                                    </p>
                                </div>
                            ) : (
                                <>
                                    <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                                    <p className="text-gray-600 dark:text-gray-300 mb-1">
                                        Drop your report here or click to browse
                                    </p>
                                    <p className="text-sm text-gray-400">
                                        PDF, JPG, PNG up to 10MB
                                    </p>
                                </>
                            )}
                        </div>

                        {/* Progress */}
                        {(isUploading || isAnalyzing) && (
                            <div className="mt-4">
                                <div className="flex items-center justify-between text-sm mb-2">
                                    <span className="text-gray-600 dark:text-gray-400">
                                        {isAnalyzing ? "🔬 AI is analyzing your report..." : "Uploading..."}
                                    </span>
                                    <span className="text-cyan-600">{uploadProgress}%</span>
                                </div>
                                <div className="w-full h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300"
                                        style={{ width: `${uploadProgress}%` }}
                                    />
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={onClose}
                                className="flex-1 py-2.5 px-4 border border-gray-300 dark:border-slate-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleUploadAndAnalyze}
                                disabled={!file || isUploading || isAnalyzing}
                                className="flex-1 py-2.5 px-4 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {isUploading || isAnalyzing ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        {isAnalyzing ? "Analyzing..." : "Uploading..."}
                                    </>
                                ) : (
                                    <>
                                        <Upload className="w-4 h-4" />
                                        Analyze Report
                                    </>
                                )}
                            </button>
                        </div>
                    </>
                )}

                {/* Step 2: Review Extracted Info */}
                {step === "review" && extractedInfo && (
                    <>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                            Please review the information extracted from your report. Click "Save to Profile" to add it to your health memory.
                        </p>

                        {/* Summary */}
                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 mb-4">
                            <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300 font-medium text-sm mb-1">
                                <Info className="w-4 h-4" />
                                Summary
                            </div>
                            <p className="text-sm text-gray-700 dark:text-gray-300">{extractedInfo.summary}</p>
                            <p className="text-xs text-gray-500 mt-1">Report type: {extractedInfo.report_type}</p>
                        </div>

                        {/* Conditions */}
                        {extractedInfo.conditions.length > 0 && (
                            <div className="mb-3">
                                <div className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    <Heart className="w-4 h-4 text-red-500" />
                                    Conditions Found
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {extractedInfo.conditions.map((c, i) => (
                                        <span key={i} className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full text-xs">
                                            {c}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Medications */}
                        {extractedInfo.medications.length > 0 && (
                            <div className="mb-3">
                                <div className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    <Pill className="w-4 h-4 text-blue-500" />
                                    Medications Found
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {extractedInfo.medications.map((m, i) => (
                                        <span key={i} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-xs">
                                            {m.name} {m.dosage && `(${m.dosage})`}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Allergies */}
                        {extractedInfo.allergies.length > 0 && (
                            <div className="mb-3">
                                <div className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    <AlertTriangle className="w-4 h-4 text-yellow-500" />
                                    Allergies Found
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {extractedInfo.allergies.map((a, i) => (
                                        <span key={i} className="px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-full text-xs">
                                            {a}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Key Facts */}
                        {extractedInfo.key_facts.length > 0 && (
                            <div className="mb-4">
                                <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    Other Notable Information
                                </div>
                                <ul className="text-sm text-gray-600 dark:text-gray-400 list-disc list-inside">
                                    {extractedInfo.key_facts.map((f, i) => (
                                        <li key={i}>{f}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* No info found */}
                        {extractedInfo.conditions.length === 0 &&
                            extractedInfo.medications.length === 0 &&
                            extractedInfo.allergies.length === 0 && (
                                <div className="text-center py-4 text-gray-500">
                                    No specific health information extracted. This may not be a medical document.
                                </div>
                            )}

                        {/* Actions */}
                        <div className="flex gap-3 mt-4">
                            <button
                                onClick={() => setStep("upload")}
                                className="flex-1 py-2.5 px-4 border border-gray-300 dark:border-slate-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
                            >
                                Back
                            </button>
                            <button
                                onClick={handleConfirmAndSave}
                                disabled={isSaving}
                                className="flex-1 py-2.5 px-4 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-lg font-medium transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {isSaving ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Saving...
                                    </>
                                ) : (
                                    <>
                                        <CheckCircle className="w-4 h-4" />
                                        Save to Profile
                                    </>
                                )}
                            </button>
                        </div>
                    </>
                )}

                {/* Step 3: Saved */}
                {step === "saved" && (
                    <div className="text-center py-8">
                        <div className="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mx-auto mb-4">
                            <CheckCircle className="w-8 h-8 text-emerald-600" />
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                            Saved to Health Profile!
                        </h3>
                        <p className="text-gray-600 dark:text-gray-400 text-sm">
                            Your health information will now be used to provide personalized medical advice.
                        </p>
                    </div>
                )}

                {/* Privacy Note */}
                {step === "upload" && (
                    <p className="text-xs text-gray-400 text-center mt-4">
                        🔒 Your reports are encrypted and analyzed securely using AI
                    </p>
                )}
            </div>
        </div>
    );
}
