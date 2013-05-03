load "../style.gp"

set title "How different start up implementations affect the initial bandwidth usage"
set xlabel "Number of nodes"
set ylabel "Bandwidth (Mb)"
set output "start.eps"
plot "start.csv" using 1:($2/1000000) title "Peer-to-peer model" with points, \
     "start2.csv" using 1:($2/1000000) title "Centralised model" with points
