%define name    ted2mkv
%define version 1.1
%define release 1

Name:           %{name}
Version:        %{version}
Release:        %{release}
Summary:        Download and convert TED videos to MKV format

Group:          Development/Libraries
License:        GPLv3
Source0:        %{name}-%{version}.tar.gz
Vendor:         Mansour Behabadi <mansour@oxplot.com>
URL:            https://github.com/oxplot/ted2mkv

BuildArch:      noarch
BuildRequires:  python >= 2.7
Requires:       python >= 2.7
Requires:       mkvtoolnix

%description
Downloads and converts TED videos available on ted.com to MKV files,
embedding all available subtitles and metadata.

%prep
%setup -n %{name}-%{version}

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc README LICENSE

%changelog
* Mon Oct 7 2013 Mansour Behabadi <mansour@oxplot.com> - 1.1-1
- Initial release
