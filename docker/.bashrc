# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions

# Bind Page UP/Page DOWN to the history search
bind '"\e[A":history-search-backward'
bind '"\e[B":history-search-forward'

export USER=sh891700
export KERNEL_VER="3.10.0-957"
export KERNEL_DIR="/usr/src/kernels/3.10.0-957.27.2.el7.x86_64"
export PATH="./:$PATH"

# share history across shells
export HISTCONTROL=ignoredups:erasedups  # no duplicate entries
export HISTSIZE=100000
export HISTFILESIZE=100000
shopt -s histappend
shopt -s cmdhist
export PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND$"\n"}history -a; history -c; history -r"

parse_git_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/'
}
parse_git_branch_paren() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/(\1)/'
}

export PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[01;31m\]$(parse_git_branch_paren)\[\033[00m\]\$ '

alias cdthor="cd main/Cumulus/firmware/THOR"
alias tclean="rm -rf obj;rm -rf THOR*"
alias tcleanall="rm -rf obj;rm -rf THOR*;make clobber"
alias tbuild="./make_thor_pkg.sh CRID=0001 RV=B debug VERBOSE=no < ~/sign.txt"

function mk_sign {
		local -r pw=${1:?"Specify a password"}
		echo $pw > ~/sign.txt
		chmod 600 ~/sign.txt
}

function glog_header {
    echo "Hash    Author Date  Commit Date  Author               Subject"
    echo "------- ------------ ------------ -------------------- -----------------------------"
}

function glog_headert {
    echo "Hash    Author Date                    Commit Date                    Author               Subject"
    echo "------- ------------------------------ ------------------------------ -------------------- -----------------------------"
}

function glog {
    glog_header
    git log --pretty=format:'%C(yellow)%h %C(red)%<(12)%ad %C(cyan)%<(12)%cd %C(magenta)%<(20,trunc)%an%Cgreen%d %Creset%s' --date=short "$@"
}

function glogt {
    glog_headert
    git log --pretty=format:'%C(yellow)%h %C(red)%<(30)%ad %C(cyan)%<(30)%cd %C(magenta)%<(20,trunc)%an%Cgreen%d %Creset%s' --date=local "$@"
}

function glogr {
    glog_header
    git log --pretty=format:'%C(yellow)%h %C(red)%<(12)%ar %C(cyan)%<(12)%cr %C(magenta)%<(20,trunc)%an%Cgreen%d %Creset%s' "$@"
}
