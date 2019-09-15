import os
import sys
from tkinter import Tk, filedialog

class TreeNode:
	""" Base tree node, not very useful on its own. """
	def __init__(self, parent=None):
		self.parent = parent
		self.children = []

		# Cached. Includes full subtree.
		self.child_count = -1

		# Cached. Includes only direct leaf nodes.
		self.self_leaf_child_count = -1


	def is_root(self):
		""" Returns True if node has no parent. """
		return self.parent == None

	def is_leaf(self):
		""" Returns True if node has no children. """
		return self.self_child_count <= 0

	def add_child(self, node):
		""" Adds extra node to the list of children. """
		if node:
			self.children.append(node)

	@property
	def self_child_count(self):
		""" Number of self children this node has. """
		return len( self.children )

	def cache_useful_data(self):
		""" Caches useful data, it's up to the node to decide what is useful and what is not. """
		self.self_leaf_child_count = self._self_leaf_child_count()
		self.child_count = self._child_count()

	def to_string(self):
		""" Converts node to human readable string. """
		if self.parent:
			return "child"
		else:
			return "root"

	def _self_leaf_child_count(self):
		return sum( 1 for node in self.children if node.self_child_count )

	def _child_count(self):
		return self.self_child_count + sum( node._child_count() for node in self.children )


class GenericTreeNode(TreeNode):
	""" Tree node that can work with all three timing data types ( headers, classes, functions ). """
	def __init__(self, parent=None, data="", duration=0.0):
		super().__init__(parent)
		self.data = data

		# This duration also includes every child.
		self.duration = duration
		
		# Cached. Excludes children. 
		self.self_duration = -1.0

		# Cached. Tree made out of 'data' separated by \
		self.tree_path = ""

	def cache_useful_data(self):
		super().cache_useful_data()
		self.tree_path = self._tree_path()

		if self.is_root():
			self.self_duration = 0.0
			self.duration = sum( node.duration for node in self.children )

		else:
			self.self_duration = self._self_duration()

	def to_string(self):
		if self.parent:
			return "{} : {}s".format(self.data, self.duration)
		else:
			return "root"

	def _self_duration(self):
		return self.duration - sum( node.duration for node in self.children )

	def _tree_path(self):
		if self.is_root():
			return self.data
		else:
			return self.parent.tree_path + "\\" + self.data

class Tree:
	def __init__(self, root=TreeNode()):
		self.root = root

	def get_nodes_po(self):
		""" Returns pairs ( node, depth ) using pre order. """

		node_stack = [(self.root, 0)]

		while len(node_stack) > 0:
			yield node_stack[-1]
			node, indent = node_stack.pop()

			for child in node.children[::-1]:
				node_stack.append((child,indent + 1))

	def cache_useful_data(self):
		""" Runs cache_useful_data on every node in the tree. """
		for node, depth in self.get_nodes_po():
			node.cache_useful_data()

	def print(self):
		for node, indent in self.get_nodes_po():
			print("{}{}".format("\t" * indent, node.to_string()))


