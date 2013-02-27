TOTAL=`detex diss.tex | tr -cd '0-9A-Za-z \n' | wc -w`
PROP=`detex proposal.tex | tr -cd '0-9A-Za-z \n' | wc -w`
echo $(($TOTAL-$PROP))
