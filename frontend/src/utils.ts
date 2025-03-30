import { COLORS, STATE } from './constants';
import { TimelineItem, BufferData } from './models';

export const Utils = {
    getItemColor: function(d: TimelineItem, index: number, items: TimelineItem[]): string {
        // Matched items take priority in normal mode, even without graying out others
        if (STATE.matchedIndices.includes(index)) {
            return COLORS.MATCHED_ITEM;
        }

        // When in query focus mode, non-matched items are greyed out (except the query itself)
        if (STATE.queryFocusMode) {
            // The query item itself keeps its color
            if (d.type === 'query' && index === STATE.selectedQueryIndex) {
                if (STATE.steppingEnabled) {
                    return COLORS.CURRENT_STEP;
                } else {
                    return COLORS.QUERY.NORMAL;
                }                
            }

            // Non-matched items are greyed out
            return COLORS.GREYED_OUT;
        }

        // Original color logic for normal and stepping modes
        if (STATE.steppingEnabled) {
            if (index === STATE.currentStepIndex) {
                return COLORS.CURRENT_STEP;
            } else if (index < STATE.currentStepIndex) {
                // Normal colors for executed items
                if (d.type === 'prompt-request') {
                    const completed = items.some(it => it.type === 'prompt-completion' && it.id === d.id);
                    return completed ? COLORS.PROMPT_REQUEST.NORMAL : COLORS.PROMPT_REQUEST.INCOMPLETE;
                }
                if (d.type === 'prompt-completion') return COLORS.PROMPT_COMPLETION.NORMAL;
                if (d.type === 'event') return COLORS.EVENT.NORMAL;
                if (d.type === 'query') return COLORS.QUERY.NORMAL;
                return COLORS.DEFAULT.NORMAL;
            } else {
                return COLORS.FUTURE_ITEM;
            }
        } else {
            // Normal colors when stepping is disabled
            if (d.type === 'prompt-request') {
                const completed = items.some(it => it.type === 'prompt-completion' && it.id === d.id);
                return completed ? COLORS.PROMPT_REQUEST.NORMAL : COLORS.PROMPT_REQUEST.INCOMPLETE;
            }
            if (d.type === 'prompt-completion') return COLORS.PROMPT_COMPLETION.NORMAL;
            if (d.type === 'event') return COLORS.EVENT.NORMAL;
            if (d.type === 'query') return COLORS.QUERY.NORMAL;
            return COLORS.DEFAULT.NORMAL;
        }
    },

    processBufferItems: function(bufferData: BufferData | null): TimelineItem[] {
        if (!bufferData || !Array.isArray(bufferData.buffer_items)) {
            return [];
        }

        // Transform bufferData items so that each 'prompt' item generates two entries
        const expandedItems: TimelineItem[] = [];

        // Track the original buffer index for each item
        bufferData.buffer_items.forEach((originalItem, originalIndex) => {
            if (originalItem.type === 'prompt') {
                // Prompt request version - add originalIndex reference
                expandedItems.push({
                    ...originalItem,
                    type: 'prompt-request',
                    originalIndex: originalIndex
                });
                // Optional prompt completion - shares same originalIndex
                if (originalItem.data?.completion?.completion_timestamp) {
                    expandedItems.push({
                        ...originalItem,
                        type: 'prompt-completion',
                        timestamp: originalItem.data.completion.completion_timestamp,
                        originalIndex: originalIndex
                    });
                }
            } else {
                // Non-prompt items - add originalIndex reference
                expandedItems.push({
                    ...originalItem,
                    originalIndex: originalIndex
                });
            }
        });

        return expandedItems.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    },

    extractTagPairs: function(items: TimelineItem[]): Set<string> {
        const allTagPairs = new Set<string>();
        items.forEach(item => {
            if (item.tags) {
                Object.entries(item.tags).forEach(([k, v]) => {
                    allTagPairs.add(`${k}=${v}`);
                });
            }
        });
        return allTagPairs;
    },

    // Process query item to highlight matched indices
    updateMatchedIndices: function(queryItem: TimelineItem, items: TimelineItem[], enableFocusMode = false): void {
        // Clear previous matched indices
        STATE.matchedIndices = [];

        // If not a query item, just return
        if (!queryItem || queryItem.type !== 'query') {
            STATE.queryFocusMode = false;
            STATE.selectedQueryIndex = -1;
            return;
        }

        STATE.selectedQueryIndex = items.indexOf(queryItem);

        // Extract matched indices from query data
        if (queryItem.data && Array.isArray(queryItem.data.matched_indices)) {
            const originalMatchedIndices = [...queryItem.data.matched_indices];

            // Translate original indices to expanded timeline indices
            items.forEach((item, expandedIndex) => {
                if (originalMatchedIndices.includes(item.originalIndex as number)) {
                    STATE.matchedIndices.push(expandedIndex);
                }
            });
        }
        STATE.queryFocusMode = enableFocusMode;
    },

    // Clear all query highlights
    clearQueryHighlights: function(): void {
        STATE.matchedIndices = [];
        STATE.queryFocusMode = false;
        STATE.selectedQueryIndex = -1;
    }
};
