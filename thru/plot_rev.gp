set title "Throughput vs Network Size"
set xlabel "Number of nodes"
set ylabel "Throughput (ops/s)"
set grid
set key on # change this later
set xtics 1
set term post eps
set output "thru_rev.eps"
plot "thru_rev-p.csv" using 1:(5/$2) title "Paxos" with linespoints, \
     "thru_rev-o.csv" using 1:(5/$2) title "Database Op" with linespoints, \
     "thru_rev-m.csv" using 1:(5/$2) title "Database Transaction" with linespoints
#yerrorbars
