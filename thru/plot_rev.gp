set title "Throughput vs Network Size"
set xlabel "Number of nodes"
set ylabel "Throughput (ops/s)"
set grid
set key on
set term post eps
set output "thru_rev.eps"
plot "thru_rev-p.csv" using 1:(5/$3) title "Paxos" with points, \
     "thru_rev-o.csv" using 1:(5/$3) title "Database Op" with points, \
     "thru_rev-m.csv" using 1:(5/$3) title "Database Transaction" with points
#yerrorbars
