#!/bin/env python

# quick script to generate every fortnightly friday from start of dissertation until some time in
# the summer
# http://stackoverflow.com/questions/2295765/generating-recurring-dates-using-python
import dateutil.rrule as dr
import dateutil.parser as dp
import dateutil.relativedelta as drel
from itertools import izip

start=dp.parse("19/10/2012")
frr = dr.rrule(dr.WEEKLY, interval=2, byweekday=drel.FR,dtstart=start, count=20)
trr = dr.rrule(dr.WEEKLY, interval=2, byweekday=drel.TH,dtstart=start, count=20)

for dt,df in izip(frr, trr):
    print "%s-%s" % (dt.strftime("%d/%m/%Y"), df.strftime("%d/%m/%Y"))
