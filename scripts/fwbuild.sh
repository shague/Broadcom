#!/usr/bin/env bash

source ~/bin/utils.sh

usage_text=$(cat <<END
Usage:
  $0 -u USER -i ip -p PORT -r REPOSITORY [-b BUILDTYPE] [-t CHIPTYPE] [-c CRID -s SIGNFILE] [-v] [-n]

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
  -r, --repo
      REPO git repository
  -b, --buildtype
      Build type [debug, release, clean] default is release
  -t, --type
      CHIPTYPE [thor, chimp] default is thor
  -c, --crid
      CRID crid for signed image [0001]
  -s, --signfile
      SIGNFILE file containing signing credentials
  -v, --verbose
      Build with VERBOSE option
  --
      Do not interpret any more arguments as options
END
)

# set -x

user=""
ip=""
port=""
repo=""
buildtype="release"
chiptype="thor"
crid=""
signfile=""
verbose="no"

function parse_args() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
        -h|--help) usage 0 "$usage_text" "";;
        -x) set -x;;
        -i|--ip) ip="$2";;
        -p|--port) port="$2";;
        -u|--user) user="$2";;
        -r|--repo) repo="$2";;
        -b|--buildtype) buildtype="$2";;
        -t|--chiptype) chiptype="$2";;
        -c|--crid) crid="$2";;
        -s|--signfile) signfile="< $2";;
        -v|--verbose) debug="VERBOSE=yes";;
        --|-) break;;
        -*) echo "Invalid option: '$1'";;
        *) ;; # option argument, continue
        esac
        shift
    done

    # validate the options
    if [ -z "$ip" ]; then
        usage 1 "usage_text" "-i|--ip must be set"
    fi

    if [ -z "$port" ]; then
        usage 1 "usage_text" "-p|--port must be set"
    fi

    if [ -z "$user" ]; then
        usage 1 "usage_text" "-u|--user must be set"
    fi

    if [ -z "$repo" ]; then
        usage 1 "usage_text" "-r|--repo must be set"
    fi

    buildtypes="debug release clean"
    if [[ "$buildtypes" != *$buildtype* ]]; then
        usage 1 "" "-b|--buildtype '$buildtype' must be one of [$buildtypes]"
    fi
    if [ "$buildtype" == "clean" ] && [ "$chiptype" == "chimp" ]; then
        usage 1 "" "-b|--buildtype '$buildtype' and -t|--chiptype '$chiptype' is not supported"
    fi

    chiptypes="thor chimp"
    if [[ "$chiptypes" != *$chiptype* ]]; then
        usage 1 "" "-t|--chiptype '$chiptype' must be one of [$chiptypes]"
    fi

    if { [ -z "$crid" ] && [ -n "$signfile" ]; } || { [ -z "$signfile" ] && [ -n "$crid" ]; }; then
        usage 1 "" "Both CRID(-c) and SIGNFILE(-s) must be included"
    fi

    echo "Using these values: $user@$ip:$port, repo:$repo, buildtype=$buildtype, chiptype=$chiptype, crid=$crid, signfile=$signfile, verbose=$verbose"
}

echo "$0 called with args: $@"

parse_args "$@"
if [ "$buildtype" == "clean" ] ; then
    if [ "$chiptype" == "thor" ]; then
        local_build_cmd="cd $repo && git clean -fdx -e '**/cscope.' -e '**/.tags' -e '**/ncscope.' -e '**/venv' -e '**/.idea' -e '**/configs/*' -e 'main/Cumulus/firmware/THOR/CMakeLists.txt'"
        echo "Cleaning the build"
    fi
else
    if [ "$chiptype" == "thor" ]; then
        build_cmd="./make_thor_dual_pkg.sh RV=B SUPPORT_OPENSPDM=0 TRUFLOW=no $crid $buildtype $signfile"
        build_dir="$repo/main/Cumulus/firmware/THOR"
    else
        build_cmd="./make_cmba_afm_pkg.sh"
        build_dir="$repo/main/Cumulus/firmware/ChiMP/bootcode"
    fi
fi

if [ -n "$build_cmd" ]; then
    echo "Command to run via ssh: '$build_cmd'"

    ssh -p $port $user@$ip "
        cd $build_dir
        time $build_cmd
    "
else
    echo "Command to run locally: '$local_build_cmd'"
    # local_build_cmd="pwd"
    eval "$local_build_cmd"
fi
