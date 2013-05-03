load "../style.gp"

set title "The effect of churn on throughput in a network of 20 nodes"
set xlabel "Rate of churn (nodes/second)"
set ylabel "Throughput (s)"
set output "churn_thru.eps"
plot "churn_thru.csv" using 1:(1/$2) with points
