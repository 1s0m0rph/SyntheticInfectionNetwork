"""
General utilities for the whole thing
"""
import numpy as np

TIME_STEPS_PER_DAY = 1440#for minutes
PROBABILITY_TRAVEL_SOMEWHERE = 0.2#per time step, what is the baseline probability that someone decides to go somewhere
AVERAGE_HOME_IDLE_TIME = 60#time steps. the average amount of time someone will spend idle at home before going somewhere
SSORT_LEVELS = 0#how many levels of quicksort partition should I apply to get the affinity order

DISEASE_STATES = {'S','II','IS','R','V'}#Susceptible; Infected, Infectious; Infected, showing Symptoms; Recovered; Vaccinated

HANDWASH_EFFECT_MODIFIERS = [[0.,-0.1],
							 [-0.1,-0.5]]#modifiers for infectivity, given that (a,b) washed their hands

INTIMATE_EFFECT_MODIFIER = 0.2#how much more infectious things tend to be when people are intimate with infecteds

#TODO: move to the actual simulation part
diseases_active = {0:None}#mapping of disease id to the actual disease object

def swap(a,idx1,idx2):
	temp = a[idx1]
	a[idx1] = a[idx2]
	a[idx2] = temp

def partition(a,low,high,comp):
	pivotIdx = np.random.choice(list(range(low,high)))
	pivot = a[pivotIdx]
	swap(a,pivotIdx,high-1)
	j = low
	for i in range(low,high - 1):
		if comp(a[i],pivot):
			swap(a,i,j)
			j+=1

	swap(a,j,high-1)
	return j

def ssort_rec(a,low,high,level,maxlevel,comp):
	if level >= maxlevel:
		return
	if low >= high:
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
		return [list(x) for x in aa]#shuffle instead of sort
	else:
		aa = a.copy()
		ssort_rec(aa,0,len(aa),0,levels,comp)
		return aa


"""
Combine these probabilities into a unified one depending on given weights which should sum to 1 in general
"""
def weighted_prob_combination(p1,w1,p2,w2):
	return p1*w1 + p2*w2

def coinflip(p):
	return np.random.choice([True,False],p=[p,1-p])


"""
manhattan distance (aka 1-norm) between (x0,x1,...) and (y0,y1,...)
"""
def manhattan_distance(x,y):
	r = 0
	for xi,yi in zip(x,y):
		r += abs(xi - yi)
	return r

"""
euclidean distance (aka 2-norm) between x and y
"""
def eucl_distance(x,y):
	r = 0
	for xi,yi in zip(x,y):
		r += (xi - yi)**2
	return np.sqrt(r)

"""
pad string s to length l with character withch, adding characters to either the beginning (at_beginning = True) or the end (else) 
"""
def pad(s:str,l:int,withch='0',at_beginning=True):
	while len(s) < l:
		if at_beginning:
			s = withch + s
		else:
			s = s + withch
	return s