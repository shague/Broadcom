FROM centos:7

# Update packages. Use ius repo for more recent git.
RUN yum update -y && \
    yum install -y https://centos7.iuscommunity.org/ius-release.rpm && \
    yum install -y make glibc.i686 git2u-all perl-WWW-Mechanize sudo && \
    yum clean all

# Build looks for perl at this location.
RUN ln -sf /usr/bin/perl /usr/local/bin

# Try to match up the host user:group with the guest user:group.
# Delete the guest user and group if found, then
# add new user, add to wheel group and update sudoers to allow passwordless sudo
ARG uservdi=sh891700
ARG user=shague
ARG group=staff
ARG uid=501
ARG gid=20
RUN if id -u ${user}; then userdel ${user}; fi && \
    gname=`getent group $gid | cut -d':' -f 1`; echo "looking for group($gid): $gname"; if [ -n "$gname" ]; then groupdel $gname; fi && \
    groupadd -g ${gid} ${group} && \
    useradd -rm -d /home/${user} -u ${uid} -g ${gid} -s /bin/bash ${user}
RUN usermod -aG wheel shague
RUN sed --in-place 's/^#\s*\(%wheel\s\+ALL=(ALL)\s\+NOPASSWD:\s\+ALL\)/\1/' /etc/sudoers

# Add the vdi user. The signing scripts require a user account.
RUN useradd -rm ${uservdi}

# Set the user and working dir so the container start with them.
# Copy over any customizations.
USER ${user}
WORKDIR /home/${user}
ADD .bashrc .bashrc
# TODO: get permissions for these files to be user rather than root
ADD .gitconfig .gitconfig
ADD .gitignore .gitignore

CMD ["/bin/bash"]
