/**
 * Tests for Toast notification components.
 * Tests ToastProvider, ToastContainer, and ToastItem rendering and interactions.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { useContext } from 'react'
import { ToastProvider } from './Toast'
import { ToastContext } from './ToastContext'

// Helper component to trigger toasts from within the provider
function ToastTrigger() {
    const toast = useContext(ToastContext)
    if (!toast) return null

    return (
        <div>
            <button onClick={() => toast.success('Success message')}>Show Success</button>
            <button onClick={() => toast.error('Error message')}>Show Error</button>
            <button onClick={() => toast.warning('Warning message')}>Show Warning</button>
            <button onClick={() => toast.info('Info message')}>Show Info</button>
        </div>
    )
}

describe('Toast Components', () => {
    beforeEach(() => {
        vi.useFakeTimers()
    })

    afterEach(() => {
        vi.useRealTimers()
    })

    describe('ToastProvider', () => {
        it('renders children correctly', () => {
            render(
                <ToastProvider>
                    <div>App Content</div>
                </ToastProvider>
            )

            expect(screen.getByText('App Content')).toBeInTheDocument()
        })
    })

    describe('Toast display', () => {
        it('shows success toast when triggered', () => {
            render(
                <ToastProvider>
                    <ToastTrigger />
                </ToastProvider>
            )

            fireEvent.click(screen.getByText('Show Success'))

            expect(screen.getByText('Success message')).toBeInTheDocument()
        })

        it('shows error toast when triggered', () => {
            render(
                <ToastProvider>
                    <ToastTrigger />
                </ToastProvider>
            )

            fireEvent.click(screen.getByText('Show Error'))

            expect(screen.getByText('Error message')).toBeInTheDocument()
        })

        it('shows multiple toasts simultaneously', () => {
            render(
                <ToastProvider>
                    <ToastTrigger />
                </ToastProvider>
            )

            fireEvent.click(screen.getByText('Show Success'))
            fireEvent.click(screen.getByText('Show Warning'))

            expect(screen.getByText('Success message')).toBeInTheDocument()
            expect(screen.getByText('Warning message')).toBeInTheDocument()
        })
    })

    describe('Toast auto-dismiss', () => {
        it('auto-dismisses success toast after duration', () => {
            render(
                <ToastProvider>
                    <ToastTrigger />
                </ToastProvider>
            )

            fireEvent.click(screen.getByText('Show Success'))
            expect(screen.getByText('Success message')).toBeInTheDocument()

            // Default duration is 5000ms
            act(() => {
                vi.advanceTimersByTime(5100)
            })

            expect(screen.queryByText('Success message')).not.toBeInTheDocument()
        })
    })

    describe('Toast dismiss button', () => {
        it('dismisses toast when dismiss button is clicked', () => {
            render(
                <ToastProvider>
                    <ToastTrigger />
                </ToastProvider>
            )

            fireEvent.click(screen.getByText('Show Info'))
            expect(screen.getByText('Info message')).toBeInTheDocument()

            // Click the dismiss button
            const dismissBtn = screen.getByLabelText('Dismiss notification')
            fireEvent.click(dismissBtn)

            // Allow exit animation
            act(() => {
                vi.advanceTimersByTime(300)
            })

            expect(screen.queryByText('Info message')).not.toBeInTheDocument()
        })
    })

    describe('Toast accessibility', () => {
        it('has role=alert on toast items', () => {
            render(
                <ToastProvider>
                    <ToastTrigger />
                </ToastProvider>
            )

            fireEvent.click(screen.getByText('Show Error'))

            const alerts = screen.getAllByRole('alert')
            expect(alerts.length).toBeGreaterThan(0)
        })

        it('toast container has aria-label for notifications region', () => {
            render(
                <ToastProvider>
                    <ToastTrigger />
                </ToastProvider>
            )

            fireEvent.click(screen.getByText('Show Success'))

            expect(screen.getByRole('region', { name: 'Notifications' })).toBeInTheDocument()
        })
    })
})
