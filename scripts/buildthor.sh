#!/usr/bin/env bash

source ~/bin/utils.sh

usage_text=$(cat <<END
Usage:
  $0 -u USER -i ip -p PORT [-c CRID -s SIGNFILE] [-d] [-v] [-l] [-n]

Options:
  -h, --help
      help
  -x
      enable debugging
  -u, --user
      USER name of user with passwordless login to build server
  -i, --ip
      IP ip address of build server
  -p, --port
      PORT ssh port of build server
  -c, --crid
      CRID crid for signed image
  -s, --signfile
      SIGNFILE file containing signing credentials
  -d, --debug
      Build with debug option
  -v, --verbose
      Build with VERBOSE option
  -l, --dual
      Build dual package
  -n, --clean
      Clean the build
  --
      Do not interpret any more arguments as options
END
)

user=""
ip=""
port=""
crid=""
signfile=""
debug=""
verbose="no"
dual=false
clean=false
function parse_args() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
        -h|--help) usage 0 "$usage_text" "";;
        -x) set -x;;
        -i|--ip) ip="$2";;
        -p|--port) port="$2";;
        -u|--user) user="$2";;
        -c|--crid) crid="$2";;
        -s|--signfile) signfile="< $2";;
        -l|--dual) dual=true;;
        -n|--clean) clean=true;;
        -d|--debug) debug="debug";;
        -v|--verbose) debug="VERBOSE=yes";;
        --|-) break;;
        -*) echo "Invalid option: '$1'";;
        *) ;; # option argument, continue
        esac
        shift
    done

    if { [ -z "$crid" ] && [ -n "$signfile" ]; } || { [ -z "$signfile" ] && [ -n "$crid" ]; }; then
        usage 1 "$usage_text" "Both CRID(-c) and SIGNFILE(-s) must be included"
    fi

}

parse_args "$@"
if $clean ; then
    thor_cmd_all="rm -rf obj;rm -rf THOR*;make clobber"
    echo "Cleaning the build"
else
    echo "Using these values: $user@$ip:$port, crid=$crid, signfile=$signfile, debug=$debug, verbose=$verbose, dual=$dual"
    if $dual ; then
        thor_cmd="./make_thor_dual_pkg.sh"
    else
        thor_cmd="./make_thor_pkg.sh"
    fi
    thor_cmd_all="$thor_cmd RV=B $crid $debug $signfile"
fi

echo "Command to run: '$thor_cmd_all'"

ssh -p $port $user@$ip "
    cd /git/int_nxt/main/Cumulus/firmware/THOR
    $thor_cmd_all
"
