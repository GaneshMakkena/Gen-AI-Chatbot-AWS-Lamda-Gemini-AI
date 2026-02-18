/**
 * Tests for ErrorBoundary component.
 * Verifies error catching, retry, and fallback rendering.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorBoundary } from './ErrorBoundary'

// Component that throws an error on demand
function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
    if (shouldThrow) throw new Error('Test error message')
    return <div>Content rendered successfully</div>
}

describe('ErrorBoundary', () => {
    beforeEach(() => {
        // Suppress console.error from React error boundary logging
        vi.spyOn(console, 'error').mockImplementation(() => { })
    })

    describe('Normal rendering', () => {
        it('renders children when no error occurs', () => {
            render(
                <ErrorBoundary>
                    <div>Hello World</div>
                </ErrorBoundary>
            )

            expect(screen.getByText('Hello World')).toBeInTheDocument()
        })
    })

    describe('Error state', () => {
        it('displays error UI when child throws', () => {
            render(
                <ErrorBoundary>
                    <ThrowError shouldThrow={true} />
                </ErrorBoundary>
            )

            expect(screen.getByText('Something went wrong')).toBeInTheDocument()
            expect(screen.getByRole('alert')).toBeInTheDocument()
        })

        it('shows Try Again and Go Home buttons', () => {
            render(
                <ErrorBoundary>
                    <ThrowError shouldThrow={true} />
                </ErrorBoundary>
            )

            expect(screen.getByText('Try Again')).toBeInTheDocument()
            expect(screen.getByText('Go Home')).toBeInTheDocument()
        })

        it('renders custom fallback when provided', () => {
            render(
                <ErrorBoundary fallback={<div>Custom fallback UI</div>}>
                    <ThrowError shouldThrow={true} />
                </ErrorBoundary>
            )

            expect(screen.getByText('Custom fallback UI')).toBeInTheDocument()
            expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
        })
    })

    describe('Recovery', () => {
        it('recovers when Try Again is clicked', () => {
            const { rerender } = render(
                <ErrorBoundary>
                    <ThrowError shouldThrow={true} />
                </ErrorBoundary>
            )

            expect(screen.getByText('Something went wrong')).toBeInTheDocument()

            // Simulate child fix before retrying so boundary can recover.
            rerender(
                <ErrorBoundary>
                    <ThrowError shouldThrow={false} />
                </ErrorBoundary>
            )

            // Click retry — the boundary resets its state
            fireEvent.click(screen.getByText('Try Again'))

            expect(screen.getByText('Content rendered successfully')).toBeInTheDocument()
        })
    })

    describe('Accessibility', () => {
        it('has role=alert on error container', () => {
            render(
                <ErrorBoundary>
                    <ThrowError shouldThrow={true} />
                </ErrorBoundary>
            )

            const alertEl = screen.getByRole('alert')
            expect(alertEl).toHaveAttribute('aria-live', 'assertive')
        })
    })
})
