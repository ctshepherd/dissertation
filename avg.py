from sys import stdin
import math

def average(s):
    return sum(s) * 1.0 / len(s)

def stddev(s):
    avg = average(s)
    return math.sqrt(average(map(lambda x: (x - avg)**2, s)))

s = [float(x) for x in (' '.join(stdin.readlines())).split()]
print "%s,%s" % (average(s), stddev(s))
