"use client";

import { useState, useRef } from "react";
import { Upload, FileText, X, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

interface ReportUploadProps {
    onAnalysisComplete: (analysis: string) => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://khucwqfzv4.execute-api.us-east-1.amazonaws.com/production";

const ALLOWED_TYPES = ["application/pdf", "image/jpeg", "image/png", "image/jpg"];
const MAX_SIZE = 10 * 1024 * 1024; // 10MB

export default function ReportUpload({ onAnalysisComplete }: ReportUploadProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [error, setError] = useState("");
    const [uploadProgress, setUploadProgress] = useState(0);

    const fileInputRef = useRef<HTMLInputElement>(null);
    const { isAuthenticated, getToken } = useAuth();

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

    async function handleUpload() {
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
            setUploadProgress(30);

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

            setUploadProgress(60);
            setIsUploading(false);
            setIsAnalyzing(true);

            // Step 3: Analyze the report
            // For now, we'll create a prompt for the chat
            const analysisPrompt = `I've uploaded a medical report (${file.name}). Please analyze it and provide:
1. Summary of key findings
2. Any abnormal values or concerns
3. Recommendations based on the report
4. Questions I should ask my doctor

Note: The file is stored at ${file_key}`;

            onAnalysisComplete(analysisPrompt);
            setUploadProgress(100);

            // Reset state
            setTimeout(() => {
                setFile(null);
                setIsOpen(false);
                setIsAnalyzing(false);
                setUploadProgress(0);
            }, 1000);

        } catch (err: any) {
            setError(err.message || "Upload failed");
            setIsUploading(false);
            setIsAnalyzing(false);
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

    if (!isAuthenticated) {
        return null; // Don't show upload button if not logged in
    }

    return (
        <>
            {/* Upload Button */}
            <button
                onClick={() => setIsOpen(true)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white text-sm font-medium transition-all shadow-md hover:shadow-lg"
                title="Upload Medical Report"
            >
                <Upload className="w-4 h-4" />
                <span className="hidden sm:inline">Upload Report</span>
            </button>

            {/* Modal */}
            {isOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-fade-in">
                        {/* Header */}
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                                Upload Medical Report
                            </h2>
                            <button
                                onClick={() => setIsOpen(false)}
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
                                        {isAnalyzing ? "Analyzing report..." : "Uploading..."}
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
                                onClick={() => setIsOpen(false)}
                                className="flex-1 py-2.5 px-4 border border-gray-300 dark:border-slate-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleUpload}
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
                                        <CheckCircle className="w-4 h-4" />
                                        Analyze Report
                                    </>
                                )}
                            </button>
                        </div>

                        {/* Privacy Note */}
                        <p className="text-xs text-gray-400 text-center mt-4">
                            🔒 Your reports are encrypted and auto-deleted after 30 days
                        </p>
                    </div>
                </div>
            )}
        </>
    );
}
