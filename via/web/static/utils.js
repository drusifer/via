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

// Diverging colorblind-safe scale for the coverage-intensity heatmap.
// Blue/orange (not red/green) per Smith's Sprint 27 Phase 2 gate note —
// red-green is unreadable for ~8% of men with red-green colorblindness.
const _INTENSITY_BLUE = [21, 101, 192];
const _INTENSITY_NEUTRAL = [240, 240, 240];
const _INTENSITY_ORANGE = [230, 81, 0];
const _INTENSITY_CLIP_PCT = 300;

function _lerpChannel(a, b, t) {
  return Math.round(a + (b - a) * t);
}

function _mixColor(c1, c2, t) {
  return `rgb(${_lerpChannel(c1[0], c2[0], t)}, ${_lerpChannel(c1[1], c2[1], t)}, ${_lerpChannel(c1[2], c2[2], t)})`;
}

/**
 * Map a coverage-intensity percentage to a colorblind-safe diverging color.
 * 0% = deep blue (gap), 100% = neutral (one covering test, adequate
 * baseline), >=300% = deep orange (duplication hotspot). Values above 300%
 * are clipped to the same color as 300% — callers must show the exact
 * numeric percentage alongside the color regardless of clipping.
 * @param {number} pct - intensity_pct (covering_test_count * 100).
 * @returns {string} CSS rgb(...) color string.
 */
export function intensityColor(pct) {
  const clamped = Math.max(0, Math.min(_INTENSITY_CLIP_PCT, pct));
  if (clamped <= 100) {
    return _mixColor(_INTENSITY_BLUE, _INTENSITY_NEUTRAL, clamped / 100);
  }
  return _mixColor(_INTENSITY_NEUTRAL, _INTENSITY_ORANGE, (clamped - 100) / (_INTENSITY_CLIP_PCT - 100));
}
