load "../style.gp"

set title "The effect of contention on latency in a network of 10 nodes"
set xlabel "Number of writers"
set ylabel "Latency (s)"
set xtics 1
set output "lat_10.eps"
plot "lat_10-p.csv" using 1:2 title "Paxos" with points, \
     "lat_10-o.csv" using 1:2 title "Database Op" with points, \
     "lat_10-m.csv" using 1:2 title "Database Transaction" with points
