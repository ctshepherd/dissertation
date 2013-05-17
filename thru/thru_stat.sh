export PYTHONPATH="/home/cs648/dissertation"

EVAL=../bin/eval
AVG=../avg.py

metric=thru
node_num=$1
#20 100; do
for mode in p o m; do
	for write_num in `seq 1 12`; do
		res=$({ for run_number in `seq 1 5`; do
			$EVAL -m $metric -n $node_num -o 5 -D 5 -w $write_num -M $mode -P 20000
		done } | python $AVG)
		echo "$node_num,$write_num,$mode,$res"
	done
done
