// Common interfaces for use across the application

export interface TimelineItem {
    type: string;
    timestamp: number;
    id?: string;
    originalIndex?: number;
    data?: {
        prompt?: string;
        completion?: {
            completion_timestamp?: number;
            text?: string;
        };
        matched_indices?: number[];
        [key: string]: any;
    };
    tags?: Record<string, string>;
    [key: string]: any;
}

export interface BufferData {
    key: string;
    buffer_items: any[];
    [key: string]: any;
}
