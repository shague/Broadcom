#!/bin/bash

function parse_git_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/'
}

# dbuild (docker build) will build a docker image.
function dbuild() {
    local -r image=${1:-brcm:latest}
    local -r uservdi=${2:-sh891700}
    local -r path=${3:-~/git/Broadcom/docker}

    docker build --rm -t $image \
        --build-arg uservdi=$uservdi --build-arg user=$(id -un) \
        --build-arg group=$(id -gn) --build-arg uid=$(id -u) --build-arg gid=$(id -g) \
        $path
}

# drun (docker run) will run a docker image.
function drun() {
    local -r name=${1:-bldr}
    local -r image=${2:-brcm:latest}
    local -r user=${3:-shague}
    local -r workdir=${4:-/git/$(parse_git_branch)/main/Cumulus/firmware/THOR}

    docker run --name $name -it --privileged \
        --mount type=bind,source=/Users/$user/.ssh,target=/home/$user/.ssh,readonly \
        --mount type=bind,source=/Users/$user/git,target=/git,consistency=cached \
        --mount type=bind,source=/opt/projects,target=/projects \
        -w $workdir \
        -u $user \
        $image
}
