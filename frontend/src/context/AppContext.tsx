/**
 * Application Context
 * Global state management using React Context for auth info,
 * language preference, and theme settings.
 */

import { createContext, useContext, useReducer, useCallback, useMemo, type ReactNode } from 'react';

// ---- State Types ----

export type Language = 'English' | 'Telugu' | 'Hindi' | 'Spanish' | 'French' | 'German' | 'Japanese' | 'Chinese' | 'Korean' | 'Arabic';
export type Theme = 'light' | 'dark' | 'system';

export interface AppState {
    language: Language;
    theme: Theme;
    generateImages: boolean;
    thinkingMode: boolean;
    sidebarCollapsed: boolean;
}

// ---- Actions ----

type AppAction =
    | { type: 'SET_LANGUAGE'; payload: Language }
    | { type: 'SET_THEME'; payload: Theme }
    | { type: 'TOGGLE_IMAGES'; payload?: boolean }
    | { type: 'TOGGLE_THINKING'; payload?: boolean }
    | { type: 'TOGGLE_SIDEBAR' }
    | { type: 'RESET_PREFERENCES' };

// ---- Initial State ----

const getInitialState = (): AppState => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('medibot-preferences') : null;
    const defaults: AppState = {
        language: 'English',
        theme: 'system',
        generateImages: false,
        thinkingMode: false,
        sidebarCollapsed: false,
    };

    if (saved) {
        try {
            return { ...defaults, ...JSON.parse(saved) };
        } catch {
            return defaults;
        }
    }
    return defaults;
};

// ---- Reducer ----

function appReducer(state: AppState, action: AppAction): AppState {
    let newState: AppState;

    switch (action.type) {
        case 'SET_LANGUAGE':
            newState = { ...state, language: action.payload };
            break;
        case 'SET_THEME':
            newState = { ...state, theme: action.payload };
            break;
        case 'TOGGLE_IMAGES':
            newState = { ...state, generateImages: action.payload ?? !state.generateImages };
            break;
        case 'TOGGLE_THINKING':
            newState = { ...state, thinkingMode: action.payload ?? !state.thinkingMode };
            break;
        case 'TOGGLE_SIDEBAR':
            newState = { ...state, sidebarCollapsed: !state.sidebarCollapsed };
            break;
        case 'RESET_PREFERENCES':
            newState = {
                language: 'English',
                theme: 'system',
                generateImages: false,
                thinkingMode: false,
                sidebarCollapsed: false,
            };
            break;
        default:
            return state;
    }

    // Persist to localStorage
    try {
        localStorage.setItem('medibot-preferences', JSON.stringify(newState));
    } catch {
        // localStorage may be unavailable
    }

    return newState;
}

// ---- Context ----

export interface AppContextValue {
    state: AppState;
    setLanguage: (lang: Language) => void;
    setTheme: (theme: Theme) => void;
    toggleImages: (enabled?: boolean) => void;
    toggleThinking: (enabled?: boolean) => void;
    toggleSidebar: () => void;
    resetPreferences: () => void;
}

const AppContext = createContext<AppContextValue | null>(null);

// ---- Provider ----

export function AppProvider({ children }: { children: ReactNode }) {
    const [state, dispatch] = useReducer(appReducer, undefined, getInitialState);

    const setLanguage = useCallback((lang: Language) =>
        dispatch({ type: 'SET_LANGUAGE', payload: lang }), []);
    const setTheme = useCallback((theme: Theme) =>
        dispatch({ type: 'SET_THEME', payload: theme }), []);
    const toggleImages = useCallback((enabled?: boolean) =>
        dispatch({ type: 'TOGGLE_IMAGES', payload: enabled }), []);
    const toggleThinking = useCallback((enabled?: boolean) =>
        dispatch({ type: 'TOGGLE_THINKING', payload: enabled }), []);
    const toggleSidebar = useCallback(() =>
        dispatch({ type: 'TOGGLE_SIDEBAR' }), []);
    const resetPreferences = useCallback(() =>
        dispatch({ type: 'RESET_PREFERENCES' }), []);

    const value = useMemo<AppContextValue>(() => ({
        state,
        setLanguage,
        setTheme,
        toggleImages,
        toggleThinking,
        toggleSidebar,
        resetPreferences,
    }), [state, setLanguage, setTheme, toggleImages, toggleThinking, toggleSidebar, resetPreferences]);

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    );
}

// ---- Hook ----
// eslint-disable-next-line react-refresh/only-export-components
export function useApp(): AppContextValue {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useApp must be used within an AppProvider');
    }
    return context;
}

export default AppContext;
