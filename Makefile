
NAME=milkcheck
VERSION=0.11
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
VIMDATADIR=/usr/share/vim/vimfiles

all: $(MANPAGE)
	$(PYTHON) setup.py build

install: all
	$(PYTHON) setup.py install -O1 --skip-build --root $(DESTDIR)
	# config files
	install -d $(DESTDIR)/$(SYSCONFIGDIR)/$(NAME)/conf/samples
	install -p -m 0644 conf/milkcheck.conf $(DESTDIR)/$(SYSCONFIGDIR)/$(NAME)
	install -p -m 0644 conf/samples/*.yaml $(DESTDIR)/$(SYSCONFIGDIR)/$(NAME)/conf/samples
	install -d $(DESTDIR)/$(MANDIR)/man8/
	# doc files
	install -p -m 0644 doc/*.8 $(DESTDIR)/$(MANDIR)/man8/
	# vim files
	install -d $(DESTDIR)/$(VIMDATADIR)/{ftdetect,syntax}
	install -p -m 0644 doc/vim/ftdetect/milkcheck.vim $(DESTDIR)/$(VIMDATADIR)/ftdetect
	install -p -m 0644 doc/vim/syntax/milkcheck.vim $(DESTDIR)/$(VIMDATADIR)/syntax

$(RPMTOPDIR):
	mkdir -p $(RPMTOPDIR)/{BUILD,RPMS,SRPMS,SPECS}

rpm: $(TARBALL) $(SPECFILE) $(RPMTOPDIR) $(MANPAGE)
	rpmbuild --define "_topdir $(RPMTOPDIR)" --define "_sourcedir $$PWD" -ba $(SPECFILE)

$(TARBALL):
	git archive --prefix=$(NAME)-$(VERSION)/ HEAD | gzip -9 >$@

.PHONY: rpm clean all test doc

clean:
	rm -f $(TARBALL)
	rm -rf $(RPMTOPDIR)

test:
	export PYTHONPATH=$$PWD/lib/ ; nosetests --exe --all-modules -w tests

$(MANPAGE): $(MANSOURCE)
	a2x -f manpage $<

doc: $(MANPAGE)

