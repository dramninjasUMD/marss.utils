#!/usr/bin/python
"""
This is a converter that will take the old DRAMSim2 vis files which contained
key,value pairs in each epoch and will convert it into a csv file that can be 
used with graph_yaml.py

This script takes a single argument which is the path of the .vis file to convert
the output file will be the same filename with extension .csv.vis
"""


from optparse import OptionParser
import re
import os 
import sys

class VisFileData:
	def __init__(self, filename):
		self.fp = open(filename, "r")
		self.valueMap = {}
		self.readMetaData()
		self.readVisFile()
		print "Loaded vis file %s"%filename
	def readMetaData(self):
		for line in self.fp:
			if line.startswith("NUM_RANKS"):
				self.num_ranks = int(line.split("=")[1])
			if line.startswith("NUM_BANKS"):
				self.num_banks = int(line.split("=")[1])

			if line.startswith("!!EPOCH_DATA"):
				break;
		print "%d ranks %d banks"%(self.num_ranks, self.num_banks)

	def readVisFile(self):
		isFirstLine=True;
		for line in self.fp:
			line = line.replace(":",",")
			line = line.replace("\n","")
			fields = line.split(",")
			for f in fields:
				pairs = f.split("=");
				if (len(pairs) == 2):
					if isFirstLine:
						self.valueMap[pairs[0]] = [pairs[1]]
					else:
						self.valueMap[pairs[0]].append(pairs[1])
				else: #the timestamp doesn't have a kv pair
					if len(f) == 0:
						continue;
		#			print "'"+f+"'"
					if isFirstLine:
						self.valueMap["ms"] = [f]
					else:
						self.valueMap["ms"].append(f)
			isFirstLine=False
		self.fp.close()
		self.num_values = len(self.valueMap["ms"])

	def sumPerBankValues(self, base_key, output_var_name):
		if output_var_name in self.valueMap:
			print "ERROR: output key %s already exists"%output_var_name
			exit();
		else:
			self.valueMap[output_var_name] = []
		for t in range(0,self.num_values):
			total = 0.0;
			for r in range(0,self.num_ranks):
				for b in range(0, self.num_banks):
					key = "%s_%d_%d"%(base_key,r,b)
					if key not in self.valueMap:
						key = "%s_%d"%(base_key, r) # per rank value?
					if key not in self.valueMap:
						print ("Key %s not found in file"%base_key)
						exit();
					total += float(self.valueMap[key][t])
			self.valueMap[output_var_name].append(total)
		assert len(self.valueMap[output_var_name]) == self.num_values, "output length didn't match"
		
	def writeCSVFile(self, output_filename):
		fp = open(output_filename, "w");
		#print header
		for k in self.valueMap.keys():
			fp.write("%s,"% k);
		fp.write("\n");
		for i in range(0,self.num_values):
			for k in self.valueMap.keys():
				fp.write("%s,"%self.valueMap[k][i])
			fp.write("\n")
		fp.close()

if __name__ == "__main__":
	if (len(sys.argv) < 2):
		print "missing input filename"
	filename = sys.argv[1]
	output_filename = filename.replace(".vis", ".csv.vis")
	v = VisFileData(filename);
	v.sumPerBankValues("b", "bandwidth")
	v.writeCSVFile(output_filename)
