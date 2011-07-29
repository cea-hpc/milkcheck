
NAME=milkcheck
VERSION=*
TARBALL=$(NAME)-$(VERSION).tar.gz
SPECFILE=$(NAME).spec
RPMTOPDIR=$$PWD/RPMBUILD

all: rpm

version:
ifeq ($(VERSION),*)
	@echo "Please run 'make VERSION=x.y'"
	@exit 1
endif

$(RPMTOPDIR):
	mkdir -p $(RPMTOPDIR)/{BUILD,RPMS,SRPMS,SPECS}

rpm: version $(TARBALL) $(SPECFILE) $(RPMTOPDIR)
	rpmbuild --define "_topdir $(RPMTOPDIR)" --define "_sourcedir $$PWD" --define "version $(VERSION)" -ba $(SPECFILE)

$(TARBALL): version
	git archive --prefix=$(NAME)-$(VERSION)/ HEAD conf/samples scripts lib setup.py | gzip -9 >$@
#	VERSION=$(VERSION) ./setup.py sdist -d .

.PHONY: rpm clean all version

clean:
	rm -f $(TARBALL)
	rm -rf $(RPMTOPDIR)
