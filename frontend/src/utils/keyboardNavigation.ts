/**
 * Handles keyboard navigation for timeline items.
 * This allows users to navigate through items using up and down arrow keys.
 */

export function setupTimelineKeyboardNavigation(
  getItems: () => HTMLElement[],
  onSelectItem: (index: number) => void,
): () => void {
  // The keyboard event handler
  const handleKeyDown = (event: KeyboardEvent) => {
    // Only handle up and down arrow keys
    if (event.key !== "ArrowUp" && event.key !== "ArrowDown") {
      return;
    }

    // Get all timeline items
    const items = getItems();
    if (!items.length) return;

    // Find currently selected item
    const currentIndex = items.findIndex((item) =>
      item.classList.contains("selected"),
    );

    let newIndex;
    if (event.key === "ArrowUp") {
      // Move to previous item (or stay at first item)
      newIndex = currentIndex > 0 ? currentIndex - 1 : 0;
      // If no item is selected yet, select the last item
      if (currentIndex === -1) newIndex = items.length - 1;
    } else {
      // Move to next item (or stay at last item)
      newIndex =
        currentIndex < items.length - 1 ? currentIndex + 1 : items.length - 1;
      // If no item is selected yet, select the first item
      if (currentIndex === -1) newIndex = 0;
    }

    // If we're already at the first/last item, do nothing
    if (newIndex === currentIndex) return;

    // Prevent default scrolling behavior
    event.preventDefault();

    // Select the new item
    onSelectItem(newIndex);

    // Scroll the new item into view if needed
    items[newIndex].scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  };

  // Add event listener
  window.addEventListener("keydown", handleKeyDown);

  // Return cleanup function
  return () => {
    window.removeEventListener("keydown", handleKeyDown);
  };
}
