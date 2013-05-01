load "../style.gp"

set title "Throughput vs Churn"
set xlabel "Rate of churn (nodes seconds)"
set ylabel "Throughput (s)"
set output "churn_thru.eps"
plot "churn_thru.csv" using 1:2 title "Churn" with points
