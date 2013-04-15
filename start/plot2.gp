set title "Start up cost"
set xlabel "Number of nodes"
set ylabel "Bandwidth (bytes)"
set grid
set key on
set term post eps
set output "start2.eps"
plot "start2.csv" using 1:3 title "Average" with linespoints, \
     "start2.csv" using 1:2 title "Maximum" with linespoints
