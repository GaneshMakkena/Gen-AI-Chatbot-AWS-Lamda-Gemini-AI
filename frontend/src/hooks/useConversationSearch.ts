/**
 * useConversationSearch hook
 * Provides filtered conversation history with debounced search.
 */

import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import type { ChatHistoryItem } from '../api/client';

interface UseSearchResult {
    query: string;
    setQuery: (q: string) => void;
    filteredItems: ChatHistoryItem[];
    isSearching: boolean;
    clearSearch: () => void;
}

/**
 * Filters chat history items by query/topic with debounce.
 * @param items - The full list of chat history items
 * @param debounceMs - Debounce delay in milliseconds (default 250)
 */
export function useConversationSearch(
    items: ChatHistoryItem[],
    debounceMs = 250
): UseSearchResult {
    const [query, setQueryRaw] = useState('');
    const [debouncedQuery, setDebouncedQuery] = useState('');
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Debounce the search input
    const setQuery = useCallback((q: string) => {
        setQueryRaw(q);
        if (timerRef.current) clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => setDebouncedQuery(q), debounceMs);
    }, [debounceMs]);

    useEffect(() => {
        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, []);

    const filteredItems = useMemo(() => {
        const trimmed = debouncedQuery.trim().toLowerCase();
        if (!trimmed) return items;

        return items.filter(item =>
            item.query.toLowerCase().includes(trimmed) ||
            item.topic.toLowerCase().includes(trimmed)
        );
    }, [items, debouncedQuery]);

    const clearSearch = useCallback(() => {
        setQueryRaw('');
        setDebouncedQuery('');
        if (timerRef.current) clearTimeout(timerRef.current);
    }, []);

    return {
        query,
        setQuery,
        filteredItems,
        isSearching: debouncedQuery.trim().length > 0,
        clearSearch,
    };
}
