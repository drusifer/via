.DEFAULT_GOAL := help

# ── Bob Protocol Configuration ───────────────────────────────────────────────
# Detect if this file is being run directly as Makefile.bob
_IS_BOB_ENTRY := $(filter %Makefile.bob,$(firstword $(MAKEFILE_LIST)))

ifdef MKF_ACTIVE

# ── Re-invocation Layer ──────────────────────────────────────────────────────
# Included by mkf.py to run the actual target.

# Include the project's original targets.
# We try Makefile.prj (legacy) and Makefile (if we are running as Makefile.bob).
ifneq ($(firstword $(MAKEFILE_LIST)),Makefile)
-include Makefile
endif
-include Makefile.prj

# ── Bob Protocol Targets ─────────────────────────────────────────────────────

.PHONY: tldr test via_index install_bob update_bob pull_bob clean_bob diff_bob

tldr: ## Show TL;DR summaries from all project files (quick orientation for agents)
	@rg --no-heading "TL;DR:" --glob "*.md" -N | sed 's|^\./||' | sort

test: ## Run unit tests
	@python -m unittest discover -s tests

via_index: ## Build the via index required by the via MCP server
	@via index "$(CURDIR)"

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
	@if [ -f "$(TARGET)/Makefile" ]; then \
		if grep -q "MKF_ACTIVE" "$(TARGET)/Makefile"; then \
			cp Makefile "$(TARGET)/Makefile" && echo "  Updated: Makefile (bob-managed)"; \
		else \
			cp Makefile "$(TARGET)/Makefile.bob" && echo "  Installed: Makefile.bob"; \
			if ! grep -q "include Makefile.bob" "$(TARGET)/Makefile"; then \
				echo "include Makefile.bob" | cat - "$(TARGET)/Makefile" > "$(TARGET)/Makefile.tmp" && mv "$(TARGET)/Makefile.tmp" "$(TARGET)/Makefile"; \
				echo "  Modified: Makefile (included Makefile.bob at top)"; \
			fi; \
		fi; \
	else \
		cp Makefile "$(TARGET)/Makefile" && echo "  Installed: Makefile (bob-managed)"; \
	fi
	@echo "Setting up Claude skill links..."
	@python $(TARGET)/agents/tools/setup_agent_links.py
	@echo ""
	@echo "Done. BobProtocol installed in $(TARGET)"
	@echo "Run 'make tldr' inside $(TARGET) to verify."

