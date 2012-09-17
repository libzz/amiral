r := $(shell svnversion -nc .. | sed -e 's/^[^:]*://;s/[A-Za-z]//')
tmpdir := $(shell mktemp -ud)
pwd := $(shell pwd)

# Modules that should be installed for the client
CLIENT_MODULES := $(COMMON_MODULES) \
	$(shell grep "CCSD_CLIENT" modules/* | cut -f1 -d':' | xargs)

# Modules that should be installed for the server
SERVER_MODULES := $(COMMON_MODULES) \
	$(shell grep "CCSD_SERVER" modules/* | cut -f1 -d':' | xargs)

all:

install-client:
	install -d -m755 -o root -g root \
	        $(DESTDIR)/usr/share/ccsd/crcnetd/modules
	install -d -m755 -o root -g root \
	        $(DESTDIR)/usr/share/ccsd/resources
	install -m644 -o root -g root $(CLIENT_MODULES) \
		$(DESTDIR)/usr/share/ccsd/crcnetd/modules/
	cp resources/ifacestatus.js $(DESTDIR)/usr/share/ccsd/resources
	chown -R root: $(DESTDIR)/usr/share/ccsd/*

install-server:
	install -d -m755 -o root -g root \
		$(DESTDIR)/usr/share/ccsd/{templates,dbschema}
	install -m644 -o root -g root $(SERVER_MODULES) \
		$(DESTDIR)/usr/share/ccsd/crcnetd/modules/
	install -m644 -o root -g root dbschema/* \
		$(DESTDIR)/usr/share/ccsd/dbschema/
	cp -r templates/* $(DESTDIR)/usr/share/ccsd/templates/
	chown -R root: $(DESTDIR)/usr/share/ccsd/*
	

clean:
	@rm -f ccsd-private-r*.tar.{bz2,gz}
	@rm -f rurallink-r*.tar.{bz2,gz}
	@find . -name \*.pyc -exec rm {} \;

# Build release tarballs
release: clean
	@rm -f $(tmpdir)
	@mkdir -p $(tmpdir)
	@svn export . $(tmpdir)/ccsd-private-r$(r)
	@rm $(tmpdir)/ccsd-private-r$(r)/ccsd-old-repo.dmp.bz2
	@cd $(tmpdir); tar cjf $(pwd)/ccsd-private-r$(r).tar.bz2 \
		ccsd-private-r$(r)/
	@cd $(tmpdir); tar czf $(pwd)/ccsd-private-r$(r).tar.gz \
		ccsd-private-r$(r)/
	@rm -rf $(tmpdir)

# Build a rurallink release tarball
# Mainly composed of a normal public release tarball with server bits stripped
# + some private bits
rl-release: clean
	@rm -f $(tmpdir)
	@mkdir -p $(tmpdir)
	@svn export ../trunk $(tmpdir)/rurallink-r$(r)
	@sed 's/ccsd_revision=".*"/ccsd_revision="$(r)"/' < \
                $(tmpdir)/rurallink-r$(r)/crcnetd/version.py > \
                $(tmpdir)/rurallink-r$(r)/crcnetd/version.py.$$
	@mv $(tmpdir)/rurallink-r$(r)/crcnetd/version.py.$$ \
                $(tmpdir)/rurallink-r$(r)/crcnetd/version.py
	@cd $(tmpdir)/rurallink-r$(r); rm -rf dbschema
	@cd $(tmpdir)/rurallink-r$(r); rm -rf scripts
	@cd $(tmpdir)/rurallink-r$(r); rm -rf templates
	@cd $(tmpdir)/rurallink-r$(r); rm -rf services
	@cd $(tmpdir)/rurallink-r$(r); rm -f ccsd
	@cd $(tmpdir)/rurallink-r$(r); grep "CCSD_SERVER" crcnetd/modules/* | \
		cut -f1 -d':' | xargs rm -f
	@cd $(tmpdir)/rurallink-r$(r); rm -f crcnetd/modules/ccs_monitor_cpe.py
	@cd $(tmpdir)/rurallink-r$(r); rm -f crcnetd/_utils/ccsd_cfengine.py
	@cd $(tmpdir)/rurallink-r$(r); rm -f crcnetd/_utils/ccsd_server.py
	@cd $(tmpdir)/rurallink-r$(r); rm -f crcnetd/_utils/ccsd_service.py
	@cd $(tmpdir)/rurallink-r$(r); rm -f crcnetd/_utils/ccsd_session.py
	@cp resources/accounting.rule resources/rl_monitor.fw \
		$(tmpdir)/rurallink-r$(r)/resources/
	@cp modules/ccs_monitor_{rurallink,status}.py \
		$(tmpdir)/rurallink-r$(r)/crcnetd/modules/
	@cp resources/*.js $(tmpdir)/rurallink-r$(r)/resources
	@cp resources/rl*  $(tmpdir)/rurallink-r$(r)/resources
	@cp Makefile.rurallink $(tmpdir)/rurallink-r$(r)/Makefile
	@mv $(tmpdir)/rurallink-r$(r)/resources/rl-page.html \
		$(tmpdir)/rurallink-r$(r)/resources/page.html
	@mv $(tmpdir)/rurallink-r$(r)/resources/rl-styles.css \
		$(tmpdir)/rurallink-r$(r)/resources/styles.css
	@mv $(tmpdir)/rurallink-r$(r)/resources/rl-contact.html \
		$(tmpdir)/rurallink-r$(r)/resources/contact.html
	@cd $(tmpdir); tar cjf $(pwd)/rurallink-r$(r).tar.bz2 rurallink-r$(r)/
	@cd $(tmpdir); tar czf $(pwd)/rurallink-r$(r).tar.gz rurallink-r$(r)/
	@rm -rf $(tmpdir)

.PHONY: all install-server install-client clean release rl-release
