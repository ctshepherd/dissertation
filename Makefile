TARGETS = figs diss

.PHONY: figs diss

all: $(TARGETS)

figs:
	$(MAKE) -C lat
	$(MAKE) -C thru

diss:
	$(MAKE) -C diss
