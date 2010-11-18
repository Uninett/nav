##
## Makefile for NAV's Java subsystems
## 
include $(top_srcdir)/common.mk

INSTALLARGS = -DDESTDIR=$(DESTDIR)

subdirs = \
	Util \
	ConfigParser \
	Database \
	Event \
	eventEngine \
	getBoksMacs \
	networkDiscovery \
	Logger \
	NetboxInfo \
	SimpleSnmp \
	Netmap

EDITFILES = \
	build.properties \
	eventEngine/eventEngine.sh \
	eventEngine/eventengine \
	getBoksMacs/getBoksMacs.sh \
	getBoksMacs/mactrace \
	networkDiscovery/networkDiscovery \
	networkDiscovery/networkDiscovery.sh

# We build our own classpath, to resolve interdependencies between the java modules.
CLASSPATH = $(shell for x in $(subdirs); do echo -n "$$PWD/$${x}/build:"; done ; echo -n $$CLASSPATH)
INSTALL_TARGETS = $(patsubst %,%_inst,$(subdirs))
QUICK_TARGETS = $(patsubst %,%_q,$(subdirs))

# Make sure we export make variables to the environment
export
.PHONY = debug .lastbuild $(INSTALL_TARGETS) $(QUICK_TARGETS)

all-local: $(EDITFILES) $(subdirs)

$(subdirs): .lastbuild
	@echo "Building $@ ..."
	(cd $@ && $(ANT) $(BUILDARGS)) && touch $@

# Describe interdependencies here:
ConfigParser:
Database: Logger
Event: Database Logger
eventEngine: ConfigParser Database Event Logger
getBoksMacs: ConfigParser Database Event Logger NetboxInfo SimpleSnmp
networkDiscovery: ConfigParser Database Event Logger NetboxInfo
Logger: ConfigParser Util
NetboxInfo: Database Event Logger
SimpleSnmp: Database Logger
Util:

.lastbuild:
# Do absolutely nothing, just let ANT decide whether a rebuild is necessary

install-exec-local:
	@for dir in $(subdirs); do \
	  echo "Installing $$dir ..."; \
	  (cd $$dir && $(ANT) install $(INSTALLARGS)) || exit 1; \
	done

clean-local:
	rm -f *~ .lastbuild
	@for dir in $(subdirs); do \
	  echo "Entering $$dir ..."; \
	  (cd $$dir && $(ANT) clean) || exit 1; \
	done

distclean-local:
	@echo Target distclean is not properly supported in the java projects, since they are built using ant.

# Debug target just prints some debug information from the Makefile
debug:
	@echo Classpath:
	@echo $$CLASSPATH
	@echo 
	@echo INSTALL_TARGETS:
	@echo $(INSTALL_TARGETS)

$(INSTALL_TARGETS):
	@dir="$(patsubst %_inst,%,$@)";  \
	echo "Installing $$dir ..."; \
	cd $$dir && $(ANT) install $(INSTALLARGS)

$(QUICK_TARGETS):
	@realtarget="$(patsubst %_q,%,$@)";                            \
	echo "Building $$realtarget ..." ;                             \
	(cd $$realtarget && $(ANT) $(BUILDARGS)) && touch $$realtarget

install-data-local: installdirs

installdirs:
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/log/eventEngine
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/log/networkDiscovery

