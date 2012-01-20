
"""
	Converter objects to take in a file and create a DataTable out of it
"""

from Graphs import *
import os.path

def readBOBFile(filename):
	if not os.path.exists(filename):
		print "ERROR: BOB file %s not found"%filename
		exit()
	
	fp = open(filename, "r")
	line = fp.readline(); 
	while line: 
		if line.startswith("!!EPOCH_DATA"):
			break; 
		line = fp.readline(); 
	return DataTable(fp)
	
if __name__ == "__main__":
	dt = readBOBFile("bob.txt"); 
	graphs = [
			SingleGraph([
				LinePlot(dt,"ns","bandwidth","Bandwidth",[':', 1.5, 'r'])
			,	LinePlot(dt,0,"rwRatio","RW Ratio", ["--", 1.2,'g'])
			], AxisDescription("ns"), AxisDescription("garbage"), "testTitle")
	];
	composite_graph = CompositeGraph(); 
	composite_graph.draw(graphs,"blah.png"); 


