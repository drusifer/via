# Bob Context

## Latest Research (2026-02-01)

### Industry Standards for Agent Architecture

**The Big 3 (AAIF - Linux Foundation):**
1. **MCP** - Model Context Protocol (Anthropic) - Universal tool connectivity
2. **AGENTS.md** - Project-specific agent instructions (OpenAI)
3. **Skills** - Modular capability packaging (Claude)

### Key Findings

- MCP adopted by OpenAI (March 2025), now industry standard
- AGENTS.md adopted by 60,000+ repos for agent discovery
- Skills use YAML frontmatter: `name`, `description`, `allowed-tools`
- Progressive disclosure: load content on-demand, not upfront
- Multi-agent patterns: Manager (orchestrator) vs Handoffs (peer delegation)

### Bob Protocol Alignment

**Already Aligned:**
- MCP tools integration
- CHAT.md handoff protocol
- State file progressive loading

**Gaps to Address:**
- No AGENTS.md at repo root for external agent discovery
- Persona files lack standard YAML frontmatter
- Could convert to official `.claude/skills/` structure

### Sources

- [Claude Agent Skills Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [AGENTS.md Spec](https://agents.md/)
- [MCP Official](https://modelcontextprotocol.io/)
