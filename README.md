# dev_environment

Personal macOS dev environment setup: dotfiles plus a TUI installer that can set
up a new machine from scratch.

## Quick start

```sh
./bootstrap.sh
```

This installs Homebrew and `uv` if they're missing, then launches an interactive
TUI (built with `uv run install.py`) where you can select/unselect which tools and
configs to install: `uv`, `ruff`, Neovim + LazyVim, tmux, iTerm2, git, GitHub CLI,
Claude Code, Codex CLI, GitHub Copilot CLI, Oh My Zsh, `jq`, `curl`, `eza`, `bat`,
`glow`, and this repo's own dotfiles.

Re-run `./bootstrap.sh` any time — it's safe to run repeatedly and only
installs/relinks what you select.

## Layout

```
bootstrap.sh   entry point: ensures brew + uv, then runs install.py
install.py     TUI installer (Textual) — the source of truth for what gets installed
shell/         bash_profile, sh_alias, zshrc, zsh_alias
git/           gitconfig
editor/        vimrc, nvim/plugins/*.lua (LazyVim colorschemes + plugins)
terminal/      screenrc, tmux.conf, iterm2/*.itermcolors
claude/        Claude Code settings.json + statusline.sh
```

See `AGENTS.md` for conventions and where to add new tools/configs.
