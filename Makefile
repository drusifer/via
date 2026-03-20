.DEFAULT_GOAL := help

ifdef MKF_ACTIVE

# ── Project targets (invoked by mkf via re-invocation) ───────────────────────
# Included here so mkf can find them when it re-runs: make MKF_ACTIVE=1 <target>
-include Makefile.prj

# ── Real recipes (invoked by mkf, not directly by the user) ─────────────────

.PHONY: tldr install_bob update_bob pull_bob clean_bob

tldr: ## Show TL;DR summaries from all project files (quick orientation for agents)
	@rg --no-heading "TL;DR:" --glob "*.md" -N | sed 's|^\./||' | sort

install_bob: ## Copy agents into a project and set up skill links (usage: make install_bob TARGET=/path/to/project)
	@[ -n "$(TARGET)" ] || { echo "Usage: make install_bob TARGET=/path/to/project"; exit 1; }
	@[ -d "$(TARGET)" ] || { echo "Error: $(TARGET) does not exist"; exit 1; }
	@echo "Installing BobProtocol into $(TARGET)..."
	@rsync -a \
		--exclude='*.docs/context.md' \
		--exclude='*.docs/current_task.md' \
		--exclude='*.docs/next_steps.md' \
		--exclude='CHAT.md' \
		agents/ $(TARGET)/agents/
	@echo "Initialising agent state files..."
	@for dir in $(TARGET)/agents/*.docs; do \
		cp agents/templates/_template_context.md    $$dir/context.md; \
		cp agents/templates/_template_current_task.md $$dir/current_task.md; \
		cp agents/templates/_template_next_steps.md $$dir/next_steps.md; \
	done
	@cp agents/templates/_template_CHAT.md $(TARGET)/agents/CHAT.md
	@echo "Installing Makefile into $(TARGET)..."
	@if [ -f "$(TARGET)/Makefile" ] && ! grep -q "MKF_ACTIVE" "$(TARGET)/Makefile"; then \
		mv "$(TARGET)/Makefile" "$(TARGET)/Makefile.prj" && echo "  Renamed: Makefile -> Makefile.prj (project targets preserved)"; \
	fi
	@cp Makefile "$(TARGET)/Makefile" && echo "  Installed: Makefile (bob-managed, includes Makefile.prj)"
	@echo "Setting up Claude skill links..."
	@python $(TARGET)/agents/tools/setup_agent_links.py
	@echo ""
	@echo "Done. BobProtocol installed in $(TARGET)"
	@echo "Run 'make tldr' inside $(TARGET) to verify."

update_bob: ## Update agents and skills in a project, preserving state (usage: make update_bob TARGET=/path/to/project)
	@[ -n "$(TARGET)" ] || { echo "Usage: make update_bob TARGET=/path/to/project"; exit 1; }
	@[ -d "$(TARGET)" ] || { echo "Error: $(TARGET) does not exist"; exit 1; }
	@echo "Updating BobProtocol in $(TARGET)..."
	@rsync -a \
		--exclude='*.docs/context.md' \
		--exclude='*.docs/current_task.md' \
		--exclude='*.docs/next_steps.md' \
		--exclude='CHAT.md' \
		--exclude='chat_archive/' \
		agents/ $(TARGET)/agents/
	@echo "Ensuring new agent state files are initialised..."
	@for dir in $(TARGET)/agents/*.docs; do \
		[ -f $$dir/context.md ] || cp agents/templates/_template_context.md $$dir/context.md; \
		[ -f $$dir/current_task.md ] || cp agents/templates/_template_current_task.md $$dir/current_task.md; \
		[ -f $$dir/next_steps.md ] || cp agents/templates/_template_next_steps.md $$dir/next_steps.md; \
	done
	@[ -f $(TARGET)/agents/CHAT.md ] || cp agents/templates/_template_CHAT.md $(TARGET)/agents/CHAT.md
	@echo "Updating Makefile in $(TARGET)..."
	@if [ -f "$(TARGET)/Makefile" ] && ! grep -q "MKF_ACTIVE" "$(TARGET)/Makefile"; then \
		mv "$(TARGET)/Makefile" "$(TARGET)/Makefile.prj" && echo "  Renamed: Makefile -> Makefile.prj (project targets preserved)"; \
	fi
	@cp Makefile "$(TARGET)/Makefile" && echo "  Updated: Makefile"
	@echo "Updating Claude skill links..."
	@python $(TARGET)/agents/tools/setup_agent_links.py
	@echo ""
	@echo "Done. BobProtocol updated in $(TARGET)"

pull_bob: ## Pull updates from another project using BobProtocol, preserving local state (usage: make pull_bob SRC=/path/to/project)
	@[ -n "$(SRC)" ] || { echo "Usage: make pull_bob SRC=/path/to/project"; exit 1; }
	@[ -d "$(SRC)" ] || { echo "Error: $(SRC) does not exist"; exit 1; }
	@echo "Pulling BobProtocol updates from $(SRC)..."
	@rsync -a --existing \
		--exclude='*.docs/context.md' \
		--exclude='*.docs/current_task.md' \
		--exclude='*.docs/next_steps.md' \
		--exclude='CHAT.md' \
		--exclude='chat_archive/' \
		$(SRC)/agents/ agents/
	@echo ""
	@echo "Done. BobProtocol pulled from $(SRC)"

clean_bob: ## Remove generated symlinks and reset agent memory/state files
	@echo "Removing generated symlinks..."
	@rm -rf .claude/skills/
	@rm -f AGENTS.md GEMINI.md .cursorrules CHATGPT.md .github/copilot-instructions.md
	@echo "Resetting agent state files to templates..."
	@for dir in agents/*.docs; do \
		cp agents/templates/_template_context.md    $$dir/context.md; \
		cp agents/templates/_template_current_task.md $$dir/current_task.md; \
		cp agents/templates/_template_next_steps.md $$dir/next_steps.md; \
	done
	@cp agents/templates/_template_CHAT.md agents/CHAT.md
	@echo "Done. Environment cleaned and state reset."

else

# ── Interception layer ───────────────────────────────────────────────────────
# All targets except help, chat, install_bob, update_bob, pull_bob, and clean_bob route through mkf (agents/tools/mkf.py).
# mkf captures output to build/build.out, posts status to CHAT.md,
# and prints the last 10 lines on exit.
#
# Verbosity (set V=):
#   make tldr              silent  — exit code only, full log in build/build.out
#   make tldr V=-v         stderr to terminal
#   make tldr V=-vv        stderr + filtered failures to terminal
#   make tldr V=-vvv       stderr + full stdout to terminal

.PHONY: help chat install_bob update_bob pull_bob clean_bob

install_bob: ## Copy agents into a project and set up skill links (usage: make install_bob TARGET=/path/to/project)
	@$(MAKE) MKF_ACTIVE=1 install_bob TARGET="$(TARGET)"

update_bob: ## Update agents and skills in a project, preserving state (usage: make update_bob TARGET=/path/to/project)
	@$(MAKE) MKF_ACTIVE=1 update_bob TARGET="$(TARGET)"

pull_bob: ## Pull updates from another project using BobProtocol, preserving local state (usage: make pull_bob SRC=/path/to/project)
	@$(MAKE) MKF_ACTIVE=1 pull_bob SRC="$(SRC)"

clean_bob: ## Remove generated symlinks and reset agent memory/state files
	@$(MAKE) MKF_ACTIVE=1 clean_bob

help: ## Show available make targets
	@echo ""
	@echo "  Build output filter (mkf) is active. All targets route through agents/tools/mkf.py."
	@echo "  Full log: build/build.out   Status posted to: agents/CHAT.md"
	@echo ""
	@echo "  Verbosity: append V=-v | V=-vv | V=-vvv to any target"
	@echo "    (none)   silent — exit code only"
	@echo "    -v       stderr to terminal"
	@echo "    -vv      stderr + failures/errors to terminal"
	@echo "    -vvv     stderr + full stdout to terminal"
	@echo ""
	@echo "  Examples:"
	@echo "    make pull_bob          # silent, log → build/build.out"
	@echo "    make update_bob V=-vvv # full output"
	@echo ""
	@echo "  Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@if [ -f Makefile.prj ]; then \
		echo ""; \
		echo "  Project targets (Makefile.prj):"; \
		grep -E '^[a-zA-Z][a-zA-Z0-9_-]*:' Makefile.prj | \
		awk 'BEGIN {FS = ":.*?## "}; /##/ {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2} !/##/ {split($$0,a,":"); printf "    \033[36m%-22s\033[0m\n", a[1]}'; \
	fi
	@echo ""

chat: ## Post a message to CHAT.md (usage: make chat MSG="<msg>" [PERSONA="<name>"] [CMD="<cmd>"] [TO="<recipient>"])
	@[ -n "$(MSG)" ] || { echo "Usage: make chat MSG=\"<message>\" [PERSONA=\"<name>\"] [CMD=\"<cmd>\"] [TO=\"<recipient>\"]"; exit 1; }
	@python agents/tools/chat.py "$(MSG)" \
		$(if $(PERSONA),--persona "$(PERSONA)") \
		$(if $(CMD),--cmd "$(CMD)") \
		$(if $(TO),--to "$(TO)")

%:
	@./agents/tools/mkf.py $(V) $@

endif
