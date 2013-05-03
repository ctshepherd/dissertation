all: lat_10.eps lat_20.eps lat_rev.eps lat_nack.eps

lat_10.eps: lat_10.csv plot_10.gp ../style.gp
	chmod -f +w *-*.csv
	for x in p o m; do sed -n "/$$x/p" lat_10.csv >lat_10-$$x.csv; done
	for x in p o m; do sed -i -e "s/$$x,//" lat_10-$$x.csv; done
	sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_10.gp
	cp lat_10.eps ../diss/figs/

lat_20.eps: lat_20.csv plot_20.gp ../style.gp
	chmod -f +w *-*.csv
	for x in p o m; do sed -n "/$$x/p" lat_20.csv >lat_20-$$x.csv; done
	for x in p o m; do sed -i -e "s/$$x,//" lat_20-$$x.csv; done
	sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_20.gp
	cp lat_20.eps ../diss/figs/

lat_rev.eps: plot_rev.gp ../style.gp
	# chmod -f +w *-*.csv
	# for x in p o m; do sed -n "/$$x/p" lat_rev.csv >lat_rev-$$x.csv; done
	# for x in p o m; do sed -i -e "s/$$x,//" lat_rev-$$x.csv; done
	# sed -i -e 's/,/\t/g' *-*.csv
	gnuplot plot_rev.gp
	cp lat_rev.eps ../diss/figs/

lat_nack.eps: lat_n0.csv lat_n1.csv lat_n2.csv plot_nack.gp ../style.gp
	gnuplot plot_nack.gp
	cp lat_nack.eps ../diss/figs/
