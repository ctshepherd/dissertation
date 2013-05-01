TARGETS = figs diss

.PHONY: figs diss count

all: $(TARGETS)

figs:
	$(MAKE) -C lat
	$(MAKE) -C thru
	$(MAKE) -C start
	$(MAKE) -C churn

diss:
	$(MAKE) -C diss

count:
	$(MAKE) -C diss count
