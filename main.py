import operator
from collections import deque
import matplotlib.pyplot as plt

PEEA = "ParallelExecutor.ExecuteActions:"


def wiztree_internal(filename, size, allocated, modified, attributes, files, folders):
    assert 0 <= files
    assert 0 <= folders
    assert 0 <= size

    return '"{}",{},{},{},{},{},{}'.format(filename.replace('"', ""), size, allocated, modified, attributes, files, folders)


def wiztree(filename, size, num_children=0):
    size = int(size * 1000000)
    return wiztree_internal(filename, size, size, "2019/01/13 15:22:10", 0, num_children, max(0, num_children - 1))


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

with open("Log.txt", "r") as file:
    def parse_count():
        count = file.readline()
        assert "Count:" in count
        return int(count.split("Count:")[1])


    def parse_total():
        total = file.readline()
        assert "Total:" in total, total
        return float(total.split("Total:")[1].strip()[:-1])


    def parse_empty():
        empty = file.readline()
        assert empty.strip() == PEEA, empty


    def parse_top():
        top = file.readline()
        assert "(top-level only):" in top, "Invalid top: {}".format(top)
        assert "Top" in top
        return int(top.split("Top")[1].split("(top-level only):")[0])


    def parse_string(string):
        line = file.readline()
        assert string in line, "{} not in {}!".format(string, line)
        assert line[len(PEEA):].strip() == string


    def parse_tree(count, current_file, getname=lambda x: x):
        current_indent = 0
        tree = Tree(current_file, 0, 0)
        queue = deque([tree])
        for _ in range(count):
            include = file.readline()
            assert include.startswith(PEEA)
            assert include[-1] == "\n"

            include = include[len(PEEA):-1]
            indent = len(include.split(include.lstrip()[0])[0]) - 4
            assert indent >= 0
            include_time = include.split(":")[-1].strip()
            assert include_time[-1] == "s", include_time
            include_name = getname(include.split(include_time)[0].strip()[:-1])
            include_time = float(include_time[:-1])

            if indent > current_indent:
                assert current_indent + 1 == indent
            else:
                for _ in range(current_indent - indent + 1):
                    queue.pop()

            new_tree = Tree(include_name, include_time, indent)
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
        print("Parsing {} items".format(count))
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

        if not line.startswith(PEEA):
            continue
        line = line[len(PEEA):]

        if not line.lstrip().startswith("["):
            continue
        extension = ""
        for ext in [".cpp", ".rc", ".lib", ".dll"]:
            if ext in line:
                extension = ext
                break
        else:
            assert False, "Invalid file name: " + line

        current_file = line.split("]")[1].lstrip().split(extension)[0] + extension
        print("Current file: " + current_file)

        if extension in [".rc", ".lib", ".dll"]:
            print("Skipping")
            continue

        parse_string("Include Headers:")

        print("Parsing includes...")
        includes_tree = parse_section(current_file, get_include_name)
        print("Includes parsed!")

        parse_string("Class Definitions:")

        print("Parsing classes...")
        classes_tree = parse_section(current_file)
        print("Classes parsed!")

        parse_string("Function Definitions:")

        print("Parsing functions...")
        functions_tree = parse_section(current_file)
        print("Functions parsed!")

        map[current_file] = includes_tree, classes_tree, functions_tree

print("Done!\n\n\n")

for name, index in (("includes", 0), ("classes", 1), ("functions", 2)):
    print("Writing " + name)
    with open("result_{}.csv".format(name), "w") as file:
        file.write("Generated by WizTree 3.26 1/13/2019 3:53:08 PM (You can hide this message by making a donation)\n"
                   "File Name,Size,Allocated,Modified,Attributes,Files,Folders)\n")
        num = 0
        for cpp in map:
            num += 1
            print("{}/{}".format(num, len(map)))
            tree = map[cpp][index]
            if tree is not None:
                tree.compute_num_children()
                tree.to_wiztree(file)

numbers = []
for key, value in sorted(headers.items(), key=operator.itemgetter(1)):
    print("{}: {}".format(key, value))
    while len(numbers) <= value:
        numbers.append(0)
    numbers[value] += 1

for i in range(len(numbers)):
    if numbers[i] != 0:
        print("{0}: {1} headers included {0} times".format(i, numbers[i]))

print("{} headers".format(len(headers)))

plt.bar(range(1, len(numbers)), numbers[1:])
plt.yscale("log")
plt.xlabel("Number of times included")
plt.ylabel("Number of headers included that many times")
plt.xlim(xmin=1)
plt.show()
