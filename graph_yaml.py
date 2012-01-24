#!/usr/bin/python -W ignore::DeprecationWarning
  

import re
import os
import sys
import time, datetime
from subprocess import *
from send_gmail import *
from Graphs import *
import config 
import yaml
import pprint
import BOB 

from optparse import OptionParser

def load_data_table(filename):
	if filename.endswith(".bob"):
		return BOB.bob_file_to_datatable(filename)
	else:
		return DataTable(filename); 
	
# should match someVar(0..10)
regex = re.compile(r'(\w+)\((\d+)..(\d+)\)');

def create_key_lookup_range(y_col_name, y_col_description):
	""" return a list of tupules containing the column name and column
			description if a column name looks like someVar(1..3) with a description of 'foo %d',
			this function will return the tupules
		[(someVar[1], 'foo 1')
			,(somevar[2], 'foo 2')
			,(somevar[3], 'foo 3')]
	"""

	matches = regex.match(y_col_name)
	if not matches: 
		return [(y_col_name,y_col_description)]
	else:
		base_key = matches.group(1)
		ret_arr = []
	
		for i in range(int(matches.group(2)), int(matches.group(3))):
			if "%d" in y_col_description:
				output_description = y_col_description%i
			else:
				output_description = y_col_description

			ret_arr.append(("%s[%d]"%(base_key,i), output_description))
		return ret_arr
def process_kv_arguments(args):
	ret_dict = {}
	for a in args:
		kv_pair = a.split("=")
		ret_dict[kv_pair[0]] = kv_pair[1]
	return ret_dict 

def parse_arguments():	
	""" command line argument parsing and some basic error checking """ 
	parser = OptionParser()
	parser.add_option("-f", "--file", dest="yaml_filename", help="yaml filename with which to generate a graph", metavar="FILE")
	parser.add_option("-e", "--email", dest="email", help="email the png output (currently no support for emailing pdfs) (mail settings in config.py)", action="store_true")
	parser.add_option("-v", "--verbose", dest="verbose", help="spit out debug output", action="store_true")
	parser.add_option("-o", "--output", dest="output_filename", help="generate output file")
	parser.add_option("-w", "--width", dest="width", help="total width of output image (inches)")
	parser.add_option("-r", "--row_height", dest="row_height", help="height of each row (inches)")
	parser.add_option("-c", "--columns", dest="columns", help="number of columns")
	parser.set_usage("""Usage: %prog [options] input_file1=INPUT_FILE ... input_fileN=INPUT_FILE 

The input_file fields are key-value pairs used by the plot's
"datafile" field -- ex: if the yaml file has this in it: 

	plots: 
		- { datafile: in_file, ... }

then the command line should read something like:

	%prog -f plot.yaml in_file=my_in_file.csv 

	""");

	(options, args) = parser.parse_args()

	debug = options.verbose
	if debug:
		print "Options given: "
		pprint.pprint(options)

	if not options.yaml_filename:
		print "Must specify at least a YAML file"
		parser.print_help()
		exit(); 

	if not os.path.exists(options.yaml_filename):
		print "YAML file %s doesn't exist"%options.yaml_filename
		parser.print_help()
		exit();

	kv_args = process_kv_arguments(args)
	if debug:
		pprint.pprint(kv_args)

	return (debug,options,kv_args)

def get_parameter(key, default_value, y, options, kv_args):
	""" get the parameter value either from the yaml or command line with
		preference given to the command line
		returns the 'default_value' parameter if the argument isn't set
	"""
	options_dict = vars(options)
	if key in options_dict and options_dict[key]:
		try:
			return float(options_dict[key])
		except ValueError:
			return options_dict[key]
	elif key in y:
		return y[key]
	elif key in kv_args:
		return kv_args[key]
	else:
		return default_value

if __name__ == "__main__":

	debug,options,kv_args = parse_arguments()

	# load the YAML file
	y = yaml.load(open(options.yaml_filename).read()) 
	if debug:
		pprint.pprint(y) 

	g = []
	datatables = {}

	# first, go ahead and load all the datafiles into a datatables map
	for i,plot_nodes in enumerate(y["graphs"]):
		line_plots = []
		for plot_title,line_params_arr in plot_nodes.iteritems():
			for plot in line_params_arr["plots"]:
				input_file_label = plot["datafile"]

				# set the input file from either the yaml or command line -- if
				# both are given, prefer the command line 
				if input_file_label not in kv_args:
					if input_file_label not in y["datafiles"]:
						print "ERROR: yaml file %s expects input file %s, which was not defined"%(options.yaml_filename, input_file_label)
						exit(); 
					else:
						input_file = y["datafiles"][input_file_label]
				else:
					input_file = kv_args[input_file_label]

				# only load the data table if this label isn't already there
				if input_file_label not in datatables:
					datatables[input_file_label] = load_data_table(input_file)
				
	# now go ahead and create the graphs array
	for plot_nodes in y["graphs"]:
		line_plots = []
		for plot_title,line_params_arr in plot_nodes.iteritems():
			for plot in line_params_arr["plots"]:
				dt = datatables[plot["datafile"]]
				for col_tupule in create_key_lookup_range(plot['y_col'], plot['name']):
					col_name,col_description = col_tupule
					if dt.contains_column(col_name):	
						line_params = []
						if "line_params" in plot:
							line_params = plot["line_params"]	
						line_plots.append(LinePlot(dt, plot['x_col'], col_name, col_description, line_params))
			g.append(SingleGraph(line_plots,  title=plot_title, **line_params_arr["properties"]))
			if debug:
				pprint.pprint(plot)

	# Grab all the parameters here 
	title = get_parameter("title", "Graph Title", y, options, kv_args)
	width = get_parameter("width", 14.0, y, options, kv_args)
	row_height = get_parameter("row_height", 5.0, y, options, kv_args)
	columns = get_parameter("columns", 1, y, options, kv_args)
	output_filename = get_parameter("output_filename", "out.png", y, options, kv_args)
	if debug:
		print "width=%f, row_height=%f, cols=%d"%(width,row_height, columns)
	
	if not options.email and output_filename.endswith(".pdf"):
		print "WARNING: cannot email pdf files, writing PDF but not emailing!"
		output_mode = "latex"
		options.email = False;
	else:
		output_mode = "png"
	string_arr= [pprint.pformat(y)]
	# finally, hand over the graphs array to a CompositeGraph to generate the layout/output
	cg = CompositeGraph(title=title,num_cols=columns,num_boxes=len(g),output_mode=output_mode)
	cg.w = width/cg.get_num_cols()
	cg.h = row_height*cg.get_num_rows()
	if debug:
		print "C=%d, R=%d"%(cg.get_num_cols(), cg.get_num_rows())
	cg.draw(g, output_filename);
	outfiles = [output_filename]

	if options.email:
		authorize_and_send(None,outfiles,strings_arr=string_arr);
