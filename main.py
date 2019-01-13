from collections import deque

PEEA = "ParallelExecutor.ExecuteActions:"


def wiztree_internal(filename, size, allocated, modified, attributes, files, folders):
    return '"{}",{},{},{},{},{},{}'.format(filename, size, allocated, modified, attributes, files, folders)


def wiztree(filename, size, num_children=0):
    size = int(size * 1000000)
    return wiztree_internal(filename, size, size, "2019/01/13 15:22:10", 0, num_children, num_children - 1)


class Tree:
    def __init__(self, name, time, indent):
        self.name = name
        self.time = time
        self.indent = indent
        self.children = []

    def __str__(self):
        string = "\t" * self.indent + "Name: {}; Time: {}".format(self.name, self.time)
        for child in self.children:
            string += "\n" + str(child)
        return string

    def get_num_children(self):
        return 1 + sum([child.get_num_children() for child in self.children])

    def to_wiztree(self, parent="C:\\"):
        path = parent + self.name + "\\"
        selftime = self.time - sum([child.time for child in self.children])

        string = wiztree(path, self.time, self.get_num_children())
        string += "\n" + wiztree(path + "self", selftime)
        for child in self.children:
            string += "\n" + child.to_wiztree(path)
        return string


current_file = ""
num_includes = 0

map = {}

with open("Log.txt", "r") as file:
    def parse_count():
        count = file.readline()
        assert "Count:" in count
        return int(count.split("Count:")[1])


    def parse_total():
        total = file.readline()
        assert "Total:" in total, total
        return float(total.split("Total:")[1].lstrip().rstrip()[:-1])


    def parse_empty():
        empty = file.readline()
        assert empty.lstrip().rstrip() == PEEA


    def parse_top():
        top = file.readline()
        assert "(top-level only):" in top, "Invalid top: {}".format(top)
        assert "Top" in top
        return int(top.split("Top")[1].split("(top-level only):")[0])


    def parse_string(string):
        line = file.readline()
        assert string in line, "{} not in {}!".format(string, line)
        assert line[len(PEEA):].lstrip().rstrip() == string


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

        num_includes = parse_count()
        print("Num includes: {}".format(num_includes))

        current_indent = 0
        tree = Tree(current_file, 0, 0)
        queue = deque([tree])
        for _ in range(num_includes):
            include = file.readline()
            assert include.startswith(PEEA)
            assert include[-1] == "\n"

            include = include[len(PEEA):-1]
            indent = len(include.split(":\\")[0]) - 5
            include_name = include.split("\\")[-1]
            include_time = float(include_name.split(":")[1].lstrip()[:-1])
            include_name = include_name.split(":")[0]

            # print(include)
            # print(indent)
            # print(include_name)
            # print(include_time)

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
        print("Includes parsed!")

        parse_empty()
        for _ in range(parse_top()):
            file.readline()
        parse_empty()
        total_time = parse_total()

        tree.time = total_time
        map[current_file] = tree

        parse_string("Class Definitions:")
        count = parse_count()
        if count > 0:
            for _ in range(count):
                file.readline()

            parse_empty()
            for _ in range(parse_top()):
                file.readline()
        parse_empty()
        parse_total()

        parse_string("Function Definitions:")
        count = parse_count()
        if count > 0:
            for _ in range(count):
                file.readline()

            parse_empty()
            for _ in range(parse_top()):
                file.readline()
        parse_empty()
        parse_total()

print("Done!\n\n\n")

with open("result.csv", "w") as file:
    file.write("Generated by WizTree 3.26 1/13/2019 3:53:08 PM (You can hide this message by making a donation)\n"
               "File Name,Size,Allocated,Modified,Attributes,Files,Folders)\n")
    for name in map:
        file.write(map[name].to_wiztree() + "\n")
