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
from textual.widgets import Button, Footer, Header, Log, SelectionList
from textual.widgets.selection_list import Selection

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


def install_iterm2_theme(log: LogFn) -> None:
    theme = REPO_ROOT / "terminal" / "iterm2" / "DevEnvironment.itermcolors"
    log(f"$ open '{theme}'")
    log("iTerm2 will prompt to import the color preset into Preferences > Profiles > Colors.")
    sh(f"open '{theme}'")


ITERM2_DEFAULT_PROFILE_GUID = "DF822600-3266-4809-861F-8115F72308AF"


def install_iterm2_profile(log: LogFn) -> None:
    dest_dir = HOME / "Library" / "Application Support" / "iTerm2" / "DynamicProfiles"
    dest = dest_dir / "DevEnvironment.json"
    log(symlink(REPO_ROOT / "terminal" / "iterm2" / "DynamicProfiles.json", dest))
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


TOOLS: list[Tool] = [
    # Core (bootstrap.sh already guarantees brew + uv; listed for visibility/re-run)
    Tool("brew", "Homebrew", "Core", lambda: which("brew"), run_cmds(
        '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    )),
    Tool("uv", "uv (Python package/tool manager)", "Core", lambda: which("uv"), brew_install("uv")),
    Tool("git", "git", "Core", lambda: which("git"), brew_install("git")),
    Tool("git-config", "  -> symlink gitconfig to ~/.gitconfig", "Core",
         lambda: (HOME / ".gitconfig").is_symlink(), link("git/gitconfig", "~/.gitconfig")),
    Tool("git-ignore-global", "  -> symlink global gitignore to ~/.config/git/ignore", "Core",
         lambda: (HOME / ".config" / "git" / "ignore").is_symlink(),
         link("git/gitignore_global", "~/.config/git/ignore")),
    Tool("gh", "GitHub CLI (gh)", "Core", lambda: which("gh"), brew_install("gh")),

    Tool("ruff", "ruff (Python linter/formatter)", "Languages",
         lambda: which("ruff"), run_cmds("uv tool install ruff")),

    Tool("nerd-font", "JetBrains Mono Nerd Font", "Fonts",
         lambda: (HOME / "Library" / "Fonts" / "JetBrainsMonoNerdFont-Regular.ttf").exists(),
         run_cmds("brew tap homebrew/cask-fonts", "brew install --cask font-jetbrains-mono-nerd-font"),
         macos_only=True),

    Tool("neovim", "Neovim", "Editor", lambda: which("nvim"), brew_install("neovim")),
    Tool("lazyvim", "  -> LazyVim starter + extra colorschemes/plugins", "Editor",
         lambda: (HOME / ".config" / "nvim" / "lua" / "config" / "lazy.lua").exists(), install_lazyvim),

    Tool("tmux", "tmux", "Terminal", lambda: which("tmux"), brew_install("tmux")),
    Tool("tmux-config", "  -> tmux.conf", "Terminal",
         lambda: (HOME / ".tmux.conf").is_symlink(), link("terminal/tmux.conf", "~/.tmux.conf")),
    Tool("iterm2", "iTerm2", "Terminal", lambda: Path("/Applications/iTerm.app").exists(),
         brew_install("iterm2", cask=True), macos_only=True),
    Tool("iterm2-theme", "  -> import color theme into iTerm2", "Terminal",
         lambda: False, install_iterm2_theme, macos_only=True),
    Tool("iterm2-profile", "  -> profile (font, colors, triggers, keymap, status bar)", "Terminal",
         lambda: (HOME / "Library" / "Application Support" / "iTerm2" / "DynamicProfiles"
                  / "DevEnvironment.json").is_symlink(),
         install_iterm2_profile, macos_only=True),

    Tool("ohmyzsh", "Oh My Zsh", "Shell", lambda: (HOME / ".oh-my-zsh").exists(), install_oh_my_zsh),
    Tool("ohmyzsh-plugins", "  -> zsh-autosuggestions + zsh-syntax-highlighting plugins", "Shell",
         lambda: all((HOME / ".oh-my-zsh" / "custom" / "plugins" / n).exists()
                      for n in OMZ_CUSTOM_PLUGINS),
         install_ohmyzsh_plugins),
    Tool("zshrc", "  -> zshrc", "Shell",
         lambda: (HOME / ".zshrc").exists(), link("shell/zshrc", "~/.zshrc")),
    Tool("zsh_alias", "  -> zsh_alias", "Shell",
         lambda: (HOME / ".zsh_alias").exists(), link("shell/zsh_alias", "~/.zsh_alias")),
    Tool("bashrc", "  -> bashrc", "Shell",
         lambda: (HOME / ".bashrc").exists(), link("shell/bashrc", "~/.bashrc")),

    Tool("claude-code", "Claude Code", "AI CLIs", lambda: which("claude"), install_claude_code),
    Tool("codex", "Codex CLI", "AI CLIs", lambda: which("codex"), install_codex),
    Tool("copilot-cli", "GitHub Copilot CLI", "AI CLIs",
         lambda: which("gh-copilot") or which("copilot"), install_copilot_cli),
    Tool("claude-settings", "  -> Claude Code settings.json", "AI CLIs",
         lambda: (HOME / ".claude" / "settings.json").is_symlink(),
         link("claude/settings.json", "~/.claude/settings.json")),
    Tool("claude-statusline", "  -> Claude Code statusline.sh", "AI CLIs",
         lambda: (HOME / ".claude" / "statusline.sh").is_symlink(),
         link("claude/statusline.sh", "~/.claude/statusline.sh")),

    Tool("jq", "jq", "CLI utilities", lambda: which("jq"), brew_install("jq")),
    Tool("curl", "curl", "CLI utilities", lambda: which("curl"), brew_install("curl")),
    Tool("eza", "eza (ls replacement)", "CLI utilities", lambda: which("eza"), brew_install("eza")),
    Tool("bat", "bat (cat replacement)", "CLI utilities", lambda: which("bat"), brew_install("bat")),
    Tool("glow", "glow (markdown viewer)", "CLI utilities", lambda: which("glow"), brew_install("glow")),

    Tool("vimrc", "  -> vimrc", "Editor",
         lambda: (HOME / ".vimrc").is_symlink(), link("editor/vimrc", "~/.vimrc")),
    Tool("vscode", "Visual Studio Code", "Editor",
         lambda: Path("/Applications/Visual Studio Code.app").exists(),
         brew_install("visual-studio-code", cask=True), macos_only=True),
    Tool("vscode-settings", "  -> settings.json (color theme + editor prefs)", "Editor",
         lambda: (HOME / "Library" / "Application Support" / "Code" / "User" / "settings.json").is_symlink(),
         link("editor/vscode/settings.json",
              "~/Library/Application Support/Code/User/settings.json"),
         macos_only=True),
    Tool("vscode-extensions", "  -> install extensions (theme + plugins)", "Editor",
         lambda: False, install_vscode_extensions),
    Tool("screenrc", "  -> screenrc", "Terminal",
         lambda: (HOME / ".screenrc").is_symlink(), link("terminal/screenrc", "~/.screenrc")),
]


class InstallerApp(App):
    CSS = """
    Screen { layout: vertical; }
    #body { height: 1fr; }
    SelectionList { width: 1fr; border: round $accent; }
    Log { width: 1fr; border: round $accent; }
    #actions { height: 3; }
    """
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        selections = []
        for t in TOOLS:
            if t.macos_only and not IS_MACOS:
                continue
            installed = t.check()
            suffix = "  (installed)" if installed else ""
            selections.append(Selection(f"{t.label}{suffix}", t.id, not installed))
        with Horizontal(id="body"):
            yield SelectionList[str](*selections, id="tools")
            yield Log(id="log")
        with Horizontal(id="actions"):
            yield Button("Select all", id="select-all")
            yield Button("Select none", id="select-none")
            yield Button("Install selected", id="install", variant="success")
            yield Button("Quit", id="quit", variant="error")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        sl = self.query_one("#tools", SelectionList)
        if event.button.id == "select-all":
            sl.select_all()
        elif event.button.id == "select-none":
            sl.deselect_all()
        elif event.button.id == "quit":
            self.exit()
        elif event.button.id == "install":
            self.do_install(list(sl.selected))

    @work(thread=True)
    def do_install(self, ids: list[str]) -> None:
        widget = self.query_one("#log", Log)

        def log(msg: str) -> None:
            for line in str(msg).splitlines() or [""]:
                self.call_from_thread(widget.write_line, line)

        if not ids:
            log("Nothing selected.")
            return

        by_id = {t.id: t for t in TOOLS}
        for tid in ids:
            tool = by_id[tid]
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
