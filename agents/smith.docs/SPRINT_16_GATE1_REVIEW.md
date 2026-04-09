# Sprint 16 — Smith Gate 1 Review

**Date**: 2026-04-08
**Reviewer**: Smith (HCI Expert)
**Stories reviewed**: `agents/cypher.docs/SPRINT_16_USER_STORIES.md`
**Verdict**: **APPROVED**

---

## Story-by-Story Review

### S16-1: `--slice` for OR'd multi-type queries — APPROVED

This is a straightforward correctness carry-over from Sprint 15. It is the right P0 opener because it protects the pagination mental model before additional workflow features build on top of it.

**HCI assessment:** Preserves trust in system status and result navigation.

### S16-2: `-ts` string constants — APPROVED

This is the highest-value Sprint 16 feature. It gives users a way to search for meaningful developer-facing strings without pretending via is a full-text search engine.

**Notes:**
- Keep scope explicit: this is structured string-symbol indexing, not arbitrary `--contains` source search.
- The value is strongest when string constants can bridge to their enclosing symbol or file through existing relationship queries.

**HCI assessment:** Strong match to real user tasks such as locating error strings, route literals, and log messages.

### S16-3: Coverage import as `covered-by` — APPROVED WITH NOTE

Very strong user value, but scope discipline matters.

**Note:**
- Prefer one documented interchange format for Sprint 16. `coverage.xml` is the safest initial target if it avoids coupling to coverage.py internals.

**HCI assessment:** Gives users a concrete and trustworthy way to ask "what is untested?" instead of inferring from call graphs alone.

### S16-4: Canned queries — APPROVED

This is the right time to add reusable query workflows because Sprint 15 and Sprint 16 make the query model richer. Naming and argument handling will matter more than implementation cleverness.

**Notes:**
- Built-ins should use user-language names, not internal jargon.
- Expansion must stay transparent so users can understand what query actually ran.

**HCI assessment:** Improves efficiency for expert users without complicating the base query model.

---

## Sprint-Level Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Story quality | ★★★★★ | Focused, traceable to Smith review and Sprint 15 closeout |
| Scope | ★★★★☆ | Tight enough if coverage import stays format-limited |
| User value | ★★★★★ | All four stories compound each other well |
| Risk | ★★★★☆ | `-ts` needs architectural discipline to avoid accidental full-text creep |

**Overall:** APPROVED. Proceed to Morpheus architecture.

## One Guidance Note For Morpheus

Keep Sprint 16 framed as **structured analysis primitives**, not "search everything." The moment `-ts` or canned queries start acting like a second search engine, the user mental model will blur.
