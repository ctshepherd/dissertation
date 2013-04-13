set title "Contention vs Throughput with 5 nodes"
set xlabel "Number of writers"
set ylabel "Throughput (ops/s)"
set grid
set key on # change this later
set xtics 1
set term post eps
set output "thru_5.eps"
plot "thru_5-p.csv" using 1:(5/$2) title "Paxos" with linespoints, \
     "thru_5-o.csv" using 1:(5/$2) title "Database Op" with linespoints, \
     "thru_5-m.csv" using 1:(5/$2) title "Database Transaction" with linespoints
#yerrorbars