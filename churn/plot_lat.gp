load "../style.gp"

set title "The effect of churn on latency in a network of 20 nodes"
set xlabel "Rate of churn (nodes/second)"
set ylabel "Latency (s)"
set output "churn_lat.eps"
plot "churn_lat.csv" using 1:2 with points
