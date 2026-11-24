Name:           license-gen
Version:        %{app_version}
Release:        1%{?dist}
Summary:        Offline generator for open-source license files
License:        GPL-3.0-only
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  make
Requires:       python3 >= 3.9
Requires:       python3-pyqt6

%description
Generate open-source license files using an interactive CLI or a PyQt6 GUI.

%prep
%autosetup

%install
make stage DESTDIR="%{buildroot}"

%files
%license LICENSE
%doc README.md
%{_bindir}/license-gen
%{_bindir}/generate-license
%{_datadir}/applications/license-gen.desktop
%{_datadir}/license-gen/
