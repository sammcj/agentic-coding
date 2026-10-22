"""Which coding agents have OpenSpec skills or commands installed in the project.

Detection is by what is on disk, so it needs no knowledge of which OpenSpec version wrote the
files: any `openspec-*` skill directory or `opsx` command file under a known agent root counts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .scan import walk_files

# Project-level config roots, from OpenSpec's tool adapters. `.agents` is shared by several tools.
AGENT_ROOTS: dict[str, list[str]] = {
    ".agents": ["Shared .agents (Amp, Antigravity, Codex, GSD, Zed)"],
    ".amazonq": ["Amazon Q Developer"],
    ".atomcode": ["AtomCode"],
    ".augment": ["Auggie"],
    ".bob": ["IBM Bob"],
    ".claude": ["Claude Code"],
    ".cline": ["Cline"],
    ".clinerules": ["Cline"],
    ".codeartsdoer": ["CodeArts"],
    ".codeassistant": ["SourceCraft Code Assistant"],
    ".codebuddy": ["CodeBuddy Code"],
    ".codestudio": ["Code Studio"],
    ".codex": ["Codex"],
    ".commandcode": ["Command Code"],
    ".continue": ["Continue"],
    ".cospec": ["CoStrict"],
    ".crush": ["Crush"],
    ".cursor": ["Cursor"],
    ".devin": ["Devin Desktop"],
    ".dsh": ["DeepSeek Harness"],
    ".easycode": ["EasyCode"],
    ".factory": ["Factory Droid"],
    ".forge": ["ForgeCode"],
    ".gemini": ["Gemini CLI"],
    ".gigacode": ["GigaCode"],
    ".github": ["GitHub Copilot"],
    ".grok": ["Grok Build"],
    ".hermes": ["Hermes Agent"],
    ".iflow": ["iFlow"],
    ".junie": ["Junie"],
    ".kilo": ["Kilo Code"],
    ".kilocode": ["Kilo Code (legacy path)"],
    ".kimi-code": ["Kimi Code"],
    ".kiro": ["Kiro"],
    ".lingma": ["Lingma"],
    ".omp": ["Oh My Pi"],
    ".opencode": ["OpenCode"],
    ".pi": ["Pi"],
    ".qoder": ["Qoder"],
    ".qwen": ["Qwen Code"],
    ".roo": ["Zoo Code"],
    ".rovodev": ["Rovo Dev CLI"],
    ".trae": ["Trae"],
    ".veai": ["Veai"],
    ".vibe": ["Mistral Vibe"],
    ".warp": ["Warp"],
    ".windsurf": ["Windsurf"],
    ".zcode": ["ZCode"],
}


# Where agents look for project instructions that sit beside OpenSpec's own. Files in an
# ad hoc place (a build directory, a scratch note) are invisible to agents too, so are not sought.
INSTRUCTION_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "CLAUDE.local.md",
    ".claude/CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
]
INSTRUCTION_DIRS = [".claude/rules", ".claude/agents", ".cursor/rules", ".github/instructions"]
_MAX_INSTRUCTION_BYTES = 256 * 1024


@dataclass
class InstructionFile:
    path: str
    bytes: int
    content: str


def instruction_files(repo: Path) -> list[InstructionFile]:
    # As in walk_files, a symlink counts only if it resolves inside the repo. AGENTS.md -> CLAUDE.md
    # is common; a link out of the repo would let the server read arbitrary files.
    real = repo.resolve()
    candidates = (repo / name for name in INSTRUCTION_FILES)
    paths = [p for p in candidates if p.is_file() and p.resolve().is_relative_to(real)]
    for d in INSTRUCTION_DIRS:
        if (repo / d).is_dir():
            paths += sorted(f for f in walk_files(repo / d) if f.suffix in (".md", ".mdc"))
    found = []
    for p in paths:
        try:
            size = p.stat().st_size
            text = p.read_text(encoding="utf-8") if size <= _MAX_INSTRUCTION_BYTES else ""
        except (OSError, UnicodeDecodeError):
            continue
        found.append(InstructionFile(p.relative_to(repo).as_posix(), size, text))
    return found


@dataclass
class AgentSetup:
    root: str
    tools: list[str]
    skills: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)


def detect_agents(repo: Path) -> list[AgentSetup]:
    found: list[AgentSetup] = []
    for root_name, tools in AGENT_ROOTS.items():
        root = repo / root_name
        if not root.is_dir():
            continue
        setup = AgentSetup(root=root_name, tools=tools)
        # Claude Code keeps whole repo checkouts under .claude/worktrees.
        for f in walk_files(root, skip_top=("worktrees",)):
            rel = f.relative_to(root)
            parts = rel.parts
            if f.name == "SKILL.md" and len(parts) >= 3 and parts[-3] == "skills":
                if parts[-2].startswith(("openspec-", "opsx-")):
                    setup.skills.append(parts[-2])
            elif any(p.startswith("opsx") for p in parts) and "skills" not in parts:
                setup.commands.append(rel.as_posix())
        if setup.skills or setup.commands:
            setup.skills.sort()
            setup.commands.sort()
            found.append(setup)
    return found
