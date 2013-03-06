export PYTHONPATH="/home/cs648/dissertation"

#for transaction_number in 50 500 5000; do
for transaction_number in 50; do
	for run_number in `seq 1 10`; do
		prefix="${transaction_number}:${run_number}:"
		log_prefix="${transaction_number}_${run_number}"
		echo $prefix
		date >logs/peval_${log_prefix}.log
		date >logs/pserv_${log_prefix}.log
		bin/pserv &>>logs/pserv_${log_prefix}.log &
		bin/peval --amount ${transaction_number} -b 10000 -p 10001 -D 3 &>>logs/peval_${log_prefix}.log
		kill $!
		sleep 1
		echo
	done
done
