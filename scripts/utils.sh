#!/bin/bash

function name2ip() {
    local -r name=$1

    case $name in
    h171)
        ip=10.13.241.171
        ;;

    dovetail)
        ip=10.27.215.76
        ;;

    miter)
        ip=10.27.215.109
        ;;

    mortise |*)
        ip=10.27.215.67
        ;;

    esac
    echo $ip
}

function usage() {
    local -r rc=${1:-0}
    local -r help=${2:-""}
    local -r msg=${3:-""}

    if [ -n "$msg" ]; then
        printf "\n%s\n" "$msg"
    fi

    if [ -n "$help" ]; then
        printf "\n%s\n" "$help"
    fi

    set -e
    trap "exit 1" ERR
    exit $rc
}
