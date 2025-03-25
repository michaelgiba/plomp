const PlompViewer = (function() {
    const bufferData = __PLOMP_BUFFER_JSON__;
    let steppingEnabled = false;
    let currentStepIndex = 0;
    
    // Utility functions
    const Utils = {
        getItemColor: function(d, index, items, steppingEnabled, currentStepIndex) {
            if (steppingEnabled) {
                if (index === currentStepIndex) {
                    return '#ff9500'; // Highlighted color for current step
                } else if (index < currentStepIndex) {
                    // Normal colors for executed items
                    if (d.type === 'prompt-request') {
                        const completed = items.some(it => it.type === 'prompt-completion' && it.id === d.id);
                        return completed ? '#6baed6' : '#f5a8a8';
                    }
                    if (d.type === 'prompt-completion') return '#3182bd';
                    if (d.type === 'event') return '#74c476';
                    return '#9e9ac8';
                } else {
                    return '#e0e0e0'; // Light gray for future items
                }
            } else {
                // Normal colors when stepping is disabled
                if (d.type === 'prompt-request') {
                    const completed = items.some(it => it.type === 'prompt-completion' && it.id === d.id);
                    return completed ? '#6baed6' : '#f5a8a8';
                }
                if (d.type === 'prompt-completion') return '#3182bd';
                if (d.type === 'event') return '#74c476';
                return '#9e9ac8';
            }
        },
        
        processBufferItems: function(bufferData) {
            if (!bufferData || !Array.isArray(bufferData.buffer_items)) {
                return [];
            }
            
            // Transform bufferData items so that each 'prompt' item generates two entries
            const expandedItems = [];
            bufferData.buffer_items.forEach((originalItem) => {
                if (originalItem.type === 'prompt') {
                    // Prompt request version
                    expandedItems.push({
                        ...originalItem,
                        type: 'prompt-request'
                    });
                    // Optional prompt completion
                    if (originalItem.data?.completion?.completion_timestamp) {
                        expandedItems.push({
                            ...originalItem,
                            type: 'prompt-completion',
                            timestamp: originalItem.data.completion.completion_timestamp
                        });
                    }
                } else {
                    expandedItems.push(originalItem);
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
                .style('fill', '#666')
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
                    if (d.type === 'prompt-request') d3.select(this).select('rect').attr('fill', '#3182bd');
                    else if (d.type === 'prompt-completion') d3.select(this).select('rect').attr('fill', '#6baed6');
                    else if (d.type === 'event') d3.select(this).select('rect').attr('fill', '#31a354');
                    else d3.select(this).select('rect').attr('fill', '#6a51a3');
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
                UIComponents.updateDetailsSidebar(d, items.indexOf(d));
            })
            .on('dblclick', function(event, d) {
                const sidebar = document.getElementById('details-sidebar');
                sidebar.style.display = 'none';
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
                        TimelineRenderer.updateItemsDisplay(items);
                    }
                });
            }
            
            const btnNext = document.getElementById('step-forward');
            if (btnNext) {
                btnNext.addEventListener('click', () => {
                    if (steppingEnabled && currentStepIndex < items.length - 1) {
                        currentStepIndex++;
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