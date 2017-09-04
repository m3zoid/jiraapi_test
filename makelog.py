"""Here is a class for outputting data, making log and error log
"""

import os
import time


class Makelog:
	def __init__(self, logname, errorlogname):
		self._logname = logname
		self._errorlogname = errorlogname

	def putto_file(self, data):
		with open(self._logname, 'a') as output_file:
			output_file.write(time.strftime("%a, %d %b %Y %H:%M:%S\n", time.localtime()))
			output_file.write(data)

	def putto_console(self, data, iscln=False):
		if iscln:
			os.system('cls' if os.name == 'nt' else 'clear')

		print time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
		print data

	def putto_errorlog(self, data, trcback):
		with open(self._errorlogname, 'a') as output_file:
			output_file.write(time.strftime("%a, %d %b %Y %H:%M:%S\n", time.localtime()))
			output_file.write("{}\n{}\n\n".format(data, trcback))
