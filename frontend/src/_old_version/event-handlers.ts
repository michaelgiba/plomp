import { STATE } from './constants';
import { Utils } from './utils';
import { TimelineRenderer } from './timeline-renderer';
import { TimelineItem } from './models';

export const EventHandlers = {
    setupSteppingControls: function(items: TimelineItem[]): void {
        const btnPrev = document.getElementById('step-backward');
        if (btnPrev) {
            btnPrev.addEventListener('click', () => {
                if (STATE.steppingEnabled && STATE.currentStepIndex > 0) {
                    STATE.currentStepIndex--;

                    // Check if current step is a query
                    const currentItem = items[STATE.currentStepIndex];
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
                if (STATE.steppingEnabled && STATE.currentStepIndex < items.length - 1) {
                    STATE.currentStepIndex++;

                    // Check if current step is a query
                    const currentItem = items[STATE.currentStepIndex];
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
                STATE.steppingEnabled = !STATE.steppingEnabled;
                btnToggleStepping.textContent = STATE.steppingEnabled ? 'Disable Stepping' : 'Enable Stepping';
                STATE.currentStepIndex = STATE.steppingEnabled ? 0 : -1;

                // Clear highlights when toggling stepping
                Utils.clearQueryHighlights();

                // If in stepping mode and first item is a query, highlight its matches
                if (STATE.steppingEnabled && items.length > 0 && items[0].type === 'query') {
                    Utils.updateMatchedIndices(items[0], items, true);
                }

                TimelineRenderer.updateItemsDisplay(items);
            });
        }
    }
};
