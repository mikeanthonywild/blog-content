Title: Dynamically swapping proprietary Nvidia / AMD graphics drivers on Linux
Date: 2015-08-01 17:18

*Disclaimer: This post, and the script it is based on, follow a very small amount of research on the topic. As such, it's quite possible some of the information here may be wrong. If you spot any mistakes then please feel free to comment below. For a more tested solution check out [gl-driver-switch](https://github.com/solus-project/gl-driver-switch), a similar project.*

Recently I was in an environment which involved using a Linux system to run benchmark tests on PCIe cards fitted with [MXM graphics adapters](https://en.wikipedia.org/wiki/Mobile_PCI_Express_Module). As an aside, MXM cards are based on the PCIe specification, and are usually used to provide discrete graphics to high-end laptops.

The cards used are a mix of AMD and Nvidia, meaning that graphics drivers need to be regularly removed and installed anew. Tediously, this usually involves a reboot – a process which takes a while on the complex test machines being used.

*[gpu-driver-swap](https://github.com/mikeanthonywild/gpu-driver-swap)* is a little script I hacked together to automate this process. It allows for both drivers to be installed side-by-side, and instead detects the card type at boot, linking in all the correct drivers and support files. A startup service is provided for systemd, but the *gpuswap.sh* script can be used on any system.

To install, edit the paths in the *gpuswap.sh* script to point towards your drivers, and then run `sudo make install && sudo systemctl enable gpu-driver-swap.service`.

### How it works

Sadly I still don't fully understand how the proprietary Nvidia / AMD graphics stacks fit together. However, after some experimentation I discovered there are only a few key files involved, and it's a relatively straightforward exercise to swap between them.

The files in question are:

* **nvidia.ko / fglrx.ko** - kernel modules used for actual interaction with the graphics hardware. These are automatically loaded at boot when the card is initialised by udev. Modules registered publish a list of supported device IDs. udev searches this list from the bottom-up, loading the first module which matches the PCIe device ID. Nothing needs to be done for these files – udev always selects the correct module at boot.

* **xorg.conf** - Xorg configuration file. As part of the *Device* section, a *Driver* identifier specifies which Xorg driver should be used. Both Nvidia and AMD provide their own libraries (*nvidia_drv.so* and *fglrx_drv.so*) so that the X server may interact with the graphics hardware – though the hardware-level interfacing is handled by the kernel module. If at all possible, device-agnostic config should be placed inside the *xorg.conf.d* directory.

* **libglx.so** - Xorg OpenGL extension allowing OpenGL clients to send 3D rendering commands to the X server. Again, both Nvidia and AMD provide their own versions of this library – a mechanism to allow OpenGL and the X server to talk to each other.

* **libGL.so** - OpenGL vendor libraries. OpenGL exists only as a specification – there is no single official implementation on Linux, so vendors such as Nvidia and AMD provide their own versions of the OpenGL library which expose a subset of features supported by their hardware. Open source drivers all use Mesa, an open implementation of the OpenGL specification.

Applications can include graphical functionality on any Linux system by linking to these libraries. This can be seen by a simple call to `ldd`:

    :::console
    $ ldd /usr/X11R6/bin/glxgears
        linux-gate.so.1 =>  (0xffffe000)
        libGL.so.1 => /usr/lib/libGL.so.1 (0xb7ed3000)
        libXp.so.6 => /usr/lib/libXp.so.6 (0xb7eca000)
        libXext.so.6 => /usr/lib/libXext.so.6 (0xb7eb9000)
        libX11.so.6 => /usr/lib/libX11.so.6 (0xb7dd4000)
        libpthread.so.0 => /lib/libpthread.so.0 (0xb7d82000)
        libm.so.6 => /lib/libm.so.6 (0xb7d5f000)
        libc.so.6 => /lib/libc.so.6 (0xb7c47000)
        libGLcore.so.1 => /usr/lib/libGLcore.so.1 (0xb6c2f000)
        libnvidia-tls.so.1 => /usr/lib/tls/libnvidia-tls.so.1 (0xb6c2d000)
        libdl.so.2 => /lib/libdl.so.2 (0xb6c29000)
        /lib/ld-linux.so.2 (0xb7fb2000)

The libraries usually point at the vendor's own library by means of a symbolic link. *gpu-driver-swap* utilises this same technique by swapping these symbolic links to the correct drivers based upon the card detected at boot. Updating these three files, it's possible to get fully-accelereated 3D graphics on any supported Nvidia / AMD card.

### Swapping between open-source and proprietary drivers

This system can be easily extended to dynamically swap between open-source and proprietary drivers, even after X has started, with a few simple additions:

* Call `ldconfig` after symbolically linking each library to update the linker's cache.

* Restart the X server to load the new X drivers.

* Unload either the open-source or proprietary kernel module, and load the other.

### Further reading

* [udev and kernel modules](https://doc.opensuse.org/documentation/html/openSUSE_121/opensuse-reference/cha.udev.html#sec.udev.drivers)

* [GLX](https://en.wikipedia.org/wiki/GLX)

* [Mesa](http://www.mesa3d.org/intro.html)
