export PYTHONPATH="/home/cs648/dissertation"

EVAL=../bin/eval
AVG=../avg.py

metric=thru
write_num=1
for mode in p o m; do
	for node_num in 2 3 4 5 10 15 20 25 30 40 50; do
		res=$({ for run_number in `seq 1 5`; do
			$EVAL -m $metric -n $node_num -o 5 -D 5 -w $write_num -M $mode -P 30000
		done } | python $AVG)
		echo "$node_num,$write_num,$mode,$res"
	done
done
