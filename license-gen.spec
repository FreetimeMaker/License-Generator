Name:           license-gen
Version:        1.0.0
Release:        1%{?dist}
Summary:        License Generator Application
License:        GPLv3
BuildArch:      x86_64
Source0:        license-gen.py
Source2:        license-gen.png
Source3:        license-gen.desktop

Requires:       python3 python3-pyqt6

%description
A console and GUI License choose for Open Source Software.

%prep

%build

%install
mkdir -p %{buildroot}/opt/xmrigui
mkdir -p %{buildroot}/usr/local/bin
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps
mkdir -p %{buildroot}/usr/share/applications

install -m 644 %{_sourcedir}/mining_tools.py %{buildroot}/usr/local/bin/mining_tools.py
install -m 755 %{_sourcedir}/xmrigui.py %{buildroot}/usr/local/bin/xmrigui
install -m 755 %{_sourcedir}/xmrig %{buildroot}/opt/xmrigui/xmrig
install -m 644 %{_sourcedir}/xmrigui.png %{buildroot}/opt/xmrigui/xmrigui.png
install -m 644 %{_sourcedir}/xmrigui.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/xmrigui.png
install -m 644 %{_sourcedir}/xmrigui.desktop %{buildroot}/usr/share/applications/xmrigui.desktop

%files
/usr/local/bin/mining_tools.py
/usr/local/bin/xmrigui
/opt/xmrigui/
/usr/share/icons/hicolor/256x256/apps/xmrigui.png
/usr/share/applications/xmrigui.desktop
