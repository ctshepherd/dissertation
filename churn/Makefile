all: churn_lat.eps churn_thru.eps

churn_lat.eps: plot_lat.gp churn_lat.csv ../style.gp
	gnuplot plot_lat.gp
	cp churn_lat.eps ../diss/figs/

churn_thru.eps: plot_thru.gp churn_thru.csv ../style.gp
	gnuplot plot_thru.gp
	cp churn_thru.eps ../diss/figs/
