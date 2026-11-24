VERSION := 1.0.0
APP := license-gen
APP_DIR := /usr/share/$(APP)
BUILD_ROOT := $(CURDIR)/build
DEB_WORK ?= $(BUILD_ROOT)
RPM_ROOT := $(BUILD_ROOT)/rpm
SOURCE := $(APP)-$(VERSION)

.PHONY: test stage deb rpm

test:
	python3 -m unittest -v

stage:
	install -Dm644 -t "$(DESTDIR)$(APP_DIR)" license_gen.py license_gui.py
	install -Dm644 -t "$(DESTDIR)$(APP_DIR)/templates" templates/*.txt
	install -Dm644 -t "$(DESTDIR)/usr/share/applications" license-gen.desktop
	install -d "$(DESTDIR)/usr/bin"
	printf '#!/bin/sh\nexec /usr/bin/python3 -E $(APP_DIR)/license_gen.py "$$@"\n' > "$(DESTDIR)/usr/bin/$(APP)"
	chmod 755 "$(DESTDIR)/usr/bin/$(APP)"
	ln -sf $(APP) "$(DESTDIR)/usr/bin/generate-license"

deb:
	@set -eu; mkdir -p "$(DEB_WORK)"; \
	root=$$(mktemp -d "$(DEB_WORK)/deb.XXXXXXXX"); trap 'rm -rf "$$root"' EXIT; \
	chmod 755 "$$root"; \
	$(MAKE) stage DESTDIR="$$root"; \
	install -Dm644 license-gen_1.0.0_amd64/DEBIAN/control "$$root/DEBIAN/control"; \
	sed -i 's/^Version:.*/Version: $(VERSION)/' "$$root/DEBIAN/control"; \
	install -Dm644 LICENSE "$$root/usr/share/doc/$(APP)/copyright"; \
	TMPDIR="$(DEB_WORK)" dpkg-deb --root-owner-group --build "$$root" "$(CURDIR)/$(APP)_$(VERSION)_all.deb"

rpm:
	mkdir -p "$(RPM_ROOT)/SOURCES" "$(RPM_ROOT)/$(SOURCE)" "$(RPM_ROOT)/tmp"
	cp -r Makefile LICENSE README.md license-gen.desktop license_gen.py license_gui.py templates "$(RPM_ROOT)/$(SOURCE)/"
	tar -czf "$(RPM_ROOT)/SOURCES/$(SOURCE).tar.gz" -C "$(RPM_ROOT)" "$(SOURCE)"
	rpmbuild -bb --define "_topdir $(RPM_ROOT)" --define "_tmppath $(RPM_ROOT)/tmp" --define "app_version $(VERSION)" license-gen.spec
	cp "$(RPM_ROOT)"/RPMS/noarch/$(APP)-$(VERSION)-*.rpm "$(CURDIR)/"
