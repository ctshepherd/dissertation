load "../style.gp"

set title "Contention vs Latency with 20 nodes"
set xlabel "Number of writers"
set ylabel "Latency (s)"
set output "lat_nack.eps"
plot "lat_n0.csv" using 1:2 title "Without NACKs" with points, \
     "lat_n1.csv" using 1:2 title "With NACKs Version 1" with points, \
     "lat_n2.csv" using 1:2 title "With NACKs Version 2" with points
