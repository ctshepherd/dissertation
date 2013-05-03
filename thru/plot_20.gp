load "../style.gp"

set title "The effect of contention on throughput in a network of 20 nodes"
set xlabel "Number of writers"
set ylabel "Throughput (ops/s)"
set xtics 1
set output "thru_20.eps"
plot "thru_20-p.csv" using 1:(20/$2) title "Paxos" with points, \
     "thru_20-o.csv" using 1:(20/$2) title "Database Op" with points, \
     "thru_20-m.csv" using 1:(20/$2) title "Database Transaction" with points
