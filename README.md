# dev_environment

Personal macOS dev environment setup: dotfiles plus a TUI installer that can set
up a new machine from scratch.

## Quick start

```sh
./bootstrap.sh
```

This installs Homebrew and `uv` if they're missing, then launches an interactive
TUI (built with `uv run install.py`) where you can select/unselect which tools and
configs to install: git, GitHub CLI, `ruff`, JetBrains Mono Nerd Font, Neovim +
LazyVim, vim, tmux, iTerm2 (+ theme/profile), Oh My Zsh (+ plugins), zsh, bash,
Claude Code, Codex CLI, GitHub Copilot CLI, `jq`, `curl`, `eza`, `bat`, `glow`,
VS Code, screen, and this repo's own dotfiles.

Re-run `./bootstrap.sh` any time — it's safe to run repeatedly and only
installs/relinks what you select.

## Layout

```
bootstrap.sh   entry point: ensures brew + uv, then runs install.py
install.py     TUI installer (Textual) — the source of truth for what gets installed
shell/         bashrc, zshrc, zsh_alias
git/           gitconfig, gitignore_global
editor/        vimrc, nvim/plugins/*.lua (LazyVim colorschemes + plugins),
               vscode/settings.json + extensions.txt
terminal/      screenrc, tmux.conf, iterm2/*.itermcolors, iterm2/*.json (profile)
claude/        Claude Code settings.json + statusline.sh
```

See `AGENTS.md` for conventions and where to add new tools/configs.
