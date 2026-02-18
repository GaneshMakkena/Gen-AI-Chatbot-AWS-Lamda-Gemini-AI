/**
 * Skip Navigation Link
 * Accessibility improvement: allows keyboard users to skip
 * the sidebar navigation and jump directly to main content.
 */

import './SkipLink.css';

export function SkipLink() {
    return (
        <a href="#main-content" className="skip-link">
            Skip to main content
        </a>
    );
}
