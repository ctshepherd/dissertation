for x in *.csv; do
	start=`python <<EOF
tool, metric, node, ops, run = "$x".split(".")[0].split("_")
print "%s,%s,%s,%s," % (metric, node[1:], ops[1:], run[1:])
EOF`
	sed -i "s/^/$start/" $x
done
