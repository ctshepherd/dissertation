all: start.eps start2.eps

start.eps: plot.gp start.csv
	gnuplot plot.gp
	cp start.eps ../diss/figs/

start2.eps: plot2.gp start2.csv
	gnuplot plot2.gp
	cp start2.eps ../diss/figs/
