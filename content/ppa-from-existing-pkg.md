Title: Creating a PPA from an existing Debian source package
Date: 2017-11-13 21:00

Using ngspice as an example, this post details how to acquire a source package from the Ubuntu repitories, make some modifications to the package config and upload it to a PPA.

The content here is based largely on [this post](https://blog.packagecloud.io/eng/2014/10/28/howto-gpg-sign-verify-deb-packages-apt-repositories/).

## Setup Launchpad credentials

To identify yourself to Launchpad you'll need to register your PGP and SSH keys with them.

```shell
$ export DEBFULLNAME="Mike Wild"
$ export DEBEMAIL="mike@mikeanthonywild.com"
```

## Obtain the source package

The Docker image for Ubuntu doesn't have the source repositories enabled by default (unsure about the standard image), so you'll need to enable these first by uncommenting the relevant line in `/etc/apt/source.list`. You'll also need to install some developer packages before you can grab the sources:

```shell
# apt-get update
# apt-get install gnupg pbuilder ubuntu-dev-tools apt-file
$ apt-get source ngspice
```

dpkg will download the source and extract it to a subdirectory. Before proceeding, enter the source directory:

```shell
$ cd ngspice-26
```

## Configuring the package

Debian configuration data is stored under `debian`. To modify the options used to build the package, modify the `debian/rules` file. In this example we add the `--with-ngshared` option to ensure that the ngspice shared library gets build (not enabled by default):

```make
./configure $(CROSS) \
                --prefix=/usr \
                --mandir=\$${prefix}/share/man \
                --enable-maintainer-mode \
                --with-editline=yes \
                --enable-xspice \
                --enable-cider \
                --disable-debug) \
                --with-ngshared
```

## Signing and uploading

Add to the changenotes (required, otherwise build and sign will fail). The Ubuntu release is required, otherwise package upload will fail:

```shell
$ dch
ngspice (26-1.1ubuntu1) zesty; urgency=medium

  * Enable --with-ngshared option

 -- Mike Wild <mike@mikeanthonywild.com>  Mon, 13 Nov 2017 21:54:14 +0000
```

Once this is done you will need to build, sign and upload the package:


```
$ debuild -S -sa
$ dput ppa:mikewild/ngspice-shared ../ngspice_26-1.1ubuntu1_source.changes
```

Launchpad should hopefully take care of building packages from here...
