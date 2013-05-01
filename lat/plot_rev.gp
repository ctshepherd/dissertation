load "../style.gp"

set title "Latency vs Network Size"
set xlabel "Number of nodes"
set ylabel "Latency (s)"
set output "lat_rev.eps"
plot "lat_rev-p.csv" using 1:2 title "Paxos" with points, \
     "lat_rev-o.csv" using 1:2 title "Database Op" with points, \
     "lat_rev-m.csv" using 1:2 title "Database Transaction" with points
