lat_5.eps: lat_5.csv plot_5.gp
	chmod +w *-*.csv
	for x in p o m; do sed -n "/$$x/p" lat_5.csv >lat_5-$$x.csv; done
	for x in p o m; do sed -i -e "s/$$x,//" lat_5-$$x.csv; done
	sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_5.gp
	cp lat_5.eps ../diss/figs/
