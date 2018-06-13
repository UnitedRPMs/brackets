%{?nodejs_find_provides_and_requires}
%global arch %(test $(rpm -E%?_arch) = x86_64 && echo "x64" || echo "ia32")
%global debug_package %{nil}
%global _hardened_build 1
%global __provides_exclude_from /opt/%{name}/node-core
%global __requires_exclude_from /opt/%{name}/node-core
%global __provides_exclude_from /opt/%{name}/
%global __requires_exclude_from /opt/%{name}/
%global __requires_exclude (npm|libnode)

# commit brackets
%global _commit defded0cafa7a7e815ba30d5c8babaa483042dde
%global _shortcommit %(c=%{_commit}; echo ${c:0:7})

# commit brackets-shell
%global _commit1 66072d0d75040f9c9b49631475bd747e87e556f7
%global _shortcommit1 %(c=%{_commit1}; echo ${c:0:7})

%bcond_with clang
%bcond_with source_cef

Name:    brackets
Version: 1.13
Release: 1%{?dist}
Summary: An open source code editor for the web

Group:   Applications/Editors
License: MIT
URL:     http://brackets.io
Source0: https://github.com/adobe/brackets/archive/%{_commit}/%{name}-%{_shortcommit}.tar.gz
Source1: https://github.com/adobe/brackets-shell/archive/%{_commit1}/%{name}-shell-%{_shortcommit1}.tar.gz
# Why 306 mb with cef?
%if %{with source_cef} 
Source2: http://s3.amazonaws.com/files.brackets.io/cef/cef_binary_3.2785.1487_linux64_release.zip
%endif
Source3: brackets-snapshot
Source4: brackets-shell-snapshot

BuildRequires: alsa-lib
BuildRequires: GConf2 
BuildRequires: python2-devel 
BuildRequires: libXScrnSaver 
BuildRequires: nss-devel 
BuildRequires: pango-devel 
BuildRequires: unzip
BuildRequires: gtk2-devel
BuildRequires: icu
BuildRequires: git 
BuildRequires: curl
BuildRequires: desktop-file-utils
%if %{with clang} 
BuildRequires: clang llvm
%endif
BuildRequires: compat-libgcrypt
BuildRequires: libXtst-devel
Requires: desktop-file-utils
# enable LiveDevelopment Inspector
Recommends: ruby
Recommends: compat-libgcrypt


%description
Brackets is an open-source editor for web design and development
built on top of web technologies such as HTML, CSS and JavaScript.
The project was created and is maintained by Adobe, and is released
under an MIT License.

%prep
# We need some sub-modules
%{S:3} -c %{_commit}
%{S:4} -c %{_commit1}
mv -f  brackets-shell-%{_shortcommit1} %{name}-%{_shortcommit}/brackets-shell

%setup -T -D -n %{name}-%{_shortcommit} 

%if %{with source_cef} 
mkdir -p brackets-shell/downloads/
mv -f %{S:2} brackets-shell/downloads/
%endif

%build

# get nvm

git clone https://github.com/creationix/nvm.git ~/nvm

# activate nvm

echo "source ~/nvm/nvm.sh" >> ~/.bashrc

source ~/.bashrc
nvm install 6.11.0
nvm use 6.11.0

%if %{with clang}
export CC=clang
export CXX=clang++
%endif

# build 
pushd brackets-shell
	sed -i 's/python/python2/' gyp/gyp
	npm install
	#environment cleaning due to branch switch
	rm -rf out
	node_modules/grunt-cli/bin/grunt cef icu node create-project
        make V=0
popd
	npm install 
	sed "/'npm-install',$/d" -i Gruntfile.js
	brackets-shell/deps/node/bin/Brackets-node node_modules/grunt-cli/bin/grunt build

%install
pushd brackets-shell
	install -Dm755 installer/linux/debian/brackets "%{buildroot}/opt/brackets/brackets"
	install -dm755 "%{buildroot}/usr/bin"
	ln -s /opt/brackets/brackets "%{buildroot}/usr/bin/brackets"

	install -dm755 "%{buildroot}/usr/share"
	install -Dm644 installer/linux/debian/brackets.desktop "%{buildroot}/usr/share/applications/brackets.desktop"
	install -Dm644 installer/linux/debian/package-root/usr/share/icons/hicolor/scalable/apps/brackets.svg "%{buildroot}/usr/share/icons/hicolor/scalable/apps/brackets.svg"
	for size in 32 48 128 256; do
		install -Dm644 "out/Release/files/appshell${size}.png" "%{buildroot}/usr/share/icons/hicolor/${size}x${size}/apps/brackets.png"
	done

	pushd out/Release
	install -dm755 "%{buildroot}/opt/brackets"
	cp -R {files,locales,node-core} "%{buildroot}/opt/brackets/"
	find . -maxdepth 1 -type f -exec \
	cp {} %{buildroot}/opt/brackets/{} \;
	chmod 4755 %{buildroot}/opt/brackets/chrome-sandbox
        popd
         popd
###
	cp -rf samples %{buildroot}/opt/brackets/
        mkdir -p %{buildroot}/opt/brackets/www/
	cp -rf dist/* %{buildroot}/opt/brackets/www/

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null ||:
/usr/bin/update-desktop-database &>/dev/null ||:

%postun
if [ $1 -eq 0 ]; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null ||:
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null ||:
fi
/usr/bin/update-desktop-database &>/dev/null ||:

%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null ||:

%files
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_datadir}/icons/hicolor/scalable/apps/brackets.svg
/opt/brackets/

%changelog

* Thu Jun 07 2018 David Va <davidva AT tuta DOT io> - 1.13-1
- Updated to 1.13
- Initial build
