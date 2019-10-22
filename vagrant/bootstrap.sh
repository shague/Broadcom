#!/bin/bash

# Update packages. Use ius repo for more recent git.
# gcc/++ for building bnxPkgUtil.
# Add ln to perl binary because the build looks for it at that location.
# Add ln to cmake3 because build requires cmake version 3 but calls cmake.
yum update -y \
&& yum install -y https://centos7.iuscommunity.org/ius-release.rpm \
&& yum install -y \
    cmake3 \
    gcc gcc-c++ \
    git2u \
    glibc.i686 glibc-static \
    java-1.8.0-openjdk-headless \
    kernel-devel \
    make \
    perl-WWW-Mechanize \
    sudo \
    tcl-devel \
    npm \
&& ln -sf /usr/bin/cmake3 /usr/bin/cmake \
&& ln -sf /usr/bin/perl /usr/local/bin \
&& yum clean all

# Add the vdi user if it does not exit.
# The signing scripts require a user account.
if ! id -u sh891700; then adduser -rm sh891700; fi
