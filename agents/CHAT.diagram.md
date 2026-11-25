# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `bobp chat-diagram` (or it regenerates automatically on every `bobp chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Morpheus
    participant Neo
    Note over User,Neo: 📅 2026-11-24
    User->>All: "request"
    Note right of User: "refine Cycle 2: identify<br/>tests that only touch<br/>mocks and nothing in the<br/>imported module"
    Morpheus->>Neo: "lead decide"
    Note right of Morpheus: "Morpheus+Neo refining<br/>Cycle 2 per user<br/>directive: adding import<br/>ed_module_covered_count<br/>(covered-by symbols in<br/>test's AST-imported<br/>project m…"
    Neo->>User: "swe done"
    Note right of Neo: "Cycle 2 refined (DRY<br/>single-pass AST): added<br/>DatabaseStore.get_test_c<br/>overed_file_counts() + i<br/>mported_module_covered_c<br/>ount + mocks_only flag…"
```
