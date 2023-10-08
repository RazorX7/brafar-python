import ast

from zss import Node, simple_distance

from basic_framework.program_builder import get_code


def zss_ast_visit(ast_node, parent_zss_node):
    zss_label = str_node(ast_node)
    if zss_label == "":
        for field, value in ast.iter_fields(ast_node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        zss_ast_visit(item, parent_zss_node)
            elif isinstance(value, ast.AST):
                zss_ast_visit(value, parent_zss_node)
    else:
        zss_node = Node(zss_label)
        for field, value in ast.iter_fields(ast_node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        zss_ast_visit(item, zss_node)
            elif isinstance(value, ast.AST):
                zss_ast_visit(value, zss_node)
        parent_zss_node.addkid(zss_node)


def str_node(node):
    return acc_str_node(node)


# accurate label approach
def acc_str_node(node):
    if hasattr(node, "id"):
        return node.id
    elif hasattr(node, "name"):
        return node.name
    elif hasattr(node, "arg"):
        return node.arg
    elif hasattr(node, "n"):
        return str(node.n)
    elif hasattr(node, "s"):
        return "\'" + node.s + "\'"
    else:
        if node.__class__.__name__ in ["Module", "Load", "Store"]:
            return ""
        else:
            return node.__class__.__name__


def zss_node_cnt(zss_node):
    s = 1
    for child_zss_node in zss_node.children:
        s += zss_node_cnt(child_zss_node)
    return s


def label_weight(l1, l2):
    if l1 == l2:
        return 0
    else:
        return 1


def zss_code_ast_edit(code_a, code_b):
    root_node_a = ast.parse(code_a)
    root_zss_node_a = Node("root")
    zss_ast_visit(root_node_a, root_zss_node_a)

    root_node_b = ast.parse(code_b)
    root_zss_node_b = Node("root")
    zss_ast_visit(root_node_b, root_zss_node_b)

    cost, ops = simple_distance(root_zss_node_a, root_zss_node_b, label_dist=label_weight, return_operations=True)
    return cost, ops


class ProgramTree(ast.NodeVisitor):
    def __init__(self, p_path):
        self.__p_path = p_path
        self.__p_code = get_code(self.__p_path)
        self.__p_node = ast.parse(self.__p_code)
        self.__methods = {}
        self.visit(self.__p_node)

    def visit_FunctionDef(self, node):
        self.__methods[node.name] = ast.unparse(node)
        return node

    def get_method_by_name(self, name):
        return self.__methods.get(name)

    def calculate_distance_func(self, func_name, func_code):
        return zss_code_ast_edit(self.__methods.get(func_name), func_code)[0]

    def get_closest_func(self, func_name, func_codes):
        code = ""
        mini_cost = 10000000
        for func_code in func_codes:
            cur_cost = self.calculate_distance_func(func_name, func_code)
            if cur_cost < mini_cost:
                code = func_code
                mini_cost = cur_cost
        return code
