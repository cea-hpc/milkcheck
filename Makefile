
NAME=milkcheck
VERSION=*
TARBALL=$(NAME)-$(VERSION).tar.gz
SPECFILE=$(NAME).spec
RPMTOPDIR=$$PWD/RPMBUILD
TESTDIR=$$PWD/tests
MANPAGE=doc/$(NAME).8
MANSOURCE=doc/$(NAME).asciidoc
DESTDIR=/
MANDIR=/usr/share/man
SYSCONFIGDIR=/etc
PYTHON=python

all: $(MANPAGE)
	$(PYTHON) setup.py build

install: all
	$(PYTHON) setup.py install -O1 --skip-build --root $(DESTDIR)
	# config files
	install -d $(DESTDIR)/$(SYSCONFIGDIR)/$(NAME)/conf/samples
	install -p -m 0644 conf/samples/*.yaml $(DESTDIR)/$(SYSCONFIGDIR)/$(NAME)/conf/samples
	install -d $(DESTDIR)/$(MANDIR)/man8/
	# doc files
	install -p -m 0644 doc/*.8 $(DESTDIR)/$(MANDIR)/man8/

version:
ifeq ($(VERSION),*)
	@echo "Please run 'make VERSION=x.y'"
	@exit 1
endif

$(RPMTOPDIR):
	mkdir -p $(RPMTOPDIR)/{BUILD,RPMS,SRPMS,SPECS}

rpm: version $(TARBALL) $(SPECFILE) $(RPMTOPDIR) $(MANPAGE)
	rpmbuild --define "_topdir $(RPMTOPDIR)" --define "_sourcedir $$PWD" -ba $(SPECFILE)

$(TARBALL): version
	git archive --prefix=$(NAME)-$(VERSION)/ HEAD conf/samples scripts lib doc setup.py Makefile | gzip -9 >$@

.PHONY: rpm clean all version test doc

clean:
	rm -f $(TARBALL)
	rm -rf $(RPMTOPDIR)

test:
	cd $(TESTDIR) ; nosetests --exe --all-modules

$(MANPAGE): $(MANSOURCE)
	a2x -f manpage $<

doc: $(MANPAGE)

