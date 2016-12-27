Title: Installing Adobe Lightroom 5 on Ubuntu 16.04 wtih Wine
Date: 2016-12-27 21:29

Running Windows programs on Linux under Wine can be very hit-and-miss, especially with outdated packages on Ubuntu LTS. Despite being listed as a Gold program on the WineHQ AppDB, the latest release of Lightroom 5 (5.7) will trip up with older versions of Wine which don't include [special patches with workarounds](https://bugs.winehq.org/show_bug.cgi?id=35192). Fortunately Wine 2.0 includes these patches and can be found in Wine's development PPA.

To begin, add the PPA and grab a more modern version of Wine. **[1]**

    sudo add-apt-repository ppa:wine/wine-builds
    sudo apt update && sudo apt install winehq-devel

Download the latest Adobe Lightroom installer [here](https://www.adobe.com/support/downloads/detail.jsp?ftpID=5853) and create a 32-bit Wine prefix for it. **[2]**

    export WINEPREFIX=~/.wine_lr5 && export WINEARCH=win32 winetricks win7
    wine ~/Downloads/path_to_lightroom_installer.exe
    winetricks winxp
    winetricks gdiplus corefonts windowscodecs ie7
    winetricks win7

Possibly your system will not be using the version of Winetricks from the development PPA and the installation of IE7 will fail with a 404. To rectify this, you can download a newer version of Winetricks with `wget https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks && sudo cp winetricks /usr/bin/ && sudo chmod +x /usr/bin/winetricks` **[3]**.

Having done all of that, Lightroom 5 should be installed, and thanks to some extra packages from Winetricks, the UI should render correctly.

### References

1. https://www.linuxbabe.com/ubuntu/install-wine-devel-package-ubuntu-16-04
2. https://bugs.winehq.org/show_bug.cgi?id=35192#c59
3. https://askubuntu.com/questions/756402/how-to-install-wine-in-ubuntu-15-10
