load "../style.gp"

set title "The effect of contention on throughput in a network of 10 nodes"
set xlabel "Number of writers"
set ylabel "Throughput (ops/s)"
set xtics 1
set output "thru_10.eps"
plot "thru_10-p.csv" using 1:(5/$2) title "Paxos" with points, \
     "thru_10-o.csv" using 1:(5/$2) title "Database Op" with points, \
     "thru_10-m.csv" using 1:(5/$2) title "Database Transaction" with points
