const PlompViewer = (function() {
    // Color constants - Improved palette
    const COLORS = {
        CURRENT_STEP: '#ff9500',         // Vibrant orange for current step (kept for visibility)
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
        MATCHED_ITEM: '#e67e22',          // Warmer orange for matched items (less aggressive than red)
        GREYED_OUT: '#d0d0d0',          // Light grey for non-matched items when a query is focused
    };
    
    const bufferData = __PLOMP_BUFFER_JSON__;
    let steppingEnabled = false;
    let currentStepIndex = 0;
    let matchedIndices = [];             // Array to track currently matched indices
    let queryFocusMode = false;          // Flag to track when a query is focused/selected
    let selectedQueryIndex = -1;         // Track the currently selected query's index
    
    // Utility functions
    const Utils = {
        getItemColor: function(d, index, items, steppingEnabled, currentStepIndex) {
            // Matched items take priority in normal mode, even without graying out others
            if (matchedIndices.includes(index)) {
                return COLORS.MATCHED_ITEM;
            }
            
            // When in query focus mode, non-matched items are greyed out (except the query itself)
            if (queryFocusMode) {
                // The query item itself keeps its color
                if (d.type === 'query' && index === selectedQueryIndex) {
                    return COLORS.QUERY.NORMAL;
                }
                
                // Non-matched items are greyed out
                return COLORS.GREYED_OUT;
            }
            
            // Original color logic for normal and stepping modes
            if (steppingEnabled) {
                if (index === currentStepIndex) {
                    return COLORS.CURRENT_STEP;
                } else if (index < currentStepIndex) {
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
        
        processBufferItems: function(bufferData) {
            if (!bufferData || !Array.isArray(bufferData.buffer_items)) {
                return [];
            }
            
            // Transform bufferData items so that each 'prompt' item generates two entries
            const expandedItems = [];
            
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
            
            return expandedItems.sort((a,b) => new Date(a.timestamp) - new Date(b.timestamp));
        },
        
        extractTagPairs: function(items) {
            const allTagPairs = new Set();
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
        updateMatchedIndices: function(queryItem, items, enableFocusMode = false) {
            // Clear previous matched indices
            matchedIndices = [];
            
            // If not a query item, just return
            if (!queryItem || queryItem.type !== 'query') {
                queryFocusMode = false;
                selectedQueryIndex = -1;
                return;
            }
            
            selectedQueryIndex = items.indexOf(queryItem);
            
            // Extract matched indices from query data
            if (queryItem.data && Array.isArray(queryItem.data.matched_indices)) {
                const originalMatchedIndices = [...queryItem.data.matched_indices];
                
                // Translate original indices to expanded timeline indices
                items.forEach((item, expandedIndex) => {
                    if (originalMatchedIndices.includes(item.originalIndex)) {
                        matchedIndices.push(expandedIndex);
                    }
                });
                
                // Only enable focus mode if explicitly requested
                queryFocusMode = enableFocusMode && matchedIndices.length > 0;
            } else {
                queryFocusMode = false;
            }
        },
        
        // Clear all query highlights
        clearQueryHighlights: function() {
            matchedIndices = [];
            queryFocusMode = false;
            selectedQueryIndex = -1;
        }
    };

    // UI component handling
    const UIComponents = {
        setupStatsSection: function(container, bufferData, items) {
            if (bufferData.key) {
                const statsDiv = document.getElementById('stats-section');
                statsDiv.innerHTML = `
                    <p style="margin: 0; font-size: 12px;"><strong>Buffer:</strong> ${bufferData.key} (${items.length} items)</p>
                    <button id="step-backward" style="font-size: 12px;">&#9664;</button>
                    <button id="step-forward" style="font-size: 12px;">&#9654;</button>
                    <button id="toggle-stepping" style="font-size: 12px;">Enable Stepping</button>
                `;
            }
        },
        
        createTooltip: function(container) {
            return d3.select(container)
                .append('div')
                .attr('class', 'timeline-tooltip');
        },
        
        updateDetailsSidebar: function(item, index) {
            const sidebar = document.getElementById('details-sidebar');
            sidebar.style.display = 'block';
            sidebar.innerHTML = `
                <h3>${item.type.toUpperCase()} (#${index})</h3>
                <pre>${JSON.stringify(item, null, 2)}</pre>
            `;
        },
        
        setupTagFilters: function(items) {
            const allTagPairs = Utils.extractTagPairs(items);
            const tagFiltersContainer = document.getElementById('tag-filters');
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
        },
        
        applyTagFilter: function(items) {
            const active = Array.from(document.querySelectorAll('.tag-filter.active'))
                .map(el => el.textContent);
            
            // Build the 'visible' list based on active tags
            const visibleData = items.filter(d => {
                if (!active.length) return true;
                if (!d.tags) return false;
                return active.every(pair => {
                    const [k, v] = pair.split('=');
                    return d.tags[k] === v;
                });
            });
            
            // Update display styling (hide non-visible items)
            d3.selectAll('.timeline-item')
                .style('display', d => visibleData.includes(d) ? '' : 'none');
        }
    };

    // Timeline rendering
    const TimelineRenderer = {
        createSVG: function(container, width, height) {
            return d3.select(container)
                .append('svg')
                .attr('width', width - 400)
                .attr('height', height);
        },
        
        renderTimestamps: function(svg, yScale, items, leftColumnWidth) {
            const timestampGroup = svg.append('g')
                .attr('class', 'timestamp-group');
            timestampGroup.selectAll('.timestamp')
                .data(items)
                .enter()
                .append('text')
                .attr('class', 'timestamp')
                .attr('x', leftColumnWidth - 6)
                .attr('y', (d, i) => yScale(i) + yScale.bandwidth() - 4)
                .attr('text-anchor', 'end')
                .style('font-size', '10px')
                .style('fill', COLORS.TEXT)
                .text(d => new Date(d.timestamp).toLocaleTimeString());
                
            return timestampGroup;
        },
        
        renderItemBlocks: function(svg, yScale, items, width, leftColumnWidth, tooltip) {
            const itemBlocksGroup = svg.append('g')
                .attr('class', 'item-block-group');
            
            const blocks = itemBlocksGroup.selectAll('.timeline-item')
                .data(items)
                .enter()
                .append('g')
                .attr('class', 'timeline-item')
                .attr('transform', (d, i) => {
                    if (d.type === 'prompt-completion') return `translate(${leftColumnWidth + 20}, ${yScale(i)})`;
                    return `translate(${leftColumnWidth}, ${yScale(i)})`;
                });
            
            blocks.append('rect')
                .attr('height', yScale.bandwidth())
                .attr('width', width - 500)
                .attr('fill', (d, i) => Utils.getItemColor(d, i, items, steppingEnabled, currentStepIndex));
            
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
        
        attachBlockEvents: function(blocks, items, tooltip) {
            blocks.on('mouseover', function(event, d) {
                if (!steppingEnabled || items.indexOf(d) <= currentStepIndex) {
                    if (queryFocusMode && !matchedIndices.includes(items.indexOf(d)) && 
                        !(d.type === 'query' && matchedIndices.length > 0)) {
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
            .on('mouseout', function(event, d) {
                const i = items.indexOf(d);
                d3.select(this).select('rect').attr('fill', Utils.getItemColor(d, i, items, steppingEnabled, currentStepIndex));
                tooltip.style('display', 'none');
            })
            .on('click', function(event, d) {
                const itemIndex = items.indexOf(d);
                UIComponents.updateDetailsSidebar(d, itemIndex);
                
                // Process query item highlighting
                if (d.type === 'query') {
                    // Handle clicking on the same query again (toggle off highlights)
                    if (selectedQueryIndex === itemIndex) {
                        Utils.clearQueryHighlights();
                    } else {
                        // Pass false to not enable focus mode (don't gray out non-matched items)
                        Utils.updateMatchedIndices(d, items, false);
                    }
                } else {
                    // Clear matched indices when clicking non-query items
                    Utils.clearQueryHighlights();
                }
                
                // Update display to reflect matched items
                TimelineRenderer.updateItemsDisplay(items);
            })
            .on('dblclick', function(event, d) {
                const sidebar = document.getElementById('details-sidebar');
                sidebar.style.display = 'none';
                
                // Clear matched indices on double-click
                Utils.clearQueryHighlights();
                TimelineRenderer.updateItemsDisplay(items);
            });
        },
        
        updateItemsDisplay: function(items) {
            d3.selectAll('.timeline-item')
                .select('rect')
                .attr('fill', (d, i) => Utils.getItemColor(d, i, items, steppingEnabled, currentStepIndex));
            
            // Show current step in sidebar
            if (steppingEnabled && currentStepIndex >= 0 && currentStepIndex < items.length) {
                UIComponents.updateDetailsSidebar(items[currentStepIndex], currentStepIndex);
            }
        }
    };
    
    // Event handlers
    const EventHandlers = {
        setupSteppingControls: function(items) {
            const btnPrev = document.getElementById('step-backward');
            if (btnPrev) {
                btnPrev.addEventListener('click', () => {
                    if (steppingEnabled && currentStepIndex > 0) {
                        currentStepIndex--;
                        
                        // Check if current step is a query
                        const currentItem = items[currentStepIndex];
                        if (currentItem.type === 'query') {
                            // In stepping mode, we might want to enable focus mode
                            Utils.updateMatchedIndices(currentItem, items, true);
                        } else {
                            Utils.clearQueryHighlights();
                        }
                        
                        TimelineRenderer.updateItemsDisplay(items);
                    }
                });
            }
            
            const btnNext = document.getElementById('step-forward');
            if (btnNext) {
                btnNext.addEventListener('click', () => {
                    if (steppingEnabled && currentStepIndex < items.length - 1) {
                        currentStepIndex++;
                        
                        // Check if current step is a query
                        const currentItem = items[currentStepIndex];
                        if (currentItem.type === 'query') {
                            // In stepping mode, we might want to enable focus mode
                            Utils.updateMatchedIndices(currentItem, items, true);
                        } else {
                            Utils.clearQueryHighlights();
                        }
                        
                        TimelineRenderer.updateItemsDisplay(items);
                    }
                });
            }
            
            const btnToggleStepping = document.getElementById('toggle-stepping');
            if (btnToggleStepping) {
                btnToggleStepping.addEventListener('click', () => {
                    steppingEnabled = !steppingEnabled;
                    btnToggleStepping.textContent = steppingEnabled ? 'Disable Stepping' : 'Enable Stepping';
                    currentStepIndex = steppingEnabled ? 0 : -1;
                    
                    // Clear highlights when toggling stepping
                    Utils.clearQueryHighlights();
                    
                    // If in stepping mode and first item is a query, highlight its matches
                    if (steppingEnabled && items.length > 0 && items[0].type === 'query') {
                        Utils.updateMatchedIndices(items[0], items, true);
                    }
                    
                    TimelineRenderer.updateItemsDisplay(items);
                });
            }
        }
    };
    
    // Main timeline view controller
    const TimelineView = {
        render: function(container) {
            const loadingDiv = document.getElementById('loading-indicator');
            loadingDiv.style.display = 'block';
            
            container.innerHTML = '';
            
            const timelineContainer = document.createElement('div');
            container.appendChild(timelineContainer);
            
            const items = Utils.processBufferItems(bufferData);
            
            if (!items.length) {
                timelineContainer.innerHTML = '<p>No buffer items to display.</p>';
                loadingDiv.style.display = 'none';
                return;
            }
            
            UIComponents.setupStatsSection(container, bufferData, items);
            const tooltip = UIComponents.createTooltip(container);
            
            const width = container.clientWidth;
            const itemHeight = 20;
            const height = items.length * itemHeight + 10;
            const leftColumnWidth = 70;
            
            const svg = TimelineRenderer.createSVG(timelineContainer, width, height);
            
            const yScale = d3.scaleBand()
                .domain(d3.range(items.length))
                .range([0, height])
                .padding(0.1);
            
            TimelineRenderer.renderTimestamps(svg, yScale, items, leftColumnWidth);
            TimelineRenderer.renderItemBlocks(svg, yScale, items, width, leftColumnWidth, tooltip);
            
            UIComponents.setupTagFilters(items);
            EventHandlers.setupSteppingControls(items);
            
            loadingDiv.style.display = 'none';
        }
    };
    
    return {
        init: function() {
            const timelineView = document.getElementById('timeline-view');
            TimelineView.render(timelineView);
        }
    };
})();

document.addEventListener('DOMContentLoaded', PlompViewer.init);