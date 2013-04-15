TARGETS = figs diss

.PHONY: figs diss

all: $(TARGETS)

figs:
	$(MAKE) -C lat
	$(MAKE) -C thru
	$(MAKE) -C start

diss:
	$(MAKE) -C diss
