# Morpheus Next Steps

## Resume Point: Sprint 10 Post-Smith-Gate-2

### Immediate on Resume
1. Check CHAT.md for Smith's Gate 2 response
2. If approved: hand off to Neo for Cycle 1 (S10-1 `--ref-type`)
3. If rejected: address Smith's concerns in arch doc, resubmit

### Implementation Phase Order (for Neo handoff)
- Cycle 1: S10-1 (`--ref-type`) — `via/pipeline/parser.py` changes only
- Cycle 2: S10-2 (`--stale`) + S10-3 (`prep_tldr`) — parallel implementation
- Cycle 3: TD-WATCH-1 (`PathFilter`) — last, no dependencies

### Key Arch Invariants to Communicate to Neo
- `--ref-type` is detected PRE-parse in `_find_relationship_split()` — not via argparse
- `anchor_mtime` field on `MatchRecord` carries the anchor's mtime for `--stale` post-filter
- `prep_tldr` last-run file: `.via/prep_tldr_last_run`; use `time.time()` (NOT `os.time()`)
- `PathFilter.should_include_dir/file` are PUBLIC methods (no underscore prefix)
