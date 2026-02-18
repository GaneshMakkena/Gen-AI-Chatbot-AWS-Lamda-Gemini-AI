/**
 * Tests for LoadingSpinner, Skeleton, and ProgressBar components.
 * Verifies rendering, props, and accessibility attributes.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingSpinner, Skeleton, ProgressBar } from './LoadingSpinner'

describe('LoadingSpinner', () => {
    describe('Default rendering', () => {
        it('renders with default message', () => {
            render(<LoadingSpinner />)

            expect(screen.getByText('Loading...')).toBeInTheDocument()
        })

        it('has role=status for accessibility', () => {
            render(<LoadingSpinner />)

            expect(screen.getByRole('status')).toBeInTheDocument()
        })

        it('has aria-busy attribute', () => {
            render(<LoadingSpinner />)

            expect(screen.getByRole('status')).toHaveAttribute('aria-busy', 'true')
        })
    })

    describe('Custom props', () => {
        it('renders custom message', () => {
            render(<LoadingSpinner message="Processing your request..." />)

            expect(screen.getByText('Processing your request...')).toBeInTheDocument()
        })

        it('applies size class', () => {
            const { container } = render(<LoadingSpinner size="large" />)

            expect(container.querySelector('.loading-spinner--large')).toBeInTheDocument()
        })

        it('renders overlay when fullScreen is true', () => {
            const { container } = render(<LoadingSpinner fullScreen />)

            expect(container.querySelector('.loading-spinner__overlay')).toBeInTheDocument()
        })

        it('does not render message when empty string', () => {
            const { container } = render(<LoadingSpinner message="" />)

            expect(container.querySelector('.loading-spinner__message')).not.toBeInTheDocument()
        })
    })

    describe('Screen reader support', () => {
        it('has sr-only text for screen readers', () => {
            render(<LoadingSpinner />)

            expect(screen.getByText('Loading, please wait')).toBeInTheDocument()
        })
    })
})

describe('Skeleton', () => {
    it('renders with default dimensions', () => {
        const { container } = render(<Skeleton />)

        const skeleton = container.querySelector('.skeleton')
        expect(skeleton).toBeInTheDocument()
        expect(skeleton).toHaveStyle({ width: '100%', height: '1rem' })
    })

    it('applies custom width and height', () => {
        const { container } = render(<Skeleton width={200} height={40} />)

        const skeleton = container.querySelector('.skeleton')
        expect(skeleton).toHaveStyle({ width: '200px', height: '40px' })
    })

    it('accepts string dimensions', () => {
        const { container } = render(<Skeleton width="50%" height="2rem" />)

        const skeleton = container.querySelector('.skeleton')
        expect(skeleton).toHaveStyle({ width: '50%', height: '2rem' })
    })

    it('is hidden from assistive technology', () => {
        const { container } = render(<Skeleton />)

        expect(container.querySelector('.skeleton')).toHaveAttribute('aria-hidden', 'true')
    })
})

describe('ProgressBar', () => {
    it('renders with correct ARIA attributes', () => {
        render(<ProgressBar value={50} />)

        const progressbar = screen.getByRole('progressbar')
        expect(progressbar).toHaveAttribute('aria-valuenow', '50')
        expect(progressbar).toHaveAttribute('aria-valuemin', '0')
        expect(progressbar).toHaveAttribute('aria-valuemax', '100')
    })

    it('shows percentage text by default', () => {
        render(<ProgressBar value={75} />)

        expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('hides percentage text when showPercentage is false', () => {
        render(<ProgressBar value={75} showPercentage={false} />)

        expect(screen.queryByText('75%')).not.toBeInTheDocument()
    })

    it('clamps percentage between 0 and 100', () => {
        render(<ProgressBar value={150} />)

        expect(screen.getByText('100%')).toBeInTheDocument()
    })

    it('uses custom max value', () => {
        render(<ProgressBar value={5} max={10} />)

        expect(screen.getByText('50%')).toBeInTheDocument()
    })

    it('applies custom label', () => {
        render(<ProgressBar value={30} label="Upload progress" />)

        expect(screen.getByRole('progressbar')).toHaveAttribute('aria-label', 'Upload progress')
    })
})
