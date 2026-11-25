VERSION := 1.1.0
APP := license-gen
PREFIX ?= /usr/local
STAGE_PREFIX ?= /usr
APP_DIR = $(STAGE_PREFIX)/share/$(APP)
BUILD_ROOT := $(CURDIR)/build
DEB_WORK ?= $(BUILD_ROOT)
RPM_ROOT := $(BUILD_ROOT)/rpm
SOURCE := $(APP)-$(VERSION)
AUTO_INSTALL_DEPS ?= 1

.PHONY: test stage install uninstall deb rpm deb-deps rpm-deps
.DEFAULT_GOAL := test

install: STAGE_PREFIX = $(PREFIX)
install: stage

uninstall:
	rm -f "$(DESTDIR)$(PREFIX)/bin/$(APP)" "$(DESTDIR)$(PREFIX)/bin/generate-license"
	rm -f "$(DESTDIR)$(PREFIX)/share/applications/license-gen.desktop"
	rm -f "$(DESTDIR)$(PREFIX)/share/$(APP)/license_gen.py" "$(DESTDIR)$(PREFIX)/share/$(APP)/license_gui.py"
	for file in templates/*.txt; do rm -f "$(DESTDIR)$(PREFIX)/share/$(APP)/$$file" || exit; done
	rmdir "$(DESTDIR)$(PREFIX)/share/$(APP)/templates" "$(DESTDIR)$(PREFIX)/share/$(APP)" 2>/dev/null || true


test:
	python3 -m unittest -v

stage:
	install -Dm644 -t "$(DESTDIR)$(APP_DIR)" license_gen.py license_gui.py
	install -Dm644 -t "$(DESTDIR)$(APP_DIR)/templates" templates/*.txt
	install -Dm644 -t "$(DESTDIR)$(STAGE_PREFIX)/share/applications" license-gen.desktop
	install -d "$(DESTDIR)$(STAGE_PREFIX)/bin"
	printf '#!/bin/sh\nexec /usr/bin/python3 -E -B "%s/license_gen.py" "$$@"\n' "$(APP_DIR)" > "$(DESTDIR)$(STAGE_PREFIX)/bin/$(APP)"
	chmod 755 "$(DESTDIR)$(STAGE_PREFIX)/bin/$(APP)"
	ln -sf $(APP) "$(DESTDIR)$(STAGE_PREFIX)/bin/generate-license"

deb-deps:
	@set -eu; \
	command -v dpkg-deb >/dev/null 2>&1 && exit 0; \
	if [ "$(AUTO_INSTALL_DEPS)" != 1 ] || ! command -v apt-get >/dev/null 2>&1; then \
		echo 'Debian builds require dpkg-deb (package: dpkg).' >&2; exit 1; \
	fi; \
	prefix=; if [ "$$(id -u)" -ne 0 ]; then prefix=sudo; fi; \
	$$prefix apt-get update; \
	$$prefix apt-get install -y dpkg

rpm-deps:
	@set -eu; \
	command -v rpmbuild >/dev/null 2>&1 && exit 0; \
	if [ "$(AUTO_INSTALL_DEPS)" != 1 ] || ! command -v dnf >/dev/null 2>&1; then \
		echo 'RPM builds require rpmbuild (package: rpm-build).' >&2; exit 1; \
	fi; \
	prefix=; if [ "$$(id -u)" -ne 0 ]; then prefix=sudo; fi; \
	$$prefix dnf install -y rpm-build

deb: deb-deps
	@set -eu; mkdir -p "$(DEB_WORK)"; \
	root=$$(mktemp -d "$(DEB_WORK)/deb.XXXXXXXX"); trap 'rm -rf "$$root"' EXIT; \
	chmod 755 "$$root"; \
	$(MAKE) stage DESTDIR="$$root"; \
	install -Dm644 "$(APP)_$(VERSION)_all/DEBIAN/control" "$$root/DEBIAN/control"; \
	sed -i 's/^Version:.*/Version: $(VERSION)/' "$$root/DEBIAN/control"; \
	install -Dm644 LICENSE "$$root/usr/share/doc/$(APP)/copyright"; \
	TMPDIR="$(DEB_WORK)" dpkg-deb --root-owner-group --build "$$root" "$(CURDIR)/$(APP)_$(VERSION)_all.deb"

rpm: rpm-deps
	mkdir -p "$(RPM_ROOT)/SOURCES" "$(RPM_ROOT)/$(SOURCE)" "$(RPM_ROOT)/tmp"
	cp -r Makefile LICENSE README.md license-gen.desktop license_gen.py license_gui.py templates "$(RPM_ROOT)/$(SOURCE)/"
	tar -czf "$(RPM_ROOT)/SOURCES/$(SOURCE).tar.gz" -C "$(RPM_ROOT)" "$(SOURCE)"
	rpmbuild -bb --define "_topdir $(RPM_ROOT)" --define "_tmppath $(RPM_ROOT)/tmp" --define "app_version $(VERSION)" license-gen.spec
	cp "$(RPM_ROOT)"/RPMS/noarch/$(APP)-$(VERSION)-*.rpm "$(CURDIR)/"
