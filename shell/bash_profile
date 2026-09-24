export TERM=xterm-color

#export PS1='\[\033[1;36m\]\u\[\033[m\]@\[\033[1;32m\]\h:\[\033[1;35m\]\w\[\033[1;31m\]\$\[\033[0m\] '
export PS1='\[\033[1;36m\]\u\[\033[1;31m\]@\[\033[1;32m\]\h:\[\033[1;35m\]\w\[\033[1;31m\]\$\[\033[0m\] '

export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad
alias ls='ls -GFh'

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# Enable grep highlight
export GREP_OPTIONS='--color=auto'

# Configuration for history
export HISTTIMEFORMAT="%h %d %H:%M:%S "
export HISTSIZE=10000  # Default: 500
export HISTFILESIZE=10000
shopt -s histappend  # Appending bash command to history instead of overwriting
PROMPT_COMMAND='history -a'  # Store bash history immediately
export HISTCONTROL=ignorespace:erasedups
export HISTIGNORE="ls:ps:cd:history"

## alias for git
# alias to remove all local branches that are not on remote anymore
alias git-clean-branch="git fetch -p && git remote prune origin && git branch -vv | grep ': gone]'| grep -v '\*' | awk '{ print $1; }' | xargs git branch -d"
alias git-clean-local-branch="git checkout master && git pull && git branch | grep -v 'master' | xargs git branch -D"

## command for SCP with tunneling
# 1. First, open the tunnel
#  > ssh -L 1234:target-machine:22 -p 45678 user1@proxy-machine
#  ex) > ssh -L 5678:1.2.3.4:22 -p 22 bjang@11.22.33.44
# 2. Then, use the tunnel to copy the file directly to target
#  > scp -P 1234 ./<path-to-copy> user2@localhost:<path-to-be-copied>
#  ex) > scp -r -P 5678 ./<path-to-copy> bjang@localhost:<path-to-be-copied>

