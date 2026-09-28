# AGENTS.md

Personal dotfiles repo for macOS shell/dev environment setup. Not a software
project — there is no build, lint, or test step.

## Layout

Entry points live at the repo root; everything else is grouped by topic.

- `bootstrap.sh` — mandatory bootstrap: installs Homebrew + `uv` if missing, then
  runs `uv run install.py`. Entry point for setting up a new machine.
- `install.py` — `uv`-run, single-file Python script (PEP 723 inline deps, pulls in
  `textual`) that shows a TUI checklist of every tool/config below; the user
  selects/unselects items and installs/links them. The `TOOLS` list is the single
  source of truth for what this repo manages.

- `shell/` — bash/zsh env setup. This repo is zsh-only in practice (see
  `zshrc`/`zsh_alias` below); `bashrc` is kept for anyone who still
  drops into bash, but isn't actively maintained.
  - `bashrc` — bash env vars, prompt (`PS1`), history config, `ls`/grep aliases,
    Docker/pipenv/cargo env sourcing. Symlinked to `~/.bashrc` (bash reads this for
    interactive non-login shells, which is how bash actually gets invoked here).
  - `zshrc` — oh-my-zsh setup (`ZSH_THEME="robbyrussell"`,
    `plugins=(git zsh-autosuggestions zsh-syntax-highlighting)`), editor/PATH env
    vars, Docker/kaf/kubectl/dbt integration sourcing. Symlinked to `~/.zshrc`.
    `install.py` also clones `zsh-autosuggestions`/`zsh-syntax-highlighting` into
    `~/.oh-my-zsh/custom/plugins/` (not bundled with oh-my-zsh itself), otherwise
    the `plugins=(...)` line silently no-ops on a fresh machine.
  - `zsh_alias` — all shell aliases/functions (eza/bat/glow/nvim wrappers, kubectl,
    jq helpers, git branch cleanup, terraform, brew/gcloud update). Symlinked to
    `~/.zsh_alias`, sourced from `zshrc`. (Previously split into a zsh-only file
    plus a "shared bash+zsh" `sh_alias` — merged back into one file since nothing
    actually sourced `sh_alias` for bash; see git history if bash support becomes
    a real target again.)
- `git/`
  - `gitconfig` — global git config: `delta` as pager/diff filter, aliases (`st`,
    `co`, `br`, `plog`, `glog`, etc.), `pull.rebase = true`, SSH rewrite for GitHub.
  - `gitignore_global` — global gitignore (`**/.claude/settings.local.json`),
    symlinked to `~/.config/git/ignore` (git reads this path by default even
    without an explicit `core.excludesfile`, so none is set in `gitconfig`).
- Fonts (no dedicated directory — just a `Tool` entry in `install.py`):
  - JetBrains Mono Nerd Font (brew cask `font-jetbrains-mono-nerd-font`) — backs
    icon rendering for `nvim-web-devicons` (LazyVim) and `eza` in the terminal.
- `editor/`
  - `vimrc` — vim/neovim config.
  - `nvim/plugins/colorscheme.lua` — extra LazyVim colorschemes (catppuccin,
    tokyonight, kanagawa, monokai-pro — the active one), copied into
    `~/.config/nvim/lua/plugins/` after `install.py` clones the LazyVim starter.
  - `nvim/plugins/git.lua` — gitsigns (inline blame, hunk keymaps) + vim-fugitive,
    copied the same way.
  - `install.py` also appends `vim.o.background = "dark"` to
    `~/.config/nvim/init.lua` if it isn't already there.
  - `vscode/settings.json` — VS Code user settings (One Dark Pro Monokai Darker
    theme, per-language formatters/rulers, gitlens/yaml/copilot config),
    symlinked to `~/Library/Application Support/Code/User/settings.json`.
  - `vscode/extensions.txt` — one extension ID per line, installed with
    `code --install-extension` (theme + language/lint/git plugins).
- `terminal/`
  - `screenrc` — GNU screen config.
  - `tmux.conf` — tmux config.
  - `iterm2/Dracula+.itermcolors` — color preset matching the profile's actual
    colors below (it turned out to be iTerm2's built-in "Dracula+" preset,
    already applied — not a bespoke palette, hence the name); opened with
    `open` so iTerm2 prompts to import it as a reusable Color Preset.
  - `iterm2/DynamicProfiles.json` — the actual default iTerm2 profile (font,
    ANSI colors, triggers, keyboard map, status bar layout), symlinked into
    `~/Library/Application Support/iTerm2/DynamicProfiles/` (iTerm2's
    supported mechanism for version-controlled profiles; hot-reloaded, doesn't
    touch unrelated app prefs). `install.py` also sets
    `Default Bookmark Guid` via `defaults write` so it's selected as default on
    a fresh machine. This is the source of truth for the colors above — if you
    change the profile's colors in iTerm2, regenerate the `.itermcolors` preset
    from it rather than editing the two independently.
- `claude/`
  - `settings.json` — Claude Code CLI settings (permissions, status line, theme,
    effort level).
  - `statusline.sh` — Claude Code status line script referenced by `settings.json`.

## Conventions

- Every file under `shell/`, `git/`, `editor/`, `terminal/`, `claude/` is meant to
  be symlinked into `$HOME` (or `~/.claude/`, `~/.config/nvim/`) by `install.py` —
  check existing symlinks before assuming a fresh copy.
- Keep shell scripts portable (bash/zsh) unless a file is explicitly bash-only or
  zsh-only (the directory/filename already signals which).
- `git/gitconfig` has some duplicate `[core]`/`[interactive]`/`[delta]`/`[merge]`
  blocks (git merges them) — prefer editing the existing key rather than adding a
  new block.
- No secrets or machine-specific absolute paths that would break on another
  machine, aside from intentional ones already present (e.g. editor path).

## Making changes

- Edit the file directly; there's no build step to run afterward.
- If a change affects how the shell or git behaves, mention that a new shell /
  `source`d file is needed to pick it up.
- New tool/config to install on a fresh machine → add a `Tool(...)` entry to the
  `TOOLS` list in `install.py` (check + install callable), not a new standalone
  script. If it needs a config file, put it under the matching topic directory
  (`shell/`, `git/`, `editor/`, `terminal/`, `claude/`) and link it with the
  `link(rel_src, dest)` helper.
- `./bootstrap.sh` is the only thing that should be run "cold" (it assumes nothing
  beyond macOS + `curl`); everything else in `install.py` assumes `brew` and `uv`
  already exist.
