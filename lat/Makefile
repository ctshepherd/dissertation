all: lat_5.eps lat_20.eps lat_rev.eps

lat_5.eps: lat_5.csv plot_5.gp ../style.gp
	#chmod -f +w *-*.csv
	for x in p o m; do sed -n "/$$x/p" lat_5.csv >lat_5-$$x.csv; done
	for x in p o m; do sed -i -e "s/$$x,//" lat_5-$$x.csv; done
	sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_5.gp
	cp lat_5.eps ../diss/figs/

lat_20.eps: lat_20.csv plot_20.gp ../style.gp
	chmod -f +w *-*.csv
	for x in p o m; do sed -n "/$$x/p" lat_20.csv >lat_20-$$x.csv; done
	for x in p o m; do sed -i -e "s/$$x,//" lat_20-$$x.csv; done
	sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_20.gp
	cp lat_20.eps ../diss/figs/

lat_rev.eps: lat_rev.csv plot_rev.gp ../style.gp
	# chmod -f +w *-*.csv
	# for x in p o m; do sed -n "/$$x/p" lat_rev.csv >lat_rev-$$x.csv; done
	# for x in p o m; do sed -i -e "s/$$x,//" lat_rev-$$x.csv; done
	# sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_rev.gp
	cp lat_rev.eps ../diss/figs/
