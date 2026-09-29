#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["textual>=0.60.0"]
# ///
"""Interactive TUI installer for this dev-environment repo.

Run via ./bootstrap.sh (which guarantees brew + uv first), or directly with
`uv run install.py` once brew and uv already exist.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Header, Log, Tree
from textual.widgets.tree import TreeNode

CHECKED = "☑"
UNCHECKED = "☐"

REPO_ROOT = Path(__file__).resolve().parent
HOME = Path.home()
IS_MACOS = sys.platform == "darwin"

LogFn = Callable[[str], None]


def sh(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, text=True, capture_output=True)


def which(name: str) -> bool:
    return shutil.which(name) is not None


def run_cmds(*cmds: str) -> Callable[[LogFn], None]:
    def _run(log: LogFn) -> None:
        for c in cmds:
            log(f"$ {c}")
            r = sh(c)
            log(r.stdout or r.stderr or "(no output)")
    return _run


def brew_install(*formulae: str, cask: bool = False) -> Callable[[LogFn], None]:
    flag = "--cask " if cask else ""
    return run_cmds(*(f"brew install {flag}{f}" for f in formulae))


def symlink(src: Path, dest: Path) -> str:
    src = src.resolve()
    if dest.is_symlink() and dest.resolve() == src:
        return f"ok    {dest} already linked -> {src}"
    if dest.exists() or dest.is_symlink():
        backup = dest.with_name(dest.name + f".bak.{datetime.now():%Y%m%d%H%M%S}")
        dest.rename(backup)
        note = f" (backed up existing file to {backup.name})"
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        note = ""
    dest.symlink_to(src)
    return f"linked {dest} -> {src}{note}"


def link(rel_src: str, dest: str) -> Callable[[LogFn], None]:
    """rel_src is a repo-relative path; dest is a path under $HOME, e.g. '~/.vimrc'."""
    def _run(log: LogFn) -> None:
        log(symlink(REPO_ROOT / rel_src, Path(dest).expanduser()))
    return _run


def install_lazyvim(log: LogFn) -> None:
    nvim_cfg = HOME / ".config" / "nvim"
    if not nvim_cfg.exists():
        log(f"$ git clone https://github.com/LazyVim/starter {nvim_cfg}")
        r = sh(f"git clone https://github.com/LazyVim/starter '{nvim_cfg}'")
        log(r.stdout or r.stderr or "(no output)")
        shutil.rmtree(nvim_cfg / ".git", ignore_errors=True)
    else:
        log(f"ok    {nvim_cfg} already exists, skipping clone")

    plugins_dir = nvim_cfg / "lua" / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    src_dir = REPO_ROOT / "editor" / "nvim" / "plugins"
    for f in sorted(src_dir.glob("*.lua")):
        dest = plugins_dir / f.name
        shutil.copyfile(f, dest)
        log(f"copied {f.name} -> {dest}")

    init_lua = nvim_cfg / "init.lua"
    if init_lua.exists():
        contents = init_lua.read_text()
        if 'vim.o.background = "dark"' not in contents:
            init_lua.write_text(contents.rstrip("\n") + '\n\nvim.o.background = "dark"\n')
            log(f"appended background=dark to {init_lua}")
        else:
            log(f"ok    {init_lua} already sets background=dark")


def wanted_vscode_extensions() -> set[str]:
    ext_file = REPO_ROOT / "editor" / "vscode" / "extensions.txt"
    return {
        line.strip() for line in ext_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def vscode_extensions_installed() -> bool:
    if not which("code"):
        return False
    r = sh("code --list-extensions")
    if r.returncode != 0:
        return False
    installed = set(r.stdout.split())
    return wanted_vscode_extensions().issubset(installed)


def install_vscode_extensions(log: LogFn) -> None:
    if not which("code"):
        log("`code` CLI not found on PATH — open VS Code once and run "
            "'Shell Command: Install \"code\" command in PATH', then re-run this step.")
        return
    ext_file = REPO_ROOT / "editor" / "vscode" / "extensions.txt"
    for line in ext_file.read_text().splitlines():
        ext = line.strip()
        if not ext or ext.startswith("#"):
            continue
        log(f"$ code --install-extension {ext}")
        r = sh(f"code --install-extension {ext}")
        log(r.stdout or r.stderr or "(no output)")


def iterm2_theme_installed() -> bool:
    r = sh('defaults read com.googlecode.iterm2 "Custom Color Presets"')
    return r.returncode == 0 and "Dracula+" in r.stdout


def install_iterm2_theme(log: LogFn) -> None:
    theme = REPO_ROOT / "terminal" / "iterm2" / "Dracula+.itermcolors"
    log(f"$ open '{theme}'")
    log("iTerm2 will prompt to import the color preset into Preferences > Profiles > Colors.")
    sh(f"open '{theme}'")


ITERM2_DEFAULT_PROFILE_GUID = "DF822600-3266-4809-861F-8115F72308AF"


def iterm2_profile_installed() -> bool:
    dest = (HOME / "Library" / "Application Support" / "iTerm2" / "DynamicProfiles"
            / "CustomProfile.json")
    if not dest.is_symlink():
        return False
    r = sh('defaults read com.googlecode.iterm2 "New Bookmarks"')
    return r.returncode == 0 and ITERM2_DEFAULT_PROFILE_GUID in r.stdout


def install_iterm2_profile(log: LogFn) -> None:
    dest_dir = HOME / "Library" / "Application Support" / "iTerm2" / "DynamicProfiles"
    dest = dest_dir / "CustomProfile.json"
    log(symlink(REPO_ROOT / "terminal" / "iterm2" / "CustomProfile.json", dest))
    log(f"$ defaults write com.googlecode.iterm2 'Default Bookmark Guid' {ITERM2_DEFAULT_PROFILE_GUID}")
    r = sh(f"defaults write com.googlecode.iterm2 'Default Bookmark Guid' '{ITERM2_DEFAULT_PROFILE_GUID}'")
    log(r.stdout or r.stderr or "(no output)")
    log("Restart iTerm2 to pick up the profile (Dynamic Profiles are hot-reloaded, "
        "but the default-bookmark change needs a relaunch).")


def install_oh_my_zsh(log: LogFn) -> None:
    if (HOME / ".oh-my-zsh").exists():
        log("ok    ~/.oh-my-zsh already installed")
        return
    log("$ install oh-my-zsh (unattended, won't touch ~/.zshrc)")
    r = sh(
        "RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "
        '"$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"'
    )
    log(r.stdout or r.stderr or "(no output)")


OMZ_CUSTOM_PLUGINS = {
    "zsh-autosuggestions": "https://github.com/zsh-users/zsh-autosuggestions",
    "zsh-syntax-highlighting": "https://github.com/zsh-users/zsh-syntax-highlighting",
}


def install_ohmyzsh_plugins(log: LogFn) -> None:
    plugins_dir = HOME / ".oh-my-zsh" / "custom" / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    for name, url in OMZ_CUSTOM_PLUGINS.items():
        dest = plugins_dir / name
        if dest.exists():
            log(f"ok    {dest} already cloned")
            continue
        log(f"$ git clone {url} {dest}")
        r = sh(f"git clone '{url}' '{dest}'")
        log(r.stdout or r.stderr or "(no output)")


def ensure_node(log: LogFn) -> None:
    if not which("npm"):
        log("npm not found, installing node via brew first")
        r = sh("brew install node")
        log(r.stdout or r.stderr or "(no output)")


def install_claude_code(log: LogFn) -> None:
    ensure_node(log)
    log("$ npm install -g @anthropic-ai/claude-code")
    r = sh("npm install -g @anthropic-ai/claude-code")
    log(r.stdout or r.stderr or "(no output)")


def install_codex(log: LogFn) -> None:
    ensure_node(log)
    log("$ npm install -g @openai/codex")
    r = sh("npm install -g @openai/codex")
    log(r.stdout or r.stderr or "(no output)")


def install_copilot_cli(log: LogFn) -> None:
    if not which("gh"):
        log("gh CLI not found — select 'GitHub CLI (gh)' too, skipping for now")
        return
    log("$ gh extension install github/gh-copilot")
    r = sh("gh extension install github/gh-copilot")
    log(r.stdout or r.stderr or "(no output)")


@dataclass
class Tool:
    id: str
    label: str
    category: str
    check: Callable[[], bool]
    install: Callable[[LogFn], None]
    macos_only: bool = False
    preselect: bool = True


TOOLS: list[Tool] = [
    # Core (bootstrap.sh already guarantees brew + uv, so they aren't listed here)
    Tool("git", "git", "Core", lambda: which("git"), brew_install("git")),
    Tool("git-config", "  -> symlink gitconfig to ~/.gitconfig", "Core",
         lambda: (HOME / ".gitconfig").is_symlink(), link("git/gitconfig", "~/.gitconfig")),
    Tool("git-ignore-global", "  -> symlink global gitignore to ~/.config/git/ignore", "Core",
         lambda: (HOME / ".config" / "git" / "ignore").is_symlink(),
         link("git/gitignore_global", "~/.config/git/ignore")),
    Tool("gh", "GitHub CLI (gh)", "Core", lambda: which("gh"), brew_install("gh")),

    Tool("ruff", "ruff (Python linter/formatter)", "Languages",
         lambda: which("ruff"), run_cmds("uv tool install ruff")),
    Tool("go", "Go", "Languages", lambda: which("go"), brew_install("go"), preselect=False),
    Tool("rust", "Rust", "Languages", lambda: which("cargo"), brew_install("rust"), preselect=False),

    Tool("nerd-font", "JetBrains Mono Nerd Font", "Fonts",
         lambda: (HOME / "Library" / "Fonts" / "JetBrainsMonoNerdFont-Regular.ttf").exists(),
         run_cmds("brew tap homebrew/cask-fonts", "brew install --cask font-jetbrains-mono-nerd-font"),
         macos_only=True),

    Tool("neovim", "Neovim", "Terminal Editors", lambda: which("nvim"), brew_install("neovim")),
    Tool("lazyvim", "  -> LazyVim starter + extra colorschemes/plugins", "Terminal Editors",
         lambda: (HOME / ".config" / "nvim" / "lua" / "config" / "lazy.lua").exists(), install_lazyvim),
    Tool("vim", "vim", "Terminal Editors", lambda: which("vim"), brew_install("vim")),
    Tool("vimrc", "  -> vimrc", "Terminal Editors",
         lambda: (HOME / ".vimrc").is_symlink(), link("editor/vimrc", "~/.vimrc")),

    Tool("tmux", "tmux", "Terminal", lambda: which("tmux"), brew_install("tmux")),
    Tool("tmux-config", "  -> tmux.conf", "Terminal",
         lambda: (HOME / ".tmux.conf").is_symlink(), link("terminal/tmux.conf", "~/.tmux.conf")),
    Tool("iterm2", "iTerm2", "Terminal", lambda: Path("/Applications/iTerm.app").exists(),
         brew_install("iterm2", cask=True), macos_only=True),
    Tool("iterm2-theme", "  -> import color theme into iTerm2", "Terminal",
         iterm2_theme_installed, install_iterm2_theme, macos_only=True),
    Tool("iterm2-profile", "  -> profile (font, colors, triggers, keymap, status bar)", "Terminal",
         iterm2_profile_installed, install_iterm2_profile, macos_only=True),

    Tool("ohmyzsh", "Oh My Zsh", "Shell", lambda: (HOME / ".oh-my-zsh").exists(), install_oh_my_zsh),
    Tool("ohmyzsh-plugins", "  -> zsh-autosuggestions + zsh-syntax-highlighting plugins", "Shell",
         lambda: all((HOME / ".oh-my-zsh" / "custom" / "plugins" / n).exists()
                      for n in OMZ_CUSTOM_PLUGINS),
         install_ohmyzsh_plugins),
    Tool("zshrc", "  -> zshrc", "Shell",
         lambda: (HOME / ".zshrc").exists(), link("shell/zshrc", "~/.zshrc")),
    Tool("zsh_alias", "  -> zsh_alias", "Shell",
         lambda: (HOME / ".zsh_alias").exists(), link("shell/zsh_alias", "~/.zsh_alias")),
    Tool("bash", "bash", "Shell", lambda: which("bash"), brew_install("bash")),
    Tool("bashrc", "  -> bashrc", "Shell",
         lambda: (HOME / ".bashrc").exists(), link("shell/bashrc", "~/.bashrc")),

    Tool("claude-code", "Claude Code", "AI CLI tools", lambda: which("claude"), install_claude_code),
    Tool("claude-settings", "  -> Claude Code settings.json", "AI CLI tools",
         lambda: (HOME / ".claude" / "settings.json").is_symlink(),
         link("claude/settings.json", "~/.claude/settings.json")),
    Tool("claude-statusline", "  -> Claude Code statusline.sh", "AI CLI tools",
         lambda: (HOME / ".claude" / "statusline.sh").is_symlink(),
         link("claude/statusline.sh", "~/.claude/statusline.sh")),
    Tool("codex", "Codex CLI", "AI CLI tools", lambda: which("codex"), install_codex, preselect=False),
    Tool("copilot-cli", "GitHub Copilot CLI", "AI CLI tools",
         lambda: which("gh-copilot") or which("copilot"), install_copilot_cli, preselect=False),

    Tool("claude-desktop", "Claude Desktop", "AI tools",
         lambda: Path("/Applications/Claude.app").exists(),
         brew_install("claude", cask=True), macos_only=True, preselect=False),
    Tool("chatgpt", "ChatGPT", "AI tools",
         lambda: Path("/Applications/ChatGPT.app").exists(),
         brew_install("chatgpt", cask=True), macos_only=True, preselect=False),
    Tool("github-copilot", "GitHub Copilot (for Xcode)", "AI tools",
         lambda: Path("/Applications/GitHub Copilot for Xcode.app").exists(),
         brew_install("github-copilot-for-xcode", cask=True), macos_only=True, preselect=False),

    Tool("jq", "jq", "CLI utilities", lambda: which("jq"), brew_install("jq")),
    Tool("curl", "curl", "CLI utilities", lambda: which("curl"), brew_install("curl")),
    Tool("eza", "eza (ls replacement)", "CLI utilities", lambda: which("eza"), brew_install("eza")),
    Tool("bat", "bat (cat replacement)", "CLI utilities", lambda: which("bat"), brew_install("bat")),
    Tool("glow", "glow (markdown viewer)", "CLI utilities", lambda: which("glow"), brew_install("glow")),
    Tool("terraform", "terraform", "CLI utilities", lambda: which("terraform"), brew_install("terraform")),

    Tool("vscode", "Visual Studio Code", "IDEs",
         lambda: Path("/Applications/Visual Studio Code.app").exists(),
         brew_install("visual-studio-code", cask=True), macos_only=True),
    Tool("vscode-settings", "  -> settings.json (color theme + editor prefs)", "IDEs",
         lambda: (HOME / "Library" / "Application Support" / "Code" / "User" / "settings.json").is_symlink(),
         link("editor/vscode/settings.json",
              "~/Library/Application Support/Code/User/settings.json"),
         macos_only=True),
    Tool("vscode-extensions", "  -> install extensions (theme + plugins)", "IDEs",
         vscode_extensions_installed, install_vscode_extensions),
    Tool("cursor", "Cursor", "IDEs",
         lambda: Path("/Applications/Cursor.app").exists(),
         brew_install("cursor", cask=True), macos_only=True, preselect=False),
    Tool("pycharm", "PyCharm CE", "IDEs",
         lambda: Path("/Applications/PyCharm CE.app").exists(),
         brew_install("pycharm-ce", cask=True), macos_only=True, preselect=False),
    Tool("intellij", "IntelliJ IDEA CE", "IDEs",
         lambda: Path("/Applications/IntelliJ IDEA CE.app").exists(),
         brew_install("intellij-idea-ce", cask=True), macos_only=True, preselect=False),

    Tool("screen", "screen", "Terminal", lambda: which("screen"), brew_install("screen")),
    Tool("screenrc", "  -> screenrc", "Terminal",
         lambda: (HOME / ".screenrc").is_symlink(), link("terminal/screenrc", "~/.screenrc")),
]


class InstallerApp(App):
    CSS = """
    Screen { layout: vertical; }
    #body { height: 1fr; }
    Tree { width: 1fr; border: round $accent; }
    Log { width: 1fr; border: round $accent; }
    #actions { height: 3; }
    """
    BINDINGS = [("q", "quit", "Quit")]

    SUB_PREFIX = "  -> "

    def __init__(self) -> None:
        super().__init__()
        self.by_id: dict[str, Tool] = {}
        self.installed: dict[str, bool] = {}
        self.selected: set[str] = set()
        self.node_by_id: dict[str, TreeNode[str]] = {}
        for t in TOOLS:
            if t.macos_only and not IS_MACOS:
                continue
            self.by_id[t.id] = t
            self.installed[t.id] = t.check()
            if t.preselect and not self.installed[t.id]:
                self.selected.add(t.id)

    def _display_text(self, tid: str) -> str:
        text = self.by_id[tid].label
        if text.startswith(self.SUB_PREFIX):
            text = text[len(self.SUB_PREFIX):]
        return text

    def _label(self, tid: str) -> str:
        box = CHECKED if tid in self.selected else UNCHECKED
        suffix = "  (installed)" if self.installed[tid] else ""
        return f"{box} {self._display_text(tid)}{suffix}"

    def _group_children(self, ids: list[str]) -> list[tuple[str, list[str]]]:
        """Group a category's tool ids into (parent_id, [child_ids]) pairs.

        A tool whose label starts with SUB_PREFIX is a sub-item of the
        nearest preceding tool in the same category that isn't.
        """
        groups: list[tuple[str, list[str]]] = []
        for tid in ids:
            if groups and self.by_id[tid].label.startswith(self.SUB_PREFIX):
                groups[-1][1].append(tid)
            else:
                groups.append((tid, []))
        return groups

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            tree: Tree[str] = Tree("Tools", id="tools")
            tree.show_root = False
            tree.auto_expand = False
            categories: dict[str, list[str]] = {}
            for tid, t in self.by_id.items():
                categories.setdefault(t.category, []).append(tid)
            for category in sorted(categories, key=str.lower):
                ids = categories[category]
                cat_node = tree.root.add(category, expand=True)
                groups = self._group_children(ids)
                groups.sort(key=lambda g: self._display_text(g[0]).lower())
                for parent_id, child_ids in groups:
                    child_ids = sorted(child_ids, key=lambda cid: self._display_text(cid).lower())
                    if child_ids:
                        parent_node = cat_node.add(
                            self._label(parent_id), data=parent_id, expand=True
                        )
                        self.node_by_id[parent_id] = parent_node
                        for cid in child_ids:
                            leaf = parent_node.add_leaf(self._label(cid), data=cid)
                            self.node_by_id[cid] = leaf
                    else:
                        leaf = cat_node.add_leaf(self._label(parent_id), data=parent_id)
                        self.node_by_id[parent_id] = leaf
            yield tree
            yield Log(id="log")
        with Horizontal(id="actions"):
            yield Button("Select all", id="select-all")
            yield Button("Select none", id="select-none")
            yield Button("Install selected", id="install", variant="success")
            yield Button("Quit", id="quit", variant="error")
        yield Footer()

    def _set_selected(self, tid: str, value: bool) -> None:
        if value:
            self.selected.add(tid)
        else:
            self.selected.discard(tid)
        self.node_by_id[tid].set_label(self._label(tid))

    def _toggle(self, tid: str) -> None:
        self._set_selected(tid, tid not in self.selected)

    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        tid = event.node.data
        if tid is not None:
            self._toggle(tid)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select-all":
            for tid in self.by_id:
                self._set_selected(tid, True)
        elif event.button.id == "select-none":
            for tid in self.by_id:
                self._set_selected(tid, False)
        elif event.button.id == "quit":
            self.exit()
        elif event.button.id == "install":
            self.do_install(list(self.selected))

    @work(thread=True)
    def do_install(self, ids: list[str]) -> None:
        widget = self.query_one("#log", Log)

        def log(msg: str) -> None:
            for line in str(msg).splitlines() or [""]:
                self.call_from_thread(widget.write_line, line)

        if not ids:
            log("Nothing selected.")
            return

        for tid in ids:
            tool = self.by_id[tid]
            log("")
            log(f"=== {tool.label.strip()} ===")
            try:
                tool.install(log)
            except Exception as exc:  # keep the app alive on a single failed step
                log(f"ERROR: {exc}")
        log("")
        log("Done. Restart your shell (or `exec zsh`) to pick up new configs.")


if __name__ == "__main__":
    InstallerApp().run()
