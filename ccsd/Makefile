r := $(shell svnversion -nc .. | sed -e 's/^[^:]*://;s/[A-Za-z]//')
tmpdir := $(shell mktemp -ud)
pwd := $(shell pwd)

COMMON_UTILS=crcnetd/_utils/ccsd_{common,config,events,log}.py \
			 crcnetd/_utils/__init__.py crcnetd/_utils/ccsd_daemon.py
COMMON_MODULES=crcnetd/modules/__init__.py

# Modules that should be installed for the client
CLIENT_MODULES := $(COMMON_MODULES) \
	$(shell grep "CCSD_CLIENT" crcnetd/modules/* | cut -f1 -d':' | xargs)
CLIENT_UTILS=$(COMMON_UTILS) crcnetd/_utils/ccsd_clientserver.py \
			 crcnetd/_utils/interfaces.py crcnetd/_utils/dhcpd.py \
			 crcnetd/_utils/ccsd_tc.py

# Modules that should be installed for the server
SERVER_MODULES := $(COMMON_MODULES) \
	$(shell grep "CCSD_SERVER" crcnetd/modules/* | cut -f1 -d':' | xargs)
SERVER_UTILS=$(COMMON_UTILS) \
			 crcnetd/_utils/ccsd_{ca,cfengine,email,server,service,session}.py

all:

install-client:
	install -d -m755 -o amiral -g amiral \
		$(DESTDIR)/usr/share/ccsd/{crcnetd,resources}
	install -d -m755 -o amiral -g amiral \
		$(DESTDIR)/usr/share/ccsd/crcnetd/{_utils,modules}
	install -m644 -o amiral -g amiral crcnetd/*.py \
		$(DESTDIR)/usr/share/ccsd/crcnetd/
	install -m644 -o amiral -g amiral $(CLIENT_MODULES) \
		$(DESTDIR)/usr/share/ccsd/crcnetd/modules/
	install -m644 -o amiral -g amiral $(CLIENT_UTILS) \
		$(DESTDIR)/usr/share/ccsd/crcnetd/_utils/
	install -m644 -o amiral -g amiral resources/* \
		$(DESTDIR)/usr/share/ccsd/resources/
	install -d -m755 -o amiral -g amiral $(DESTDIR)/usr/share/doc/ccsd/
	install -m644 -o amiral -g amiral docs/* $(DESTDIR)/usr/share/doc/ccsd/
	install -d -m755 -o amiral -g amiral $(DESTDIR)/usr/sbin/
	install -m755 -o amiral -g amiral crcnet-monitor \
		$(DESTDIR)/usr/sbin/crcnet-monitor

install-server:
	install -d -m755 -o amiral -g amiral \
		$(DESTDIR)/usr/share/ccsd/{crcnetd,templates,dbschema}
	install -d -m755 -o amiral -g amiral \
		$(DESTDIR)/usr/share/ccsd/crcnetd/{_utils,modules}
	install -m644 -o amiral -g amiral crcnetd/*.py \
		$(DESTDIR)/usr/share/ccsd/crcnetd/
	install -m644 -o amiral -g amiral $(SERVER_MODULES) \
		$(DESTDIR)/usr/share/ccsd/crcnetd/modules/
	install -m644 -o amiral -g amiral $(SERVER_UTILS) \
		$(DESTDIR)/usr/share/ccsd/crcnetd/_utils/
	install -m644 -o amiral -g amiral dbschema/* \
		$(DESTDIR)/usr/share/ccsd/dbschema/
	install -d -m755 -o amiral -g amiral $(DESTDIR)/usr/share/doc/ccsd/
	install -m644 -o amiral -g amiral docs/* $(DESTDIR)/usr/share/doc/ccsd/
	install -d -m755 -o amiral -g amiral $(DESTDIR)/usr/sbin/
	install -m755 -o amiral -g amiral ccsd $(DESTDIR)/usr/sbin/ccsd

uninstall:
	rm -rf /usr/sbin/ccsd /usr/share/ccsd/ /usr/share/doc/ccsd/
	
clean:
	@rm -f ccsd-r*.tar.{bz2,gz}
	@find . -name \*.pyc -exec rm {} \;

# Build release tarballs
release: clean
	@rm -f $(tmpdir)
	@mkdir -p $(tmpdir)
	@svn export . $(tmpdir)/ccsd-r$(r)
	@sed 's/ccsd_revision=".*"/ccsd_revision="$(r)"/' < \
		$(tmpdir)/ccsd-r$(r)/crcnetd/version.py > \
		$(tmpdir)/ccsd-r$(r)/crcnetd/version.py.$$
	@mv $(tmpdir)/ccsd-r$(r)/crcnetd/version.py.$$ \
		$(tmpdir)/ccsd-r$(r)/crcnetd/version.py
	@cd $(tmpdir); tar cjf $(pwd)/ccsd-r$(r).tar.bz2 ccsd-r$(r)/
	@cd $(tmpdir); tar czf $(pwd)/ccsd-r$(r).tar.gz ccsd-r$(r)/
	@rm -rf $(tmpdir)

.PHONY: clean release install-server install-client
