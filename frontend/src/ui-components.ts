import { Utils } from './utils';
import * as d3 from 'd3';
import { TimelineItem, BufferData } from './models';

export const UIComponents = {
    setupStatsSection: function(
        container: HTMLElement, 
        bufferData: BufferData, 
        items: TimelineItem[]
    ): void {
        const statsDiv = document.getElementById('stats-section');
        if (statsDiv) {
            statsDiv.innerHTML = `
                <p style="margin: 0; font-size: 12px;"><strong>Buffer:</strong> ${bufferData.key} (${items.length} items)</p>
                <button id="step-backward" style="font-size: 12px;">&#9664;</button>
                <button id="step-forward" style="font-size: 12px;">&#9654;</button>
                <button id="toggle-stepping" style="font-size: 12px;">Enable Stepping</button>
            `;
        }
    },

    createTooltip: function(container: HTMLElement): d3.Selection<HTMLDivElement, unknown, null, undefined> {
        return d3.select(container)
            .append('div')
            .attr('class', 'timeline-tooltip');
    },

    updateDetailsSidebar: function(item: TimelineItem, index: number): void {
        const sidebar = document.getElementById('details-sidebar');
        if (sidebar) {
            sidebar.style.display = 'block';
            sidebar.innerHTML = `
                <h3>${item.type.toUpperCase()} (#${index})</h3>
                <pre>${JSON.stringify(item, null, 2)}</pre>
            `;
        }
    },

    setupTagFilters: function(items: TimelineItem[]): void {
        const allTagPairs = Utils.extractTagPairs(items);
        const tagFiltersContainer = document.getElementById('tag-filters');
        if (tagFiltersContainer) {
            tagFiltersContainer.innerHTML = '';

            allTagPairs.forEach(tagPair => {
                const btn = document.createElement('div');
                btn.className = 'tag-filter';
                btn.textContent = tagPair;
                btn.addEventListener('click', () => {
                    btn.classList.toggle('active');
                    UIComponents.applyTagFilter(items);
                });
                tagFiltersContainer.appendChild(btn);
            });
        }
    },

    applyTagFilter: function(items: TimelineItem[]): void {
        const active = Array.from(document.querySelectorAll('.tag-filter.active'))
            .map(el => (el as HTMLElement).textContent as string);

        // Build the 'visible' list based on active tags
        const visibleData = items.filter(d => {
            if (!active.length) return true;
            if (!d.tags) return false;
            return active.every(pair => {
                const [k, v] = pair.split('=');
                return d.tags?.[k] === v;
            });
        });

        // Update display styling (hide non-visible items)
        d3.selectAll('.timeline-item')
            .style('display', (d: any) => visibleData.includes(d) ? '' : 'none');
    }
};
