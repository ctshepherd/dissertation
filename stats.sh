export PYTHONPATH="/home/cs648/dissertation"

for node_num in 2 3 4 5 10 15 20 25 30 40 50 60 70 80 90 100; do
	for op_num in `seq 1 10`; do
		for run_number in `seq 1 10`; do
			echo "Nodes: $node_num Ops: $op_num Run: $run_number"
			END=n${node_num}_o${op_num}_r${run_number}
			time bin/peval -m lat -n $node_num -o $op_num -D 5 -f csv/peval_lat_$END.csv >/tmp/output_$END
			echo
		done
	done
done
