"""
General utilities for the whole thing
"""
import numpy as np

def swap(a,idx1,idx2):
	temp = a[idx1]
	a[idx1] = a[idx2]
	a[idx2] = temp

def partition(a,low,high,comp):
	pivotIdx = np.random.choice(list(range(low,high)))
	pivot = a[pivotIdx]
	swap(a,pivotIdx,-1)
	j = low
	for i in range(low,high - 1):
		if comp(a[i],pivot):
			swap(a,i,j)
			j+=1

	swap(a,j,-1)
	return pivotIdx

def ssort_rec(a,low,high,level,maxlevel,comp):
	if level == maxlevel:
		return

	q = partition(a,low,high,comp)
	ssort_rec(a,low,q,level+1,maxlevel,comp)
	ssort_rec(a,q+1,high,level+1,maxlevel,comp)

"""
"stochastic sort" which gives only stochastic preference to individuals with extreme values

comp function defines how to compare two elements. this one gives "descending" order, but x < y would do ascending eg.
"""
def stoch_sort(a,levels=1,comp = lambda x,y: x > y):
	if levels == 0:
		aa = np.array(a)
		np.random.shuffle(aa)
		return list(aa)#shuffle instead of sort
	ssort_rec(a,0,len(a),0,levels,comp)