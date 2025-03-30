import { COLORS, STATE } from './constants';
import { Utils } from './utils';
import { UIComponents } from './ui-components';
import * as d3 from 'd3';
import { TimelineItem } from './models';

export const TimelineRenderer = {
    createSVG: function(
        container: HTMLElement, 
        width: number, 
        height: number
    ): d3.Selection<SVGSVGElement, unknown, null, undefined> {
        return d3.select(container)
            .append('svg')
            .attr('width', width - 400)
            .attr('height', height);
    },

    renderTimestamps: function(
        svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
        yScale: d3.ScaleBand<string>, // Update to string domain
        items: TimelineItem[],
        leftColumnWidth: number
    ): d3.Selection<SVGGElement, unknown, null, undefined> {
        const timestampGroup = svg.append('g')
            .attr('class', 'timestamp-group');
        timestampGroup.selectAll('.timestamp')
            .data(items)
            .enter()
            .append('text')
            .attr('class', 'timestamp')
            .attr('x', leftColumnWidth - 6)
            .attr('y', (d, i) => {
                // Add null checking to handle possible undefined
                const yPos = yScale(i.toString());
                return (yPos ?? 0) + yScale.bandwidth() - 4; // Use nullish coalescing operator
            })
            .attr('text-anchor', 'end')
            .style('font-size', '10px')
            .style('fill', COLORS.TEXT)
            .text(d => new Date(d.timestamp).toLocaleTimeString());

        return timestampGroup;
    },

    renderItemBlocks: function(
        svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
        yScale: d3.ScaleBand<string>, // Update to string domain
        items: TimelineItem[],
        width: number,
        leftColumnWidth: number,
        tooltip: d3.Selection<HTMLDivElement, unknown, null, undefined>
    ): d3.Selection<SVGGElement, unknown, null, undefined> {
        const itemBlocksGroup = svg.append('g')
            .attr('class', 'item-block-group');

        const blocks = itemBlocksGroup.selectAll('.timeline-item')
            .data(items)
            .enter()
            .append('g')
            .attr('class', 'timeline-item')
            .attr('transform', (d, i) => {
                const yPos = yScale(i.toString()) ?? 0; // Add null checking
                if (d.type === 'prompt-completion') {
                    return `translate(${leftColumnWidth + 20}, ${yPos})`;
                }
                return `translate(${leftColumnWidth}, ${yPos})`;
            });

        blocks.append('rect')
            .attr('height', yScale.bandwidth())
            .attr('width', width - 500)
            .attr('fill', (d, i) => Utils.getItemColor(d, i, items));

        blocks.append('text')
            .attr('x', 4)
            .attr('y', yScale.bandwidth() - 4)
            .style('font-size', '10px')
            .attr('fill', '#fff')
            .text((d, i) => {
                const base = `#${i}: ${d.type}`;
                let snippet = '';
                if (d.data?.prompt) snippet = d.data.prompt.substring(0, 100);
                else if (d.data?.completion?.text) snippet = d.data.completion.text.substring(0, 100);
                else if (d.data) snippet = JSON.stringify(d.data).substring(0, 100);
                return snippet ? base + ' - ' + snippet + '...' : base;
            });

        TimelineRenderer.attachBlockEvents(blocks, items, tooltip);

        return itemBlocksGroup;
    },

    attachBlockEvents: function(
        blocks: d3.Selection<SVGGElement, TimelineItem, SVGGElement, unknown>,
        items: TimelineItem[],
        tooltip: d3.Selection<HTMLDivElement, unknown, null, undefined>
    ): void {
        blocks.on('mouseover', function(event: MouseEvent, d: TimelineItem) {
            if (!STATE.steppingEnabled || items.indexOf(d) <= STATE.currentStepIndex) {
                if (STATE.queryFocusMode && !STATE.matchedIndices.includes(items.indexOf(d)) &&
                    !(d.type === 'query' && STATE.matchedIndices.length > 0)) {
                    // Don't highlight non-matched items in query focus mode
                    return;
                }

                if (d.type === 'prompt-request') d3.select(this).select('rect').attr('fill', COLORS.PROMPT_REQUEST.HOVER);
                else if (d.type === 'prompt-completion') d3.select(this).select('rect').attr('fill', COLORS.PROMPT_COMPLETION.HOVER);
                else if (d.type === 'event') d3.select(this).select('rect').attr('fill', COLORS.EVENT.HOVER);
                else if (d.type === 'query') d3.select(this).select('rect').attr('fill', COLORS.QUERY.HOVER);
                else d3.select(this).select('rect').attr('fill', COLORS.DEFAULT.HOVER);
            }

            const sTime = new Date(d.timestamp).toLocaleTimeString();
            let html = `<strong>${d.type.toUpperCase()}</strong><br>Timestamp: ${sTime}`;
            if (d.tags) {
                html += `<br>Tags: ${JSON.stringify(d.tags)}`;
            }
            tooltip.style('display', 'block').html(html)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function(event: MouseEvent, d: TimelineItem) {
            const i = items.indexOf(d);
            d3.select(this).select('rect').attr('fill', Utils.getItemColor(d, i, items));
            tooltip.style('display', 'none');
        })
        .on('click', function(event: MouseEvent, d: TimelineItem) {
            const itemIndex = items.indexOf(d);
            UIComponents.updateDetailsSidebar(d, itemIndex);

            // Process query item highlighting
            if (d.type === 'query') {
                // Handle clicking on the same query again (toggle off highlights)
                if (STATE.selectedQueryIndex === itemIndex) {
                    Utils.clearQueryHighlights();
                } else {
                    // Pass true to enable focus mode (grey out non-matched items)
                    Utils.updateMatchedIndices(d, items, true);
                }
            } else {
                // Clear matched indices when clicking non-query items
                Utils.clearQueryHighlights();
            }

            // Update display to reflect matched items
            TimelineRenderer.updateItemsDisplay(items);
        })
        .on('dblclick', function(event: MouseEvent, d: TimelineItem) {
            const sidebar = document.getElementById('details-sidebar');
            if (sidebar) {
                sidebar.style.display = 'none';
            }

            // Clear matched indices on double-click
            Utils.clearQueryHighlights();
            TimelineRenderer.updateItemsDisplay(items);
        });
    },

    updateItemsDisplay: function(items: TimelineItem[]): void {
        d3.selectAll('.timeline-item')
            .select('rect')
            .attr('fill', (d: any, i: number) => Utils.getItemColor(d, i, items));

        // Show current step in sidebar
        if (STATE.steppingEnabled && STATE.currentStepIndex >= 0 && STATE.currentStepIndex < items.length) {
            UIComponents.updateDetailsSidebar(items[STATE.currentStepIndex], STATE.currentStepIndex);
        }
    }
};
