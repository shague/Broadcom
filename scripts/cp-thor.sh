#!/bin/bash

# TODO:
# - add config file option so you don't need to pass parameters, or just use
# the default global vars block.
# - add signed option

source ~/bin/utils.sh

usage_text=$(cat <<END
Usage:
  $0 -l [-i CRID] -e <BNXTDRVVER> -m <BNXTMTVER> -s <SITVER> -u <USER>"
  [-d DEVICE] [-l] [-n HOSTNAME] [-r REV] [-t PKGTYPE] [-a]"
  $0 -c -u <USER>"
  $0 -p -u <USER> [-n HOSTNAME] [-r REV] [-i CRID]"

Options:
  -h help
  -x enable debugging
  -l scp and load new pkg"
  -c clean all the backup pkgs"
  -p scp pkg"
  -a build dual package
  -d DEVICE {p1p1}"
  -e BNXTDRVVER bnxt_en-1.10.0-216.0.113.0"
  -i CRID 0001|0002"
  -m BNXTMTVER bnxtmt-216.0.112.0-x86_64"
  -n HOSTNAME name of the host {mortise}"
  -r REV A0|B0 {A0}"
  -s SITVER 216.0.155.0"
  -t PKGTYPE debug|release {release}"
  -u USER"
END
)

# global vars for parsed arguments
clean=0
scp=0
dev="p1p1"
help=0
hostname="mortise"
load=0
drvver=""
mtver=""
sitver=""
pkgtype="release"
user=""
crid=""
rev="A0"
dual=false

# parse_args parses the command line options and completes basic verification
# The arguments are stored in glabal variables. Those vars are listed above.
function parse_args() {
    local OPTIND
    while getopts "achlpxd:e:i:m:n:r:s:t:u:" opts; do
        case "$opts" in
        a) dual=true;;
        c) clean=1;;
        d) dev="$OPTARG";;
        h) help=1;;
        i) crid="$OPTARG";;
        n) hostname="$OPTARG";;
        l) load=1;;
        p) scp=1;;
        e) drvver="$OPTARG";;
        m) mtver="$OPTARG";;
        r) rev="$OPTARG";;
        s) sitver="$OPTARG";;
        t) pkgtype="$OPTARG";;
        u) user="$OPTARG";;
        x) set -x;;
        esac
    done

    if [ $help = 1 ]; then
        usage 0 "$usage_text" ""
    fi
    if [ -z "$user" ]; then
        usage 1 "$usage_text" "missing required argument: -u USER"
    fi
    if [ "$pkgtype" != "debug" ] && [ "$pkgtype" != "release" ]; then
        usage 1 "$usage_text" "invalid pkgtype: $pkgtype"
    fi
    if [ -n "$rev" ]; then
        if [ "$rev" != "A0" ] && [ "$rev" != "B0" ]; then
            usage 1 "$usage_text" "invalid revision: $rev"
        fi
    fi
    if [ -n "$crid" ]; then
        if [ "$crid" != "0001" ] && [ "$crid" != "0002" ]; then
            usage 1 "$usage_text" "invalid crid: $crid"
        fi
    fi
    if [ $load = 1 ]; then
        if [ -z "$sitver" ] || [ -z "$drvver" ] || [ -z "$mtver" ] ; then
            usage 1 "$usage_text" "missing one or more required arguments: -s SITVER -d BNXTDRVVER -m BNXTMTVER"
        fi
    fi
}

# getpkgtypedirname returns the local dir name for the pkgtype:
# THOR{B0}{_DUAL_}{_SIGNED_}{_DEBUG_}
# unsigned:      THOR,                  THOR_DEBUG
# signed:        THOR_SIGNED_0001,      THOR_SIGNED_0001_DEBUG
# dual unsigned: THOR_DUAL,             THOR_DUAL_DEBUG
# dual signed:   THOR_DUAL_SIGNED_0001, THOR_DUAL_SIGNED_0001_DEBUG
function getpkgtypedirname() {
    local -r pkgtype=$1
    local -r crid=$2
    local -r rev=$3
    local -r dual=$4
    local pkgtypedir="THOR"

    if [ "$rev" = "B0" ]; then
        pkgtypedir=$pkgtypedir$rev
    fi
    if $dual; then
        pkgtypedir=$pkgtypedir"_DUAL"
    fi
    if [ "$crid" != "" ]; then
        pkgtypedir=$pkgtypedir"_SIGNED_$crid"
    fi
    if [ "$pkgtype" = "debug" ]; then
        pkgtypedir=$pkgtypedir"_DEBUG"
    fi

    echo "$pkgtypedir"
}

# get the local build pkg name
# thor{_dual}{B0}{.signed.crid0001.}pkg
# thorB0.pkg, thor.signed.crid0001.pkg
# thor_dual.pkg, thor_dual.signed.crid0001.pkg
function getpkgname() {
    local -r pkgtype=$1
    local -r crid=$2
    local -r rev=$3
    local -r dual=$4
    local pkgname="thor"

    if $dual; then
        pkgname=$pkgname"_dual"
    else
        # only unsigned images add rev to the thor string
        if [ "$rev" = "B0" ] && [ -z "$crid" ]; then
            pkgname=$pkgname$rev
        fi
    fi
    if [ "$crid" != "" ]; then
        pkgname=$pkgname".signed.crid$crid"
    fi
    pkgname=$pkgname".pkg"

    echo "$pkgname"
}

function gethostpkgname() {
    local -r pkgname=$1
    local -r pkgtype=$2
    local -r rev=$3
    local -r dual=$4
    local hostpkgname=""

    if $dual; then
        hostpkgname="$pkgname.dual.$rev.$pkgtype"
    else
        hostpkgname="$pkgname.$rev.$pkgtype"
    fi

    echo "$hostpkgname"
}

