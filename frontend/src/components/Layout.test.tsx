/**
 * Tests for Layout component.
 * Tests sidebar navigation, auth state rendering, and user interactions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Layout } from './Layout'

// Mock @aws-amplify/ui-react
const mockSignOut = vi.fn()
const mockNavigate = vi.fn()

vi.mock('@aws-amplify/ui-react', () => ({
    useAuthenticator: vi.fn(() => ({
        signOut: mockSignOut,
        user: null,
        authStatus: 'unauthenticated',
    })),
}))

// Mock react-router-dom's useNavigate
vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom')
    return {
        ...actual,
        useNavigate: () => mockNavigate,
    }
})

// Import mock so we can change return values per test
import { useAuthenticator } from '@aws-amplify/ui-react'
const mockUseAuth = vi.mocked(useAuthenticator)

const asAuthenticatorState = (
    value: {
        signOut: typeof mockSignOut
        user: { signInDetails?: { loginId?: string }; username?: string } | null
        authStatus: 'unauthenticated' | 'authenticated'
    }
) => value as unknown as ReturnType<typeof useAuthenticator>

describe('Layout', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockUseAuth.mockReturnValue(asAuthenticatorState({
            signOut: mockSignOut,
            user: null,
            authStatus: 'unauthenticated',
        }))
    })

    const renderLayout = () =>
        render(
            <MemoryRouter>
                <Layout />
            </MemoryRouter>
        )

    describe('Unauthenticated state', () => {
        it('renders app logo', () => {
            renderLayout()
            expect(screen.getByText(/MediBot/)).toBeInTheDocument()
        })

        it('shows Chat navigation link', () => {
            renderLayout()
            expect(screen.getByText('Chat')).toBeInTheDocument()
        })

        it('shows Sign In / Sign Up button', () => {
            renderLayout()
            expect(screen.getByText('Sign In / Sign Up')).toBeInTheDocument()
        })

        it('does NOT show History, Profile, or Upload links', () => {
            renderLayout()
            expect(screen.queryByText('History')).not.toBeInTheDocument()
            expect(screen.queryByText('Profile')).not.toBeInTheDocument()
            expect(screen.queryByText('Upload Report')).not.toBeInTheDocument()
        })

        it('navigates to /login when Sign In is clicked', () => {
            renderLayout()
            fireEvent.click(screen.getByText('Sign In / Sign Up'))
            expect(mockNavigate).toHaveBeenCalledWith('/login')
        })
    })

    describe('Authenticated state', () => {
        beforeEach(() => {
            mockUseAuth.mockReturnValue(asAuthenticatorState({
                signOut: mockSignOut,
                user: {
                    signInDetails: { loginId: 'jane@example.com' },
                    username: 'jane123',
                },
                authStatus: 'authenticated',
            }))
        })

        it('shows all nav links including History, Profile, Upload', () => {
            renderLayout()
            expect(screen.getByText('Chat')).toBeInTheDocument()
            expect(screen.getByText('History')).toBeInTheDocument()
            expect(screen.getByText('Profile')).toBeInTheDocument()
            expect(screen.getByText('Upload Report')).toBeInTheDocument()
        })

        it('shows user avatar with first letter of email', () => {
            renderLayout()
            expect(screen.getByText('J')).toBeInTheDocument()
        })

        it('shows user email', () => {
            renderLayout()
            expect(screen.getByText('jane@example.com')).toBeInTheDocument()
        })

        it('calls signOut when sign out button is clicked', () => {
            renderLayout()
            fireEvent.click(screen.getByTitle('Sign Out'))
            expect(mockSignOut).toHaveBeenCalled()
        })
    })

    describe('New Chat button', () => {
        it('navigates to /chat when clicked', () => {
            renderLayout()
            fireEvent.click(screen.getByText('New Chat'))
            expect(mockNavigate).toHaveBeenCalledWith('/chat')
        })
    })
})
