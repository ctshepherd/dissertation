# This is the Makefile for the demonstration dissertation
# written by Martin Richards
#
# Note that continuation lines require '\'
# and that TAB is used after ':' and before unix commands.

FIGS = figs/op-log.eps \
       figs/op-log-trylock.eps \
       figs/proposer-state-machine.eps \
       figs/paxos-msg-flow-duelling.eps \
       figs/paxos-msg-flow-one-acceptor-fail.eps \
       figs/paxos-msg-flow-usual.eps \
       figs/paxos-msg-flow-partition.eps \
       figs/op-log-slow-read-1.eps \
       figs/op-log-slow-read-2.eps \
       figs/module-layout.eps \
       figs/two-pc.eps \
       figs/three-pc.eps \
       figs/where-ast.eps \
       figs/thru_10.eps \
       figs/thru_20.eps \
       figs/thru_rev.eps \
       figs/lat_10.eps \
       figs/lat_20.eps \
       figs/lat_rev.eps \
       figs/lat_nack.eps \
       figs/churn_lat.eps \
       figs/churn_thru.eps \
       figs/start.eps

DISS = diss.tex \
       refs.bib \
       propbody.tex \
       $(FIGS)

PROP = proposal.tex propbody.tex

pub: /home/cs648/public_html/diss.pdf

/home/cs648/public_html/diss.pdf:	diss.pdf
	cp diss.pdf ~/public_html/

prop:	proposal.dvi proposal.pdf
	cp proposal.pdf ~/public_html/

diss.ps:	$(DISS)
	latex diss
	bibtex diss
	latex diss
	bibtex diss
	latex diss
	bibtex diss
	dvips -Ppdf -G0 -t a4 -pp 0-200 -o diss.ps diss.dvi

diss.pdf:	diss.ps
	ps2pdf diss.ps

proposal.ps:	$(PROP)
	latex proposal
	dvips -Ppdf -G0 -t a4 -pp 0-200 -o proposal.ps proposal.dvi

proposal.pdf:	proposal.ps
	ps2pdf proposal.ps

propcount:
	detex proposal.tex | tr -cd '0-9A-Za-z \n' | wc -w

count:
	@echo -n "Wordcount: "
	@bash count.sh

proposal.dvi: $(PROP)
	latex proposal

all:	proposal.dvi diss.ps

clean:
	rm -f diss.ps *.dvi *.aux *.log *.err
	rm -f core *~ *.lof *.toc *.blg *.bbl
	rm -f proposal.pdf diss.pdf

gv:	diss.ps
	ghostview diss.ps

gs:	diss.ps
	gs diss.ps

pr:	diss.ps
	lpr diss.ps
