"""
General utilities for the whole thing
"""
import numpy as np

TIME_STEPS_PER_DAY = 1440#for minutes
PROBABILITY_TRAVEL_SOMEWHERE = 0.2#per time step, what is the baseline probability that someone decides to go somewhere
AVERAGE_HOME_IDLE_TIME = 60#time steps. the average amount of time someone will spend idle at home before going somewhere
SSORT_LEVELS = 0#how many levels of quicksort partition should I apply to get the affinity order

DISEASE_STATES = {'S',	#susceptible
				  'II',	#infected, infectious
				  'VII',#vaccinated, infected, infectious
				  'IS',	#infected, showing symptoms
				  'VIS',#vaccinated, infected, showing symptoms
				  'R',	#recovered
				  'VR',	#vaccinated, recovered
				  'VS',	#vaccinated, susceptible
				  'VU',	#vaccinated, unsusceptible
				  'D',	#dead
				  'VD'	#vaccinated, dead
				  }

DISEASE_STATES_LIST = list(DISEASE_STATES)#for constant ordering

DISEASE_STATES_SUSCEPTIBLE = {'S','VS'}
DISEASE_STATES_INFECTIOUS = {'II','VII','IS','VIS'}
DISEASE_STATES_SYMPTOMATIC = {'IS','VIS'}
DISEASE_STATES_VACCINATED = {'VII','VIS','VR','VS','VU','VD'}
DISEASE_STATES_DEAD = {'D','VD'}
DISEASE_STATES_FINAL = DISEASE_STATES - DISEASE_STATES_INFECTIOUS
DISEASE_STATES_INITIAL = {'S','VU','VS'}

HANDWASH_EFFECT_MODIFIERS = [[0.,-0.1],
							 [-0.1,-0.5]]#modifiers for infectivity, given that (a,b) washed their hands

INTIMATE_EFFECT_MODIFIER = 0.2#how much more infectious things tend to be when people are intimate with infecteds

PLACABLE_LOCATION_TYPES = {'convention','shop'}
WORKABLE_LOCATION_TYPES = {'office','shop','convention','hospital'}

BIDIRECTIONAL_COWORKERS = False
BIDIRECTIONAL_FRIENDS = False

INTERACTION_EXPLORATION_REWARD = 0.05

GENERAL_TALK_PROBABILITY = 0.5

HOSPITAL_TREATMENT_EFFECT = 0.5	#to what extent (modulo the treatability of the disease) does being in the hospital help?

DISABLE_IDLE_INFECTION = True	#makes it so that idle infections (where people aren't explicitly interacting) aren't modeled

"""
Given a "time string" (HH:MM:SS, HH:MM, or just HH), convert that string into the equivalent number of time steps after midnight
"""
def tconv(tst: str) -> int:
	import re
	hhmmss = re.match(r'([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2})',tst)
	hhmm = re.match(r'([0-9]{1,2}):([0-9]{1,2})', tst)
	hh = re.match(r'([0-9]{1,2})', tst)
	h = 0.
	m = 0.
	s = 0.
	if hhmmss:
		h = float(hhmmss.group(1))
		m = float(hhmmss.group(2))
		s = float(hhmmss.group(3))
	elif hhmm:
		h = float(hhmm.group(1))
		m = float(hhmm.group(2))
	elif hh:
		h = float(hh.group(1))
	else:
		raise AttributeError('time string ' + tst + ' is not of the format HH:MM:SS, HH:MM, or HH')

	return int((TIME_STEPS_PER_DAY / 24.)*h + (TIME_STEPS_PER_DAY / 1440.)*m + (TIME_STEPS_PER_DAY / 86400.)*s)

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
	p = max(min(p,1),0)
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

"""
Tests whether the given time lies between the given times

times are all in minutes past midnight, with a max value of 23*60 + 59 =  1439
"""
def time_within_tuple(time,tup):
	assert(time < TIME_STEPS_PER_DAY)
	assert(tup[0] < TIME_STEPS_PER_DAY)
	assert(tup[1] < TIME_STEPS_PER_DAY)
	assert(time >= 0)
	assert(tup[0] >= 0)
	assert(tup[1] >= 0)
	#preconditions ^^

	if tup[0] > tup[1]:#then this tuple spans the midnight hour
		return (time >= tup[0]) or (time <= tup[1])

	return (time >= tup[0]) and (time <= tup[1])

"""
negative safe mod function, will return values in [0,n-1] that are congruent to a mod n 
"""
def negsafe_mod(a:int,n:int):
	if a < 0:
		return negsafe_mod(a+n,n)	#n cong 0 mod n, so this doesn't change our equivalence class
	return a % n

MAP_OPTIMIZATION_FUNCTION = manhattan_distance

def funcall_throws_error(f,*args,**kwargs):
	try:
		f(args,kwargs)
	except:
		return True
	return False