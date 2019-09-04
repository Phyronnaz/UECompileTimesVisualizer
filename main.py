import operator
import sys
from collections import deque

if len(sys.argv) < 2:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()

    log_file = filedialog.askopenfilename(title="Select log file")
else:
    log_file = sys.argv[1]

dest_files = "result" if len(sys.argv) < 3 else sys.argv[2]

def print_debug(*args, **kwargs):
    # print(*args, **kwargs)
    pass

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def wiztree_internal(filename, size, allocated, modified, attributes, files, folders):
    assert 0 <= files
    assert 0 <= folders
    assert 0 <= size

    return '"{}",{},{},{},{},{},{}'.format(filename.replace('"', ''),
                                           size,
                                           allocated,
                                           modified,
                                           attributes,
                                           files,
                                           folders)


def wiztree(filename, size, num_children=0):
    size = int(size * 1000000)
    return wiztree_internal(filename, size, size, "2019/01/01 00:00:00", 0, num_children, max(0, num_children - 1))


class Tree:
    def __init__(self, name, time, indent):
        assert 0 <= time
        self.name = name
        self.time = time
        self.indent = indent
        self.children = []

    def __str__(self):
        string = "\t" * self.indent + "Name: {}; Time: {}".format(self.name, self.time)
        for child in self.children:
            string += "\n" + str(child)
        return string

    def compute_num_children(self):
        self.num_children = 1 + sum([child.compute_num_children() for child in self.children])
        return self.num_children

    def to_wiztree(self, file, parent="C:\\"):
        path = parent + self.name + "\\"
        selftime = self.time - sum([child.time for child in self.children])

        if -1e-3 < selftime < 0:
            selftime = 0

        assert 0 <= self.time
        assert 0 <= selftime, selftime
        assert selftime <= self.time
        assert 0 < self.num_children

        file.write(wiztree(path, self.time, self.num_children) + "\n")
        file.write(wiztree(path + "self", selftime) + "\n")

        for child in self.children:
            child.to_wiztree(file, path)


map = {}
headers = {}

