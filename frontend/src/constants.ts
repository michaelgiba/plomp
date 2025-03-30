// Define TypeScript interfaces for the color structure
interface PromptRequestColors {
    NORMAL: string;
    INCOMPLETE: string;
    HOVER: string;
}

interface StandardColors {
    NORMAL: string;
    HOVER: string;
}

interface Colors {
    CURRENT_STEP: string;
    PROMPT_REQUEST: PromptRequestColors;
    PROMPT_COMPLETION: StandardColors;
    EVENT: StandardColors;
    QUERY: StandardColors;
    DEFAULT: StandardColors;
    FUTURE_ITEM: string;
    TEXT: string;
    MATCHED_ITEM: string;
    GREYED_OUT: string;
}

interface State {
    steppingEnabled: boolean;
    currentStepIndex: number;
    matchedIndices: number[];
    queryFocusMode: boolean;
    selectedQueryIndex: number;
    bufferData: any | null;
}

export const COLORS: Colors = {
    CURRENT_STEP: '#b38c00',         // Vibrant orange for current step (kept for visibility)
    PROMPT_REQUEST: {
        NORMAL: '#5b9bd5',           // Clearer blue for completed prompt requests
        INCOMPLETE: '#f17575',       // More distinct red for incomplete prompt requests
        HOVER: '#3c78c3'             // Deeper blue for hover state
    },
    PROMPT_COMPLETION: {
        NORMAL: '#2c5aa0',           // Darker blue for prompt completions (better distinction)
        HOVER: '#1e3c6e'             // Even darker blue for hover
    },
    EVENT: {
        NORMAL: '#6bbf69',           // Refreshed green for events
        HOVER: '#4d8b4a'             // Darker green hover with better contrast
    },
    QUERY: {
        NORMAL: '#20a0b1',           // More vibrant teal for query items
        HOVER: '#18717d'             // Darker teal hover state for better distinction
    },
    DEFAULT: {
        NORMAL: '#9b7fc4',           // Refreshed purple for default/other items
        HOVER: '#7456a3'             // Darker purple for better hover contrast
    },
    FUTURE_ITEM: '#dbdbdb',          // Slightly darker gray for future items (better contrast)
    TEXT: '#555',                    // Slightly darker text for better readability
    MATCHED_ITEM: '#e67e22',         // Warmer orange for matched items (less aggressive than red)
    GREYED_OUT: '#d0d0d0',           // Light grey for non-matched items when a query is focused
};

// Global state
export const STATE: State = {
    steppingEnabled: false,
    currentStepIndex: 0,
    matchedIndices: [],             // Array to track currently matched indices
    queryFocusMode: false,          // Flag to track when a query is focused/selected
    selectedQueryIndex: -1,         // Track the currently selected query's index
    bufferData: null                // Will be initialized
};
