/**
 * Pure utility functions for the via Web UI.
 *
 * TLDR:
 *   No DOM dependencies — safe to import in any environment including
 *   Node.js test runners. Exported for unit testing.
 *
 * Author: Drew Gutstein
 * License: GPL-3.0
 */

/**
 * Escape HTML special characters to prevent XSS in innerHTML assignments.
 * @param {*} s - Value to escape (any type; coerced to string).
 * @returns {string}
 */
export function esc(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * Format an ISO timestamp as a human-readable relative time string.
 * @param {string} iso - ISO 8601 datetime string.
 * @returns {string} e.g. "just now", "30s ago", "2m ago", "3h ago"
 */
export function relTime(iso) {
  const diff = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 5)    return 'just now';
  if (diff < 60)   return diff + 's ago';
  if (diff < 3600) return Math.round(diff / 60) + 'm ago';
  return Math.round(diff / 3600) + 'h ago';
}

/**
 * Map a via symbol type to its CSS badge class.
 * @param {string} type - Symbol type from the via API.
 * @returns {string} CSS class name.
 */
export function badgeClass(type) {
  const map = {
    function: 'badge-function',
    class:    'badge-class',
    method:   'badge-method',
    import:   'badge-import',
    global:   'badge-global',
    filepath: 'badge-filepath',
    filename: 'badge-filename',
    header:   'badge-header',
  };
  return map[type] || 'badge-global';
}
