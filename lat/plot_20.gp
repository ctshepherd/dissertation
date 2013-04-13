load "../style.gp"

set title "Contention vs Latency with 20 nodes"
set xlabel "Number of writers"
set ylabel "Latency (s)"
set grid
set key on # change this later
set xtics 1
set output "lat_20.eps"
plot "lat_20-p.csv" using 1:2 title "Paxos" with linespoints, \
     "lat_20-o.csv" using 1:2 title "Database Op" with linespoints, \
     "lat_20-m.csv" using 1:2 title "Database Transaction" with linespoints
#yerrorbars
