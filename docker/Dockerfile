FROM centos:7

# Update packages. Use ius repo for more recent git.
# Add ln to perl binary because the build looks for it at that location.
# wget needed to download cmake. gcc/++ for building bnxPkgUtil.
RUN yum update -y && \
    yum install -y https://centos7.iuscommunity.org/ius-release.rpm && \
    yum install -y wget make gcc-c++ libc.i686 git2u-all perl-WWW-Mechanize sudo && \
    ln -sf /usr/bin/perl /usr/local/bin && \
    yum clean all

# Try to match up the host user:group with the guest user:group.
# Delete the guest user and group if found, then
# add new user, add to wheel group and update sudoers to allow passwordless sudo
# Add the vdi user. The signing scripts require a user account.
# Only create the vdi account if it is different than user.
ARG uservdi=sh891700
ARG user=shague
ARG group=staff
ARG uid=501
ARG gid=20
RUN if id -u $user; then userdel $user; fi && \
    gname=`getent group $gid | cut -d':' -f 1` && echo "looking for group($gid): $gname" && \
    if [ -n "$gname" ]; then groupdel $gname; fi && \
    groupadd -g $gid $group && \
    useradd -rm -d /home/$user -u $uid -g $gid -s /bin/bash $user && \
    usermod -aG wheel $user && \
    sed --in-place 's/^#\s*\(%wheel\s\+ALL=(ALL)\s\+NOPASSWD:\s\+ALL\)/\1/' /etc/sudoers && \
    if [ "$user" != "$uservdi" ]; then useradd -rm ${uservdi}; fi

# Set the user and working dir so the container start with them.
# Copy over any customizations.
USER ${user}
WORKDIR /home/$user
ADD .bashrc .bashrc
# TODO: get permissions for these files to be user rather than root, thought it doesn't matter.
# This is a limitation with docker that doesn't look to be fixed.
# COPY --chown can be used but it will not take args.
ADD .gitconfig .gitconfig
ADD .gitignore .gitignore

# Get cmake, but only copy the bin and share dirs to save space.
RUN sudo mkdir -p /opt/cmake && \
    sudo wget -q https://github.com/Kitware/CMake/releases/download/v3.15.2/cmake-3.15.2-Linux-x86_64.tar.gz && \
    sudo tar -xzf cmake-3.15.2-Linux-x86_64.tar.gz -C /opt/cmake --strip-components 1 cmake-3.15.2-Linux-x86_64/bin && \
    sudo tar -xzf cmake-3.15.2-Linux-x86_64.tar.gz -C /opt/cmake --strip-components 1 cmake-3.15.2-Linux-x86_64/share && \
    sudo rm -f cmake-3.15.2-Linux-x86_64.tar.gz

CMD ["/bin/bash"]

