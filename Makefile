DEF=slidefactory.def
SIF=slidefactory.sif

ifndef PREFIX
	PREFIX=$(HOME)
endif
INSTALL_BIN=$(PREFIX)/bin
INSTALL_GIT=$(PREFIX)/lib/slidefactory
GIT=https://github.com/csc-training/slide-template

.PHONY: build clean install uninstall

build: $(SIF)

clean:
	rm $(SIF)

check:
	@if [ -e $(INSTALL_GIT) ]; then \
		echo "Already installed. Please run 'make uninstall' to remove old installation."; \
		exit 1; \
	fi

clone:
	git clone . $(INSTALL_GIT)
	cd $(INSTALL_GIT) && git remote set-url origin $(GIT) && git fetch origin

git:
	@make -s check
	@make -s clone
	@echo ""
	@echo "Installed:"
	@echo "  $(INSTALL_GIT)/"
	@echo ""
	@echo "Please add the following into your .bashrc or similar"
	@echo "  export SLIDEFACTORY=$(INSTALL_GIT)"

install: build
	@make -s check
	@if [ ! -d $(INSTALL_BIN) ]; then \
		mkdir -p $(INSTALL_BIN); \
	fi
	cp -i $(SIF) $(INSTALL_BIN)/
	@make -s clone
	@echo ""
	@echo "Installed:"
	@echo "  $(INSTALL_BIN)/$(SIF)"
	@echo "  $(INSTALL_GIT)/"
	@echo ""
	@echo "Please add the following into your .bashrc or similar"
	@echo "  export SLIDEFACTORY=$(INSTALL_GIT)"

uninstall:
	@echo "Removing:"
	@if [ -e $(INSTALL_BIN)/$(SIF) ]; then \
		echo "  $(INSTALL_BIN)/$(SIF)"; \
	fi
	@echo "  $(INSTALL_GIT)/"
	@read -r -p "Proceed [Y/n]? " OK; \
	[ "$$OK" = "y" ] || [ "$$OK" = "Y" ] || [ "$$OK" = "" ] || (exit 1;)
	@if [ -e $(INSTALL_BIN)/$(SIF) ]; then \
		rm -f $(INSTALL_BIN)/$(SIF); \
	fi
	rm -rf $(INSTALL_GIT)

%.sif: %.def
	sudo singularity build $@ $<