update_bob: ## Update bob-protocol personas, skills, tools, and templates in a target project (usage: make update_bob TARGET=/path/to/project)
	@[ -n "$(TARGET)" ] || { echo "Usage: make update_bob TARGET=/path/to/project"; exit 1; }
	@[ -d "$(TARGET)" ] || { echo "Error: $(TARGET) does not exist"; exit 1; }
	@echo "Updating BobProtocol in $(TARGET)..."
	@rsync -a agents/skills/ $(TARGET)/agents/skills/
	@rsync -a agents/tools/  $(TARGET)/agents/tools/
	@rsync -a agents/templates/ $(TARGET)/agents/templates/
	@for f in agents/*.docs/SKILL.md; do \
		rsync -a "$$f" "$(TARGET)/$$f"; \
	done
	@echo "Ensuring agent state files are initialised..."
	@for dir in $(TARGET)/agents/*.docs; do \
		[ -f $$dir/context.md ]      || cp agents/templates/_template_context.md      $$dir/context.md; \
		[ -f $$dir/current_task.md ] || cp agents/templates/_template_current_task.md $$dir/current_task.md; \
		[ -f $$dir/next_steps.md ]   || cp agents/templates/_template_next_steps.md   $$dir/next_steps.md; \
	done
	@[ -f $(TARGET)/agents/CHAT.md ] || cp agents/templates/_template_CHAT.md $(TARGET)/agents/CHAT.md
	@echo "Updating Makefile in $(TARGET)..."
	@if [ -f "$(TARGET)/Makefile" ]; then \
		if grep -q "MKF_ACTIVE" "$(TARGET)/Makefile"; then \
			cp Makefile "$(TARGET)/Makefile" && echo "  Updated: Makefile (bob-managed)"; \
		else \
			cp Makefile "$(TARGET)/Makefile.bob" && echo "  Updated: Makefile.bob"; \
			if ! grep -q "include Makefile.bob" "$(TARGET)/Makefile"; then \
				echo "include Makefile.bob" | cat - "$(TARGET)/Makefile" > "$(TARGET)/Makefile.tmp" && mv "$(TARGET)/Makefile.tmp" "$(TARGET)/Makefile"; \
				echo "  Modified: Makefile (included Makefile.bob at top)"; \
			fi; \
		fi; \
	else \
		cp Makefile "$(TARGET)/Makefile" && echo "  Updated: Makefile (bob-managed)"; \
	fi
	@echo "Updating Claude skill links..."
	@python $(TARGET)/agents/tools/setup_agent_links.py
	@echo ""
	@echo "Done. BobProtocol updated in $(TARGET)"

pull_bob: ## Pull bob-protocol personas, skills, tools, and templates from another project (usage: make pull_bob SRC=/path/to/project)
	@[ -n "$(SRC)" ] || { echo "Usage: make pull_bob SRC=/path/to/project"; exit 1; }
	@[ -d "$(SRC)" ] || { echo "Error: $(SRC) does not exist"; exit 1; }
	@echo "Pulling BobProtocol updates from $(SRC)..."
	@rsync -a --existing $(SRC)/agents/skills/    agents/skills/
	@rsync -a --existing $(SRC)/agents/tools/     agents/tools/
	@rsync -a --existing $(SRC)/agents/templates/ agents/templates/
	@for f in agents/*.docs/SKILL.md; do \
		[ -f "$(SRC)/$$f" ] && rsync -a "$(SRC)/$$f" "$$f" || true; \
	done
	@echo ""
	@echo "Done. BobProtocol pulled from $(SRC)"

clean_bob: ## Remove generated symlinks and reset agent memory/state files
	@echo "Removing generated symlinks..."
	@python agents/tools/teardown_agent_links.py --keep-mcp
	@echo "Resetting agent state files to templates..."
	@for dir in agents/*.docs; do \
		cp agents/templates/_template_context.md    $$dir/context.md; \
		cp agents/templates/_template_current_task.md $$dir/current_task.md; \
		cp agents/templates/_template_next_steps.md $$dir/next_steps.md; \
	done
	@cp agents/templates/_template_CHAT.md agents/CHAT.md
	@echo "Done. Environment cleaned and state reset."

diff_bob: ## Compare bob-protocol personas, skills, tools, and templates with a target project (usage: make diff_bob TARGET=/path/to/project)
	@[ -n "$(TARGET)" ] || { echo "Usage: make diff_bob TARGET=/path/to/project"; exit 1; }
	@[ -d "$(TARGET)" ] || { echo "Error: $(TARGET) does not exist"; exit 1; }
	@echo "Diffing BobProtocol: $(CURDIR) vs $(TARGET)"
	@echo ""
	@for dir in agents/skills agents/tools agents/templates; do \
		if [ -d "$(TARGET)/$$dir" ]; then \
			diff -rq "$$dir" "$(TARGET)/$$dir"; \
		else \
			echo "Only in this project: $$dir/"; \
		fi; \
	done || true
	@for f in agents/*.docs/SKILL.md; do \
		tgt="$(TARGET)/$$f"; \
		if [ -f "$$tgt" ]; then \
			diff -q "$$f" "$$tgt" || true; \
		else \
			echo "Only in this project: $$f"; \
		fi; \
	done
	@echo ""
	@echo "Done."

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

.PHONY: help chat test via_index install_bob update_bob pull_bob clean_bob diff_bob

install_bob: ## Copy agents into a project and set up skill links (usage: make install_bob TARGET=/path/to/project)
	@$(MAKE) MKF_ACTIVE=1 install_bob TARGET="$(TARGET)"

update_bob: ## Update agents and skills in a project, preserving state (usage: make update_bob TARGET=/path/to/project)
	@$(MAKE) MKF_ACTIVE=1 update_bob TARGET="$(TARGET)"

pull_bob: ## Pull updates from another project using BobProtocol, preserving local state (usage: make pull_bob SRC=/path/to/project)
	@$(MAKE) MKF_ACTIVE=1 pull_bob SRC="$(SRC)"

clean_bob: ## Remove generated symlinks and reset agent memory/state files
	@$(MAKE) MKF_ACTIVE=1 clean_bob

diff_bob: ## Compare bob-protocol files with a target project, excluding state files (usage: make diff_bob TARGET=/path/to/project)
	@$(MAKE) MKF_ACTIVE=1 diff_bob TARGET="$(TARGET)"

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

test: ## Run unit tests
	@./agents/tools/mkf.py $(V) $@

via_index: ## Build the via index required by the via MCP server
	@./agents/tools/mkf.py $(V) $@

# Interception logic: 
# If we are the entry point (direct make call), intercept everything.
# If we are included, we only provide targets, unless specified.
ifeq ($(MKF_ACTIVE),)
ifdef _IS_BOB_ENTRY
%:
	@./agents/tools/mkf.py $(V) $@
endif
endif

endif
