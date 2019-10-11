"""
This file contains all of the information on different locations -- homes, workplaces, entertainment centers, stores, schools, etc.

At any given time t a location has a list of people currently at the location, which can of course be empty.
"""


class Location:

	"""
	capacity indicates how many people the location can contain at most
	type is mostly for convenience so we know what kind of location it is:
		'spectator' (theater/sports event/concert/movie theater), 'convention', 'restaurant', 'shop', 'public' (park, town square; this will be used to move people between other locations), 'casino' ,
		'home', 'school', 'car'
	"""
	def __init__(self,capacity,loc_type):
		self.people = []
		self.capacity = capacity
		self.loc_type = loc_type

class Home(Location):

	def __init__(self,capacity):
		super().__init__(capacity,'home')


class School(Location):

	"""
	hours can be a time 2-tuple (minutes past midnight), or ('variable',(start,end),block).
	The first means that it is a strict schedule defined by the tuple for all students, the second indicates that students pick their own schedules between the start and end time, in blocks of 'block'
	"""
	def __init__(self,capacity,studentAgeRange,hours):
		super().__init__(capacity,'school')
		self.studentAgeRange = studentAgeRange  # instead of bothering with multiple school subclasses, just define an age range since that's all that really matters
		self.isVariableHours = hours[0] == 'variable'

		if self.isVariableHours:
			self.hours = hours[1]
			self.block = hours[2]
		else:
			self.hours = hours