function getlnpkgname() {
    local -r pkgname=$1
    local -r pkgtype=$2
    local -r rev=$3
    local -r dual=$4
    local lnpkgname=""

    if $dual; then
        lnpkgname="thor.dual.pkg"
    else
        lnpkgname="thor.pkg"
    fi

    echo "$lnpkgname"
}

function clean_pkgs() {
    local -r hostip=$1

    echo "Removing backup packages"
    ssh $user@$hostip "rm -f $rpath/thor*.pkg.*.bak"
}

function scp_pkg() {
    local -r hostip=$1
    local -r pkgname=$2
    local -r pkgtypedir=$3
    local -r pkgtype=$4
    local -r rev=$5
    local -r dual=$6
    local hostpkgname=$(gethostpkgname  "$pkgname" "$pkgtype" "$rev" "$dual")
    local lnpkgname=$(getlnpkgname  "$pkgname" "$pkgtype" "$rev" "$dual")

    echo "copying $pkgtypedir/$pkgname to $hostname($hostip):/tmp/$hostpkgname"
    scp -q $pkgtypedir/$pkgname $user@$hostip:/tmp/$hostpkgname

    echo "ssh commands about to execute:"
    echo "backing up $rpath/$hostpkgname to $rpath/$hostpkgname.$time.bak"
    echo "moving /tmp/$hostpkgname to $rpath"
    echo "creating link: ln -sf $rpath/$hostpkgname $rpath/$lnpkgname"
    echo "ssh executing commands now"
    ssh $user@$hostip "
        mv $rpath/$hostpkgname $rpath/$hostpkgname.$time.bak || true
        mv /tmp/$hostpkgname $rpath
        ln -sf $rpath/$hostpkgname $rpath/$lnpkgname
    "
}

function load_pkg() {
    local -r hostip=$1
    local -r pkgname=$2
    local -r pkgtype=$3
    local -r rev=$4
    local -r sitpath=$5
    local -r mtver=$6
    local -r drvver=$7
    local hostpkgname=$(gethostpkgname  "$pkgname" "$pkgtype" "$rev" "$dual")

    echo "rmmod bnxt_en"
    # TODO: check if driver loaded and then rmmod. rmmod on unloaded driver
    # hangs for a bit so don't do it unless necessary.
    ssh $user@$hostip "rmmod bnxt_en" || true
    echo "loading pkg with bnxtmt..."
    ssh $user@$hostip "
        cd $sitpath/$mtver;
        echo 'cmd: ./load.sh -eval nvm pkginstall $rpath/$hostpkgname';
        ./load.sh -eval 'nvm pkginstall $rpath/$hostpkgname';
        echo 'cmd rc= $?';
        echo 'cmd: ./load.sh -eval primate decode shmem | grep tag_commit;
        ./load.sh -eval 'primate decode shmem' | grep tag_commit;
        sleep 1;
        echo 'cmd: insmod $sitpath/$drvver/bnxt_en.ko';
        insmod $sitpath/$drvver/bnxt_en.ko;
        echo 'cmd rc= $?';
        sleep 1;
        echo 'cmd: dmesg | tail';
        dmesg | tail;
        echo 'cmd: ip link';
        ip link
    "
    # echo "loading pkg with bnxtnvm"
    # ssh $user@$hostip "$path/bnxtnvm -force --yes -dev=$dev -live install $path/$pkgname" || true
    # ssh $user@$hostip "$path/bnxtnvm -dev=$dev device_info"
    # ssh $user@$hostip "$path/bnxtnvm -dev=$dev view -type=pkglog"
    # echo "insmod $path/$drvver/bnxt_en.ko"
    # ssh $user@$hostip "insmod $path/$drvver/bnxt_en.ko" || true

    # TODO: add a call to verify the load passed
    # bnxtnvm has version, pkgver, etc calls but none show anything useful
    # as far as verification. Maybe primate trace could add value
}

function print_vars() {
    echo "Using these values:"
    echo "clean: $clean, scp: $scp, load: $load"
    echo "hostname: $hostname, hostip: $hostip"
    echo "pkgtype: $pkgtype, pkgtypedir: $pkgtypedir"
    echo "pkgname: $pkgname"
    echo "rpath: $rpath, sitpath: $sitpath"
    echo "sitver: $sitver, drvver: $drvver, mtver: $mtver"
    echo "dev: $dev"
    echo "time: $time"
    echo "rev: $rev, crid: $crid"
    echo "dual: $dual"
    echo ""
}

parse_args "$@"
rpath=/home/$user
sitpath="$rpath/$sitver"
hostip=$(name2ip $hostname)
pkgtypedir=$(getpkgtypedirname "$pkgtype" "$crid" "$rev" "$dual")
pkgname=$(getpkgname  "$pkgtype" "$crid" "$rev" "$dual")

# 20190815.014521[.123] - %3N (nanoseconds) not supported on mac
case "$OSTYPE" in
linux*) time="$(date +"%Y%m%d.%I%M%S.%3N")";;
darwin*) time="$(date +"%Y%m%d.%I%M%S")";;
*) usage 1 "$usage_text" "unknown OSTYPE: $OSTYPE"
esac

print_vars

if [ $clean = 1 ]; then
    clean_pkgs "$hostip"
fi
if [ $scp = 1 ]; then
    scp_pkg "$hostip" "$pkgname" "$pkgtypedir" "$pkgtype" "$rev" "$dual"
fi
if [ $load = 1 ]; then
    scp_pkg "$hostip" "$pkgname" "$pkgtypedir" "$pkgtype" "$rev" "$dual"
    load_pkg "$hostip" "$pkgname" "$pkgtype" "$rev" "$sitpath" "$mtver" "$drvver"
fi
