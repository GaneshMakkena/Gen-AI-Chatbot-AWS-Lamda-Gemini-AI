"use client";

import { X, FileText, Image as ImageIcon } from "lucide-react";

interface AttachedFile {
    id: string;
    file: File;
    preview?: string;
    type: "pdf" | "image";
}

interface FileAttachmentsProps {
    files: AttachedFile[];
    onRemove: (id: string) => void;
    maxPdfs?: number;
    maxImages?: number;
    maxTotalSizeMB?: number;
}

export default function FileAttachments({
    files,
    onRemove,
    maxPdfs = 5,
    maxImages = 10,
    maxTotalSizeMB = 50,
}: FileAttachmentsProps) {
    if (files.length === 0) return null;

    const pdfCount = files.filter((f) => f.type === "pdf").length;
    const imageCount = files.filter((f) => f.type === "image").length;
    const totalSizeMB = files.reduce((sum, f) => sum + f.file.size / 1024 / 1024, 0);

    return (
        <div className="px-2 py-2 bg-gray-50 dark:bg-slate-800/50 border-b border-gray-200 dark:border-slate-700">
            {/* File chips */}
            <div className="flex flex-wrap gap-2">
                {files.map((file) => (
                    <div
                        key={file.id}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${file.type === "pdf"
                                ? "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300"
                                : "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                            }`}
                    >
                        {file.type === "pdf" ? (
                            <FileText className="w-4 h-4" />
                        ) : file.preview ? (
                            <img
                                src={file.preview}
                                alt=""
                                className="w-6 h-6 rounded object-cover"
                            />
                        ) : (
                            <ImageIcon className="w-4 h-4" />
                        )}
                        <span className="max-w-[120px] truncate">{file.file.name}</span>
                        <button
                            onClick={() => onRemove(file.id)}
                            className="p-0.5 hover:bg-black/10 dark:hover:bg-white/10 rounded-full"
                        >
                            <X className="w-3.5 h-3.5" />
                        </button>
                    </div>
                ))}
            </div>

            {/* Limits indicator */}
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                <span>
                    📄 {pdfCount}/{maxPdfs} PDFs
                </span>
                <span>
                    🖼️ {imageCount}/{maxImages} Images
                </span>
                <span>
                    💾 {totalSizeMB.toFixed(1)}/{maxTotalSizeMB}MB
                </span>
            </div>
        </div>
    );
}

// Utility to create attached file with preview
export function createAttachedFile(file: File): AttachedFile {
    const type = file.type.startsWith("image/") ? "image" : "pdf";
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;

    let preview: string | undefined;
    if (type === "image") {
        preview = URL.createObjectURL(file);
    }

    return { id, file, preview, type };
}

// Validate file limits
export function validateFiles(
    currentFiles: AttachedFile[],
    newFiles: File[],
    maxPdfs = 5,
    maxImages = 10,
    maxTotalSizeMB = 50
): { valid: boolean; error?: string; acceptedFiles: AttachedFile[] } {
    const allFiles = [...currentFiles];
    const acceptedFiles: AttachedFile[] = [];

    for (const file of newFiles) {
        const isPdf = file.type === "application/pdf";
        const isImage = file.type.startsWith("image/");

        if (!isPdf && !isImage) {
            continue; // Skip unsupported files
        }

        const currentPdfs = allFiles.filter((f) => f.type === "pdf").length;
        const currentImages = allFiles.filter((f) => f.type === "image").length;
        const currentSize = allFiles.reduce((sum, f) => sum + f.file.size / 1024 / 1024, 0);
        const newSize = file.size / 1024 / 1024;

        if (isPdf && currentPdfs >= maxPdfs) {
            return { valid: false, error: `Maximum ${maxPdfs} PDFs allowed`, acceptedFiles };
        }

        if (isImage && currentImages >= maxImages) {
            return { valid: false, error: `Maximum ${maxImages} images allowed`, acceptedFiles };
        }

        if (currentSize + newSize > maxTotalSizeMB) {
            return { valid: false, error: `Total size cannot exceed ${maxTotalSizeMB}MB`, acceptedFiles };
        }

        const attached = createAttachedFile(file);
        allFiles.push(attached);
        acceptedFiles.push(attached);
    }

    return { valid: true, acceptedFiles };
}

// Export AttachedFile type
export type { AttachedFile };
