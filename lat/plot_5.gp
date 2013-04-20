set title "Contention vs Latency with 5 nodes"
set xlabel "Number of writers"
set ylabel "Latency (s)"
set grid
set key on # change this later
set xtics 1
set term post eps
set output "lat_5.eps"
plot "lat_5-p.csv" using 1:2 title "Paxos" with points, \
     "lat_5-o.csv" using 1:2 title "Database Op" with points, \
     "lat_5-m.csv" using 1:2 title "Database Transaction" with points
#yerrorbars
