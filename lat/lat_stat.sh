export PYTHONPATH="/home/cs648/dissertation"

EVAL=../bin/eval
AVG=../avg.py

metric=lat
node_num=$1
for mode in o m; do
	for write_num in `seq 1 12`; do
		res=$({ for run_number in `seq 1 5`; do
			$EVAL -m $metric -n $node_num -o 5 -D 5 -w $write_num -M $mode
		done } | python $AVG)
		echo "$write_num,$mode,$res"
	done
done
