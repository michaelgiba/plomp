import { STATE } from './constants';
import { Utils } from './utils';
import { UIComponents } from './ui-components';
import { TimelineRenderer } from './timeline-renderer';
import { EventHandlers } from './event-handlers';
import * as d3 from 'd3';  // Proper import for d3
import { TimelineItem } from './models';

// Define global variable provided by the application
declare const __PLOMP_BUFFER_JSON__: any;

// Main timeline view controller
const TimelineView = {
    render: function(container: HTMLElement): void {
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) {
            loadingDiv.style.display = 'block';
        }

        container.innerHTML = '';

        const timelineContainer = document.createElement('div');
        container.appendChild(timelineContainer);

        STATE.bufferData = __PLOMP_BUFFER_JSON__;
        const items: TimelineItem[] = Utils.convertBufferDataToTimelineItems(STATE.bufferData);

        if (!items.length) {
            timelineContainer.innerHTML = '<p>No buffer items to display.</p>';
            if (loadingDiv) {
                loadingDiv.style.display = 'none';
            }
            return;
        }

        UIComponents.setupStatsSection(container, STATE.bufferData, items);
        const tooltip = UIComponents.createTooltip(container);

        const width = container.clientWidth;
        const itemHeight = 20;
        const height = items.length * itemHeight + 10;
        const leftColumnWidth = 70;

        const svg = TimelineRenderer.createSVG(timelineContainer, width, height);

        const yScale = d3.scaleBand()
            .domain(d3.range(items.length).map(i => i.toString())) // Convert numbers to strings
            .range([0, height])
            .padding(0.1);

        TimelineRenderer.renderTimestamps(svg, yScale, items, leftColumnWidth);
        TimelineRenderer.renderItemBlocks(svg, yScale, items, width, leftColumnWidth, tooltip);

        UIComponents.setupTagFilters(items);
        EventHandlers.setupSteppingControls(items);

        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
    }
};

// Initialize the viewer
const PlompViewer = {
    init: function(): void {
        const timelineView = document.getElementById('timeline-view');
        if (timelineView) {
            TimelineView.render(timelineView);
        }
    }
};

document.addEventListener('DOMContentLoaded', PlompViewer.init);

// Export to global scope for external access
declare global {
    interface Window {
        PlompViewer: typeof PlompViewer;
    }
}
window.PlompViewer = PlompViewer;

// Export PlompViewer as default for webpack
export default PlompViewer;
