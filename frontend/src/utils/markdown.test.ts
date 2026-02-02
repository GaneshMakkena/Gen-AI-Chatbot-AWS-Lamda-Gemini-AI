import { describe, it, expect } from 'vitest';
import { formatMarkdown, sanitizeHtml } from './markdown';

describe('markdown utils', () => {
  it('formats basic markdown into HTML', () => {
    const html = formatMarkdown('**Bold**\n\n- Item');
    expect(html).toContain('<strong>Bold</strong>');
    expect(html).toContain('<ul>');
    expect(html).toContain('<li>Item</li>');
  });

  it('sanitizes disallowed tags and attributes', () => {
    const html = sanitizeHtml('<p onclick="alert(1)">Safe</p><script>alert(1)</script>');
    expect(html).toContain('<p>Safe</p>');
    expect(html).not.toContain('onclick');
    expect(html).not.toContain('<script');
  });

  it('removes potentially dangerous elements', () => {
    const html = sanitizeHtml('<img src="x" onerror="alert(1)"><p>Ok</p>');
    expect(html).not.toContain('<img');
    expect(html).toContain('<p>Ok</p>');
  });
});
