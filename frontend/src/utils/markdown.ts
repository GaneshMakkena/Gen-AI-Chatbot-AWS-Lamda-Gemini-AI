export function formatMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
    .replace(/<p><\/p>/g, '');
}

export function sanitizeHtml(html: string): string {
  if (typeof window === 'undefined' || typeof DOMParser === 'undefined') {
    return html.replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');
  const allowedTags = new Set(['P', 'UL', 'LI', 'STRONG', 'H2', 'H3', 'H4', 'EM', 'BR']);

  const elements = Array.from(doc.body.querySelectorAll('*'));
  for (const el of elements) {
    if (!allowedTags.has(el.tagName)) {
      const text = doc.createTextNode(el.textContent || '');
      el.replaceWith(text);
      continue;
    }

    for (const attr of Array.from(el.attributes)) {
      el.removeAttribute(attr.name);
    }
  }

  return doc.body.innerHTML;
}
