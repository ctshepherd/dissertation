set title "Contention vs Throughput with 20 nodes"
set xlabel "Number of writers"
set ylabel "Throughput (ops/s)"
set grid
set key on # change this later
set xtics 1
set term post eps
set output "thru_20.eps"
plot "thru_20-p.csv" using 1:(20/$2) title "Paxos" with linespoints, \
     "thru_20-o.csv" using 1:(20/$2) title "Database Op" with linespoints, \
     "thru_20-m.csv" using 1:(20/$2) title "Database Transaction" with linespoints
#yerrorbars
