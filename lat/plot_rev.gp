set title "Contention vs Latency with 20 nodes"
set xlabel "Number of writers"
set ylabel "Latency (s)"
set grid
set key on
set term post eps
set output "lat_rev.eps"
plot "lat_rev-p.csv" using 1:2 title "Paxos" with linespoints, \
     "lat_rev-o.csv" using 1:2 title "Database Op" with linespoints, \
     "lat_rev-m.csv" using 1:2 title "Database Transaction" with linespoints
#yerrorbars
