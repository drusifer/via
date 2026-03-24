/**
 * Unit tests for pure utility functions in via/web/static/utils.js.
 * No DOM required — these run in Node without jsdom.
 */
import { describe, it, expect } from 'vitest';
import { esc, relTime, badgeClass } from '../../via/web/static/utils.js';

// ---------------------------------------------------------------------------
// esc
// ---------------------------------------------------------------------------
describe('esc', () => {
  it('escapes ampersand', () => expect(esc('a&b')).toBe('a&amp;b'));
  it('escapes less-than', () => expect(esc('<div>')).toBe('&lt;div&gt;'));
  it('escapes greater-than', () => expect(esc('x>y')).toBe('x&gt;y'));
  it('escapes all three in one string', () =>
    expect(esc('<b>a&b</b>')).toBe('&lt;b&gt;a&amp;b&lt;/b&gt;'));
  it('returns empty string for null', () => expect(esc(null)).toBe(''));
  it('returns empty string for undefined', () => expect(esc(undefined)).toBe(''));
  it('coerces numbers to string', () => expect(esc(42)).toBe('42'));
  it('passes plain text unchanged', () => expect(esc('hello world')).toBe('hello world'));
  it('does not double-escape', () => expect(esc('&amp;')).toBe('&amp;amp;'));
});

// ---------------------------------------------------------------------------
// badgeClass
// ---------------------------------------------------------------------------
describe('badgeClass', () => {
  it.each([
    ['function', 'badge-function'],
    ['class',    'badge-class'],
    ['method',   'badge-method'],
    ['import',   'badge-import'],
    ['global',   'badge-global'],
    ['filepath', 'badge-filepath'],
    ['filename', 'badge-filename'],
    ['header',   'badge-header'],
  ])('maps "%s" → "%s"', (type, expected) => {
    expect(badgeClass(type)).toBe(expected);
  });

  it('returns badge-global for unknown type', () =>
    expect(badgeClass('unknown')).toBe('badge-global'));
  it('returns badge-global for empty string', () =>
    expect(badgeClass('')).toBe('badge-global'));
  it('returns badge-global for undefined', () =>
    expect(badgeClass(undefined)).toBe('badge-global'));
});

// ---------------------------------------------------------------------------
// relTime
// ---------------------------------------------------------------------------
describe('relTime', () => {
  const ago = ms => new Date(Date.now() - ms).toISOString();

  it('returns "just now" for < 5 seconds', () =>
    expect(relTime(ago(3_000))).toBe('just now'));

  it('returns "Xs ago" for 5–59 seconds', () =>
    expect(relTime(ago(30_000))).toBe('30s ago'));

  it('boundary: exactly 5s is "5s ago" not "just now"', () =>
    expect(relTime(ago(5_000))).toBe('5s ago'));

  it('boundary: exactly 59s is "59s ago"', () =>
    expect(relTime(ago(59_000))).toBe('59s ago'));

  it('returns "Xm ago" for 60s–3599s', () =>
    expect(relTime(ago(120_000))).toBe('2m ago'));

  it('boundary: exactly 60s is "1m ago"', () =>
    expect(relTime(ago(60_000))).toBe('1m ago'));

  it('returns "Xh ago" for >= 3600s', () =>
    expect(relTime(ago(7_200_000))).toBe('2h ago'));

  it('boundary: exactly 1h is "1h ago"', () =>
    expect(relTime(ago(3_600_000))).toBe('1h ago'));
});
