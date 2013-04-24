load "../style.gp"

set title "Contention vs Throughput with 5 nodes"
set xlabel "Number of writers"
set ylabel "Throughput (ops/s)"
set xtics 1
set output "thru_5.eps"
plot "thru_5-p.csv" using 1:(5/$2) title "Paxos" with points, \
     "thru_5-o.csv" using 1:(5/$2) title "Database Op" with points, \
     "thru_5-m.csv" using 1:(5/$2) title "Database Transaction" with points
