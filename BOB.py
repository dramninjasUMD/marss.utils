
"""
	BOB-specific functions 
"""

from Graphs import *
import os.path

def bob_file_to_datatable(filename):
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
	
# used by graph and send
def get_sim_desc_from_num(num):
	prefix="#SIM_DESC="
	bob_variant_prefix="#BOB_VARIANT="
	f = open(config.get_marss_dir_path("simulate%d.sh"%num));
	sim_desc=""
	bob_variant=""
	for line in f:
		if line.startswith(prefix):
			sim_desc = line[len(prefix)+1:].strip("\" \n")
		if line.startswith(bob_variant_prefix):
			bob_variant = "_"+line[len(bob_variant_prefix)+1:].strip("\" \n")
	return sim_desc+bob_variant

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


