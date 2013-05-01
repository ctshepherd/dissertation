load "../style.gp"

set title "Latency vs Churn"
set xlabel "Rate of churn (nodes seconds)"
set ylabel "Latency (s)"
set output "churn_lat.eps"
plot "churn_lat.csv" using 1:2 title "Churn" with points
