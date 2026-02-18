/**
 * PDF Export Utility
 * Exports a conversation (messages + images) to a downloadable PDF.
 * Uses the browser's print-to-PDF capabilities with a hidden iframe.
 */

import type { ChatResponse } from '../types/api';

interface ExportMessage {
    role: 'user' | 'assistant';
    content: string;
    response?: ChatResponse;
    timestamp: Date;
}

/**
 * Generate a printable HTML document from conversation messages
 * and trigger the browser's print dialog for PDF export.
 */
export function exportConversationAsPdf(
    messages: ExportMessage[],
    title = 'MediBot Conversation'
): void {
    const html = buildExportHtml(messages, title);

    // Create a hidden iframe, write the HTML, and trigger print
    const iframe = document.createElement('iframe');
    iframe.style.position = 'fixed';
    iframe.style.top = '-10000px';
    iframe.style.left = '-10000px';
    iframe.style.width = '1px';
    iframe.style.height = '1px';
    document.body.appendChild(iframe);

    const doc = iframe.contentDocument || iframe.contentWindow?.document;
    if (!doc) {
        document.body.removeChild(iframe);
        throw new Error('Could not create export document');
    }

    doc.open();
    doc.write(html);
    doc.close();

    // Wait for content to render, then print
    iframe.onload = () => {
        setTimeout(() => {
            iframe.contentWindow?.print();
            // Clean up after dialog closes
            setTimeout(() => {
                document.body.removeChild(iframe);
            }, 1000);
        }, 500);
    };
}

function buildExportHtml(messages: ExportMessage[], title: string): string {
    const messagesHtml = messages
        .map(msg => {
            const roleLabel = msg.role === 'user' ? '🧑 You' : '🤖 MediBot';
            const roleClass = msg.role === 'user' ? 'user-msg' : 'assistant-msg';
            const time = msg.timestamp.toLocaleString();

            const content = escapeHtml(msg.content);
            // Render step images if present
            let stepsHtml = '';
            if (msg.response?.step_images?.length) {
                stepsHtml = msg.response.step_images
                    .map(step => `
                        <div class="step-card">
                            <h4>Step ${escapeHtml(step.step_number)}: ${escapeHtml(step.title)}</h4>
                            <p>${escapeHtml(step.description)}</p>
                            ${step.image_url ? `<img src="${escapeHtml(step.image_url)}" alt="Step ${escapeHtml(step.step_number)}" />` : ''}
                        </div>
                    `)
                    .join('');
            }

            return `
                <div class="message ${roleClass}">
                    <div class="message-header">
                        <strong>${roleLabel}</strong>
                        <span class="timestamp">${time}</span>
                    </div>
                    <div class="message-content">${content}</div>
                    ${stepsHtml}
                </div>
            `;
        })
        .join('');

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>${escapeHtml(title)}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 2rem;
            color: #1a1a1a;
            line-height: 1.6;
        }
        h1 {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            color: #2563eb;
        }
        .subtitle {
            color: #666;
            font-size: 0.875rem;
            margin-bottom: 2rem;
            border-bottom: 1px solid #e5e5e5;
            padding-bottom: 1rem;
        }
        .message {
            margin-bottom: 1.5rem;
            padding: 1rem;
            border-radius: 8px;
            page-break-inside: avoid;
        }
        .user-msg { background: #f0f4ff; border-left: 3px solid #2563eb; }
        .assistant-msg { background: #f9fafb; border-left: 3px solid #10b981; }
        .message-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }
        .timestamp { color: #999; }
        .message-content { white-space: pre-wrap; }
        .step-card {
            margin-top: 0.75rem;
            padding: 0.75rem;
            background: white;
            border: 1px solid #e5e5e5;
            border-radius: 6px;
            page-break-inside: avoid;
        }
        .step-card h4 { color: #2563eb; margin-bottom: 0.25rem; }
        .step-card img {
            max-width: 100%;
            height: auto;
            margin-top: 0.5rem;
            border-radius: 4px;
        }
        @media print {
            body { padding: 0.5rem; }
            .message { box-shadow: none; }
        }
    </style>
</head>
<body>
    <h1>🏥 ${escapeHtml(title)}</h1>
    <div class="subtitle">
        Exported on ${new Date().toLocaleString()} &middot; ${messages.length} messages
    </div>
    ${messagesHtml}
</body>
</html>`;
}

function escapeHtml(str: string): string {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
