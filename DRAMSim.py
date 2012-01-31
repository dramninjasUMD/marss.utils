"""
	DRAMSim-specific functions
"""
import tempfile
import os.path
from Graphs import *


def vis_file_to_datatable(filename):
	if not os.path.exists(filename):
		print "ERROR: BOB file %s not found"%filename
		exit()
	
	output = tempfile.NamedTemporaryFile(delete=False)
	fp = open(filename, "r")
	line = 'blah'; 
	startCopying = False
	while line: 
		line = fp.readline(); 
		if line.startswith("!!EPOCH_DATA"):
			startCopying = True; 
			continue
		elif line.startswith("!!HISTOGRAM_DATA"):
			break;
		if startCopying: 
			output.write(line)
	print "outfilename="+output.name
	output.close()
	return DataTable(output.name)

