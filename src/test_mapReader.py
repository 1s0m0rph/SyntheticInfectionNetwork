from unittest import TestCase

from Map import *

class TestMapReader(TestCase):
	def test_read_from_file(self):
		fname = r'C:\Users\Isomorph\Documents\School Fall 2019\CSCI\3352\project\3352_project_infection\test_map_0.png'
		mr = MapReader()
		mr.read_from_file(fname)
