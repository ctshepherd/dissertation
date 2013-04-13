all: thru_5.eps thru_20.eps thru_rev.eps

thru_5.eps: thru_5.csv plot_5.gp
	chmod +w *-*.csv
	for x in p o m; do sed -n "/$$x/p" thru_5.csv >thru_5-$$x.csv; done
	for x in p o m; do sed -i -e "s/$$x,//" thru_5-$$x.csv; done
	sed -i -e "s/5,//" thru_5-*.csv
	sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_5.gp
	cp thru_5.eps ../diss/figs/

thru_20.eps: thru_20.csv plot_20.gp
	chmod +w *-*.csv
	for x in p o m; do sed -n "/$$x/p" thru_20.csv >thru_20-$$x.csv; done
	for x in p o m; do sed -i -e "s/$$x,//" thru_20-$$x.csv; done
	sed -i -e "s/20,//" thru_20-*.csv
	sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_20.gp
	cp thru_20.eps ../diss/figs/

thru_rev.eps: thru_rev.csv plot_rev.gp
	chmod +w *-*.csv
	for x in p o m; do sed -n "/$$x/p" thru_rev.csv >thru_rev-$$x.csv; done
	for x in p o m; do sed -i -e "s/$$x,//" thru_rev-$$x.csv; done
	sed -i -e "s/rev,//" thru_rev-*.csv
	sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_rev.gp
	cp thru_rev.eps ../diss/figs/
