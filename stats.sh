export PYTHONPATH="/home/cs648/dissertation"

mkdir -p csv/

# Thru - latency - paxos
# for metric in thru; do
# 	for node_num in `seq 2 10`; do
# 		for write_num in `seq 1 $node_num`; do
# 			res=$({ for run_number in `seq 1 5`; do
# 				bin/eval -m $metric -n $node_num -o 5 -D 5 -w $write_num -B paxos
# 			done } | python statistic.py)
# 			echo "$node_num,$write_num,$res"
# 		done
# 	done
# done

metric=thru
node_num=$1
#20 100; do
for mode in p o m; do
	for write_num in `seq 1 $node_num`; do
		res=$({ for run_number in `seq 1 5`; do
			bin/eval -m $metric -n $node_num -o 5 -D 5 -w $write_num -M $mode
		done } | python avg.py)
		echo "$node_num,$write_num,$mode,$res"
	done
done
