DEF=slidefactory.def
SIF=slidefactory.sif

ifndef PREFIX
	PREFIX=$(HOME)/.local
endif
INSTALL_BIN=$(PREFIX)/bin
INSTALL_GIT=$(PREFIX)/lib/slidefactory
GIT=https://github.com/csc-training/slide-template

.PHONY: build clean install uninstall

build: $(SIF)

clean:
	rm $(SIF)

install: build
	@if [ -e $(INSTALL_GIT) ]; then \
		echo "Already installed. Please run 'make uninstall' to remove old installation."; \
		exit 1; \
	fi
	@if [ ! -d $(INSTALL_BIN) ]; then \
		mkdir -p $(INSTALL_BIN); \
	fi
	cp $(SIF) $(INSTALL_BIN)/
	git clone $(GIT) $(INSTALL_GIT)
	@echo ""
	@echo "Installed:"
	@echo "  $(INSTALL_BIN)/$(SIF)"
	@echo "  $(INSTALL_GIT)/"

uninstall:
	@echo "Removing:"
	@echo "  $(INSTALL_BIN)/$(SIF)"
	@echo "  $(INSTALL_GIT)/"
	@read -r -p "Proceed [Y/n]? " OK; \
	[ "$$OK" = "y" ] || [ "$$OK" = "Y" ] || [ "$$OK" = "" ] || (exit 1;)
	rm -f $(INSTALL_BIN)/$(SIF)
	rm -rf $(INSTALL_GIT)

%.sif: %.def
	sudo singularity build $@ $<