with open(log_file, "r", encoding="utf-8-sig") as file:
    line = file.readline()
    file.seek(0)

    if "Unreal" in line:
        configuration = "Unreal"
        prefix = "ParallelExecutor.ExecuteActions:"
        default_indent = 4
    elif "Qt" in line:
        configuration = "Qt"
        prefix = ""
        default_indent = 1
    else:
        configuration = "MSVC"
        prefix = ""
        default_indent = 3

    print("{} log file detected".format(configuration))


    def get_line():
        line = file.readline()
        assert line.startswith(prefix), "{} does not start with {}".format(line, prefix)
        return line[len(prefix):]


    def get_line_for_try():
        last_pos = file.tell()
        line = file.readline()
        file.seek(last_pos)
        assert line.startswith(prefix), "{} does not start with {}".format(line, prefix)
        return line[len(prefix):]


    def parse_int(string):
        line = get_line().strip()
        assert string in line, "{} not in {}".format(string, line)
        return int(line.split(string)[1])


    def parse_float(string, suffix):
        line = get_line().strip()
        assert string in line, "{} not in {}".format(string, line)
        assert line.endswith(suffix), "{} does not end with {}".format(line, suffix)
        line = line.split(string)[1][:-len(suffix)].strip()
        if line == "-nan(ind)":
            return 0
        else:
            return float(line)


    def parse_count():
        return parse_int("Count:")


    def parse_total():
        return parse_float("Total:", "s")


    def parse_seconds(string):
        return parse_float(string, " sec")


    def parse_empty():
        empty = get_line().strip()
        assert empty == "", empty


    def parse_top():
        top = get_line().strip()
        assert "(top-level only):" in top, "(top-level only) not in " + top
        assert "Top" in top, "Top not in " + top
        return int(top.split("Top")[1].split("(top-level only):")[0])


    def parse_string(string):
        line = get_line().strip()
        assert line == string, line + "!=" + string


    def try_parse_string(string):
        line = get_line_for_try().strip()
        if line == string:
            parse_string(string)
            return True
        else:
            return False


    def try_parse_int(string):
        line = get_line_for_try().strip()
        if string not in line:
            return 0
        else:
            return parse_int(string)


    def try_parse_float(string, suffix):
        line = get_line_for_try().strip()
        if string not in line:
            return 0
        else:
            return parse_float(string, suffix)


    def try_parse_seconds(string):
        return try_parse_float(string, " sec")


    def try_parse_empty():
        line = get_line_for_try().strip()
        if line == "":
            parse_empty()
            return True
        else:
            return False


    def parse_beginstring(string):
        line = get_line().strip()
        assert line.startswith(string), "{} does not start with {}".format(line, string)


    def parse_tree(count, current_file, getname=lambda x: x):
        current_indent = 0
        tree = Tree(current_file, 0, 0)
        queue = deque([tree])
        for _ in range(count):
            include = get_line()
            assert include[-1] == "\n", include
            include = include[:-1]

            indent = len(include.split(include.lstrip()[0])[0]) - default_indent
            assert indent > 0, "Wrong indent: default indent should be {}".format(indent + default_indent - 1)

            include_time = include.split(":")[-1].strip()
            assert include_time[-1] == "s", "Wrong time: " + include_time

            include_name = getname(include.split(include_time)[0].strip()[:-1])
            include_time = float(include_time[:-1])

            if indent > current_indent:
                assert current_indent + 1 == indent, "Going from {} indents to {}".format(current_indent, indent)
            else:
                for _ in range(current_indent - indent + 1):
                    queue.pop()

            new_tree = Tree(include_name, include_time, indent)
            assert len(queue) > 0, "Wrong indent level"
            queue[-1].children.append(new_tree)
            queue.append(new_tree)
            current_indent = indent

            assert len(queue) == current_indent + 1
        return tree


    def get_include_name(include_name):
        include_name = include_name.split("\\")[-1]
        if include_name not in headers:
            headers[include_name] = 0
        headers[include_name] += 1
        return include_name


    def parse_section(current_file, getname=lambda x: x):
        tree = None
        count = parse_count()
        print_debug("    Parsing {} items...".format(count))
        if count > 0:
            tree = parse_tree(count, current_file, getname)

            parse_empty()

            for _ in range(parse_top()):
                file.readline()
        parse_empty()
        total = parse_total()
        if tree is not None:
            tree.time = total
        return tree


    while True:
        line = file.readline()
        if len(line) == 0:
            assert len(file.readline()) == 0
            break

        if not line.startswith(prefix):
            continue
        line = line[len(prefix):]

        if configuration == "Unreal":
            if not line.lstrip().startswith("["):
                print("Skipping line " + line.strip())
                continue
        elif configuration == "Qt":
            if line[0] == "\t":
                print("Skipping line " + line.strip())
                continue

        extension = ""
        for ext in [".h", ".cpp", ".rc", ".lib", ".dll", ".exe"]:
            if ext in line:
                extension = ext
                break
        else:
            assert False, "Invalid file name: " + line

        if configuration == "Unreal":
            line = line.split("]")[1]

        current_file = line.strip().split(extension)[0] + extension
        print(current_file)

        if extension in [".rc", ".lib", ".dll", ".exe"]:
            print("Skipping extension " + extension)
            continue

        try_parse_string("Unknown compiler version - please run the configure tests and report the results")
        try_parse_string("Include Headers:")

        print_debug("    Parsing includes...")
        includes_tree = parse_section(current_file, get_include_name)
        print_debug("    Includes parsed!")

        parse_string("Class Definitions:")

        print_debug("    Parsing classes...")
        classes_tree = parse_section(current_file)
        print_debug("    Classes parsed!")

        parse_string("Function Definitions:")

        print_debug("    Parsing functions...")
        functions_tree = parse_section(current_file)
        print_debug("    Functions parsed!")

        parse_beginstring("time(")
        parse_beginstring("Elapsed Time before Code Generation:")

        if try_parse_string("Code Generation Summary"):
            parse_int("Total Function Count:")
            parse_seconds("Elapsed Time:")
            parse_seconds("Total Compilation Time:")
            parse_seconds("Average time per function:")
            for _ in range(try_parse_int("Anomalistic Compile Times:")):
                get_line()
            try_parse_int("Serialized Initializer Count:")
            try_parse_seconds("Serialized Initializer Time:")
            parse_empty()

        if try_parse_string("RdrReadProc Caching Stats"):
            parse_int("Functions Cached:")
            parse_int("Retrieved Count:")
            parse_int("Abandoned Retrieval Count:")
            parse_int("Abandoned Caching Count:")
            parse_int("Wasted Caching Attempts:")
            parse_int("Functions Retrieved at Least Once:")
            parse_int("Functions Cached and Never Retrieved:")
            parse_string("Most Hits:")
            while not try_parse_empty():
                get_line()
            parse_string("Least Hits:")
            while not try_parse_empty():
                get_line()

        parse_beginstring("Elapsed Time after Code Generation:")
        parse_beginstring("time(")

        map[current_file] = includes_tree, classes_tree, functions_tree

        print_debug("")

print("Done!\n\n\n")

if query_yes_no("Write wiztree files?"):
    for name, index in (("includes", 0), ("classes", 1), ("functions", 2)):
        print("Writing " + name)
        with open("{}_{}.csv".format(dest_files, name), "w") as file:
            file.write("File Name,Size,Allocated,Modified,Attributes,Files,Folders)\n")
            num = 0
            for cpp in map:
                num += 1
                print("{}/{}".format(num, len(map)), end="\r")
                tree = map[cpp][index]
                if tree is not None:
                    tree.compute_num_children()
                    tree.to_wiztree(file)

    print("Done!\n\n\n")

if query_yes_no("Print header usage?"):
    print("Header usage:")
    for key, value in sorted(headers.items(), key=operator.itemgetter(1)):
        print("{}: {}".format(key, value))

if query_yes_no("Print cumulative include times?"):
    headers_cost = {}

    def iterate_includes_tree(tree):
        if tree.name not in headers_cost:
            headers_cost[tree.name] = 0
        headers_cost[tree.name] += tree.time

        for child in tree.children:
            iterate_includes_tree(child)

    for cpp in map:
        tree = map[cpp][0]
        if tree is not None:
          iterate_includes_tree(tree)

    sorted_headers_cost = sorted(headers_cost.items(), key=operator.itemgetter(1))

    for name, time in sorted_headers_cost:
        print("{}: included {} times, total time: {}s".format(name.ljust(50), str(headers[name] if name in headers else 1).ljust(4), time))
