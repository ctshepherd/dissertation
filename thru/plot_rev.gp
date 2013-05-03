load "../style.gp"

set title "The effect of network size on throughput"
set xlabel "Number of nodes"
set ylabel "Throughput (ops/s)"
set output "thru_rev.eps"
plot "thru_rev-p.csv" using 1:(5/$3) title "Paxos" with points, \
     "thru_rev-o.csv" using 1:(5/$3) title "Database Op" with points, \
     "thru_rev-m.csv" using 1:(5/$3) title "Database Transaction" with points
