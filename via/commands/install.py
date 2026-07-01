"""
Install/uninstall/status commands for VIA integrations.

TLDR:
    InstallTarget ABC defines install(), uninstall(), status() interface.
    McpInstallTarget reads/writes .mcp.json (project) or ~/.claude.json (global)
    to register `via mcp serve` as an MCP server named "via".
    INSTALL_TARGETS registry maps target names to classes.
    Used by `via install mcp`, `via uninstall mcp`, `via status mcp`.

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

import argparse
import json
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .base import CommandHandlerABC
from via.core.constants import EXIT_ERROR, EXIT_SUCCESS


class InstallTarget(ABC):
    """Abstract base for installable targets."""

    @abstractmethod
    def install(self, global_install: bool = False) -> int: ...

    @abstractmethod
    def uninstall(self, global_install: bool = False) -> int: ...

    @abstractmethod
    def status(self) -> int: ...


class McpInstallTarget(InstallTarget):
    """Writes/reads .mcp.json (project) or ~/.claude.json (global)."""

    SERVER_NAME = "via"

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root).resolve() if project_root else Path.cwd().resolve()

    def _project_mcp_json(self) -> Path:
        return self.project_root / ".mcp.json"

    def _global_mcp_json(self) -> Path:
        return Path.home() / ".claude.json"

    def _via_entry(self) -> dict:
        return {
            "command": sys.executable,
            "args": ["-m", "via", "mcp", "serve", str(self.project_root)],
        }

    def _read_mcp_json(self, path: Path) -> dict:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _write_mcp_json(self, path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, indent=2) + "\n")

    def install(self, global_install: bool = False) -> int:
        path = self._global_mcp_json() if global_install else self._project_mcp_json()
        data = self._read_mcp_json(path)
        data.setdefault("mcpServers", {})[self.SERVER_NAME] = self._via_entry()
        self._write_mcp_json(path, data)
        print(f"Installed: {self.SERVER_NAME} → {path}")
        return EXIT_SUCCESS

    def uninstall(self, global_install: bool = False) -> int:
        path = self._global_mcp_json() if global_install else self._project_mcp_json()
        data = self._read_mcp_json(path)
        servers = data.get("mcpServers", {})
        if self.SERVER_NAME in servers:
            del servers[self.SERVER_NAME]
            if servers:
                self._write_mcp_json(path, data)
            elif path.exists():
                path.unlink()
            print(f"Uninstalled: {self.SERVER_NAME} from {path}")
        else:
            print(f"{self.SERVER_NAME} not found in {path}")
        return EXIT_SUCCESS

    def status(self) -> int:
        project_path = self._project_mcp_json()
        global_path = self._global_mcp_json()

        project_data = self._read_mcp_json(project_path)
        global_data = self._read_mcp_json(global_path)

        project_installed = self.SERVER_NAME in project_data.get("mcpServers", {})
        global_installed = self.SERVER_NAME in global_data.get("mcpServers", {})

        print(f"via MCP status:")
        print(f"  Project ({project_path}): {'installed' if project_installed else 'not installed'}")
        print(f"  Global  ({global_path}):  {'installed' if global_installed else 'not installed'}")

        return EXIT_SUCCESS if (project_installed or global_installed) else EXIT_ERROR


INSTALL_TARGETS: dict[str, type[InstallTarget]] = {
    'mcp': McpInstallTarget,
}


class InstallCommandHandler(CommandHandlerABC):
    """Handler for install/uninstall/status integrations."""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        pass

    @classmethod
    def get_help(cls) -> str:
        return "Install, uninstall or check status of VIA integrations"

    def run(self, args: argparse.Namespace) -> int:
        target_cls = INSTALL_TARGETS.get(args.target)
        if not target_cls:
            print(f"Error: Unsupported installation target: {args.target}", file=sys.stderr)
            return EXIT_ERROR

        target = target_cls()
        global_install = getattr(args, "global_install", False)

        if args.command == "install":
            return target.install(global_install=global_install)
        elif args.command == "uninstall":
            return target.uninstall(global_install=global_install)
        elif args.command == "status":
            return target.status()
        else:
            print(f"Error: Unknown command: {args.command}", file=sys.stderr)
            return EXIT_ERROR