class TimingFile:
	""" Respresets single .cpp.timing.txt file """
	def __init__(self,path,headers, classes, functions):
		self.name = os.path.basename(path)
		self.path = path
		self.headers = headers
		self.classes = classes
		self.functions = functions

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=60, fill='█'):
    """
	Taken from https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()

def get_argv_path_or_ask_user(argument_index):
	""" Tries to get a path from sys.argv and if that fails asks the user directly. """
	if len(sys.argv) <= argument_index:
		root = Tk()
		root.withdraw()
		path = filedialog.askdirectory()
	else:
		path = sys.argv[argument_index]

	if path and os.path.exists(path) and os.path.isdir(path):
		return path

	return ""

def get_search_path():
	""" Figures out where to look for timing data. Either uses argv or asks the user. """
	return get_argv_path_or_ask_user(1)

def get_output_path():
	""" Figures out where to write results. Either uses argv or asks the user. """
	return get_argv_path_or_ask_user(2)

def get_timing_file_paths(path):
	""" Recursivly searches given path for cpp.timing.txt files. """

	paths = []
	for root, dirs, files in os.walk(path):
		for file in files:
			if file.endswith("cpp.timing.txt"):
				file_path = os.path.join(root, file)
				paths.append(file_path)

	return paths

def find_section(lines, section_marker):
	""" Finds section length ( Count ) and index of a first data line.  """

	for index, line in enumerate(lines):
		if line == section_marker:
			if index + 1 < len(lines):
				count_line = lines[index + 1].strip()
				if count_line.startswith("Count:"):
					return (int(count_line[6:]), index + 2)


	raise RuntimeError("Malformed timing file, failed to find section: {}".format(section_marker))

def get_indent_level(line):
	""" Counts number of tabs ( "\t" ) at the beginning of the line. """

	level = 0
	for c in line:
		if c == "\t":
			level += 1
		else:
			break

	return level

def make_section_tree(path, lines, section_marker, make_node):
	""" Makes a Tree instance for a requested section. """

	root_node_data = "W:\\" + os.path.basename(path).rstrip( ".timing.txt")
	tree = Tree(make_node(root_node_data))
	
	node_stack = [(tree.root, 0)]
	line_count, first_line_index = find_section(lines,section_marker)
	for line in lines[first_line_index : first_line_index + line_count]:
		parent_node, parent_indent = node_stack[-1]

		child_indent = get_indent_level(line)

		while child_indent <= parent_indent:
			if len(node_stack) > 0:
				node_stack.pop()
				parent_node, parent_indent = node_stack[-1]
			else:
				raise RuntimeError("Malformed section tree, section: {}".format(section_marker))

		child_node = make_node(line, parent_node)

		parent_node.add_child(child_node)
		node_stack.append((child_node, child_indent))

	tree.cache_useful_data()
	return tree

def make_generic_tree_node(line=None, parent=None):
	""" Parses data line ( data : timing ) and creates GenericTreeNode. """

	if parent:
		separator_index = line.rfind(":") 
		if separator_index != -1:
			data = line[0 : separator_index].strip().rstrip()
			duration = float(line[separator_index + 1 : -1])
			return GenericTreeNode(parent, data, duration)

		raise RuntimeError("Malformed data line, can't find ':': {}".format(line))
	else:
		return GenericTreeNode(None, line, 0.0 )

def make_generic_tree_header_node(line=None, parent=None): 
	node = make_generic_tree_node(line,parent)
	if not node.is_root():
		node.data =  os.path.basename(node.data)
	return node

def make_timing_file(path,lines):
	"""  Creates an instance of TimingFile from a given list of lines. Returns None in case of malformed data. """
	try:
		header_tree = make_section_tree(path,lines, "Include Headers:", make_generic_tree_header_node)
		class_tree = make_section_tree(path,lines, "Class Definitions:", make_generic_tree_node)
		function_tree = make_section_tree(path,lines, "Function Definitions:", make_generic_tree_node)
		return TimingFile(path, header_tree, class_tree, function_tree)

	except RuntimeError as error:
		print("Failed to create timing file for {}. {}".format(path, str(error)))
		return None

def read_timing_file(path):
	""" Creates an instance of TimingFile from a given path. """

	if not os.path.exists(path):
		print("Can't read timing file, no longer exists: {}".format(path))
		return None
	elif not os.path.isfile(path):
		print("Can't read timing file, not a file: {}".format(path))
		return None
	else:
		try:
			with open(path, "r", encoding="utf-8") as file:
				lines = list(map(lambda line : line.rstrip(), file.readlines()))
				return make_timing_file(path,lines)

		except OSError as error:
			print("Can't read timing file, failed to open: {}".format(path))

	return None

def read_timing_files(paths):
	""" Creates an instance of TimingFile for every path provided. """

	files = []
	for index, path in enumerate(paths):
		print_progress_bar(index + 1, len(paths), "Reading timing files:")
		file = read_timing_file(path)
		if file:
			files.append(file)

	return files

def write_wiztree_file(timing_files, get_tree, output_path, debug_prefix=""):
	""" Writes .csv file for a single Tree object. """

	with open(output_path, "w", encoding="utf-8") as wiztree_file:
		wiztree_file.write("File Name,Size,Allocated,Modified,Attributes,Files,Folders\n")

		for index, timing_file in enumerate(timing_files):
			for node, depth in get_tree(timing_file).get_nodes_po():
				if not node.is_leaf():
					file_name = '"' + node.tree_path + '\\"'
				else:
					file_name = '"' + node.tree_path + '"'
					
				# Note about 1024 * 1000. 
				# We want to convert 1s to 1MB in WizTree but both
				# 1000 * 1000 and 1024 * 1024 give bad results ( too small or too big ).
				# Only with 1024 * 1000 0.93s gets displayed as 0.93MB.

				if node.is_root():
					size = int( node.duration * 1024 * 1000 )
				else:
					size = int( node.self_duration * 1024 * 1000 )

				allocated = size
				modified = r"2019/01/01 00:00:00"
				attributes = "0"
				files = node.self_leaf_child_count
				folders = node.self_child_count - files

				wiztree_file.write( "{},{},{},{},{},{},{}\n".format( file_name, size, allocated, modified, attributes, files, folders ) )

				if not node.is_leaf() and not node.is_root():
					file_name = '"' + node.tree_path + "\\self" + '"' 
					wiztree_file.write( "{},{},{},{},{},{},{}\n".format( file_name, size, allocated, modified, attributes, files, folders ) )

			print_progress_bar(index+1, len(timing_files), debug_prefix)



def write_wiztree_files(timing_files, output_path):
	""" Writes .csv files for all three types of data. """

	write_wiztree_file(timing_files, lambda f : f.headers, os.path.join(output_path, "wiztree_includes.csv"), "Writing wiztree includes:")
	write_wiztree_file(timing_files, lambda f : f.classes, os.path.join(output_path, "wiztree_classes.csv"), "Writing wiztree classes:")
	write_wiztree_file(timing_files, lambda f : f.functions, os.path.join(output_path, "wiztree_functions.csv"), "Writing wiztree functions:")

if __name__ == "__main__":
	search_path = get_search_path()
	file_paths = get_timing_file_paths(search_path)
	timing_files = read_timing_files(file_paths)

	output_path = get_output_path()
	write_wiztree_files(timing_files,output_path)
