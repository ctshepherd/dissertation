load "../style.gp"

set title "Start up cost"
set xlabel "Number of nodes"
set ylabel "Bandwidth (Mb)"
set output "start.eps"
plot "start.csv" using 1:($2/1000000) title "Old" with points, \
     "start2.csv" using 1:($2/1000000) title "New" with points
