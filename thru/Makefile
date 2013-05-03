all: thru_10.eps thru_20.eps thru_rev.eps

thru_10.eps: thru_10.csv plot_10.gp ../style.gp
	chmod -f +w *-*.csv
	for x in p o m; do sed -n "/$$x/p" thru_10.csv >thru_10-$$x.csv; done
	for x in p o m; do sed -i -e "s/$$x,//" thru_10-$$x.csv; done
	sed -i -e "s/10,//" thru_10-*.csv
	sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_10.gp
	cp thru_10.eps ../diss/figs/

thru_20.eps: thru_20.csv plot_20.gp ../style.gp
	chmod -f +w *-*.csv
	for x in p o m; do sed -n "/$$x/p" thru_20.csv >thru_20-$$x.csv; done
	for x in p o m; do sed -i -e "s/$$x,//" thru_20-$$x.csv; done
	sed -i -e "s/20,//" thru_20-*.csv
	sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_20.gp
	cp thru_20.eps ../diss/figs/

thru_rev.eps: thru_rev.csv plot_rev.gp ../style.gp
	chmod -f +w *-*.csv
	for x in p o m; do sed -n "/$$x/p" thru_rev.csv >thru_rev-$$x.csv; done
	for x in p o m; do sed -i -e "s/$$x,//" thru_rev-$$x.csv; done
	sed -i -e "s/rev,//" thru_rev-*.csv
	sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_rev.gp
	cp thru_rev.eps ../diss/figs/
