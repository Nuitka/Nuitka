import ast
import sys
import typing

if sys.version_info < (3, 9):
    from astunparse import unparse

    ast.unparse = unparse


class MainBlockRemover(ast.NodeTransformer):
    """AST transformer that removes 'if __name__ == "__main__":' blocks."""

    def visit_If(self, node):
        if (
            isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "__name__"
        ):
            if (
                len(node.test.ops) == 1
                and isinstance(node.test.ops[0], ast.Eq)
                and len(node.test.comparators) == 1
            ):
                comparator = node.test.comparators[0]
                if (
                    sys.version_info >= (3, 8)
                    and isinstance(comparator, ast.Constant)
                    and comparator.value == "__main__"
                ) or (
                    sys.version_info < (3, 8)
                    and isinstance(comparator, ast.Str)
                    and comparator.s == "__main__"
                ):
                    return None
        return self.generic_visit(node)


def preprocess_source(source_code):
    tree = ast.parse(source_code)
    transformer = MainBlockRemover()
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    return ast.unparse(transformed_tree)


def generate_stub_from_source(source_code, output_file_path, text_only=False):
    preprocessed_code = preprocess_source(source_code)
    tree = ast.parse(preprocessed_code)

    class StubGenerator(ast.NodeVisitor):
        def __init__(self):
            self.stubs = []
            self.imports_helper_dict = {}
            self.imports_output = set()
            self.typing_imports = typing.__all__
            self.in_class = False
            self.indentation_level = 0
            self.typevars = set()

        def visit_Import(self, node):
            for alias in node.names:
                self.imports_output.add("import %s" % alias.name)

        def visit_ImportFrom(self, node):
            module = node.module if node.module is not None else "."
            for alias in node.names:
                name = alias.name
                if module:
                    if module not in self.imports_helper_dict:
                        self.imports_helper_dict[module] = set()
                    self.imports_helper_dict[module].add(name)

        def visit_FunctionDef(self, node):
            if self.in_class:
                self.visit_MethodDef(node)
            else:
                for parent_node in ast.walk(tree):
                    if isinstance(parent_node, ast.ClassDef):
                        for child_node in parent_node.body:
                            if (
                                isinstance(child_node, ast.FunctionDef)
                                and child_node.name == node.name
                                and (child_node.lineno == node.lineno)
                            ):
                                return
                self.visit_RegularFunctionDef(node)

        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    target_name = target.id
                    target_type = ast.unparse(node.value).strip()
                    if (
                        isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and (node.value.func.id == "TypeVar")
                    ):
                        if "typing" not in self.imports_helper_dict:
                            self.imports_helper_dict["typing"] = set()
                        self.imports_helper_dict["typing"].add("TypeVar")
                        self.typevars.add(target_name)
                        if node.value.args:
                            typevar_def = "%s = TypeVar(%s)" % (target_name, ', '.join([ast.unparse(arg) for arg in node.value.args]))
                            self.stubs.append(typevar_def + "\n\n")
                        else:
                            self.stubs.append(
                                '"%s" = TypeVar("%s")\n\n' % (target_name, target_name)
                            )
                        continue
                    if target_type in self.typing_imports:
                        self.imports_output.add(target_type)
                    if target_type in self.typing_imports:
                        stub = "%s: %s\n" % (target_name, target_type)
                        self.stubs.append(stub)
                    elif isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Name):
                            if node.value.func.id == "frozenset":
                                stub = "%s = frozenset(%s)\n" % (target_name, ', '.join([ast.unparse(arg).strip() for arg in node.value.args]))
                                self.stubs.append(stub)
                            elif node.value.func.id == "namedtuple":
                                tuple_name = ast.unparse(node.value.args[0]).strip()
                                stub = "%s =  namedtuple(%s, %s)\n" % (target_name, tuple_name, ', '.join([ast.unparse(arg).strip() for arg in node.value.args[1:]]))
                                self.stubs.append(stub)
                            elif node.value.func.id == "TypeVar":
                                if "typing" not in self.imports_helper_dict:
                                    self.imports_helper_dict["typing"] = set()
                                self.imports_helper_dict["typing"].add("TypeVar")
                                self.typevars.add(target_name)
                    elif isinstance(node.value, ast.Subscript):
                        if isinstance(node.value.value, ast.Name):
                            target_name = target.id
                        target_type = ast.unparse(node.value).strip()
                        if "typing_extensions" not in self.imports_helper_dict:
                            self.imports_helper_dict["typing_extensions"] = set()
                        self.imports_helper_dict["typing_extensions"].add("TypeAlias")
                        stub = "%s: TypeAlias = %s\n" % (target_name, target_type)
                        self.stubs.append(stub)
                    elif not self.in_class:
                        stub = "%s = %s\n" % (target_name, target_type)
                        self.stubs.append(stub)
                elif isinstance(target, ast.Subscript):
                    if isinstance(target.value, ast.Name):
                        target_name = target.value.id
                    else:
                        continue
                    target_type = ast.unparse(node.value).strip()
                    stub = "%s: %s\n" % (target_name, target_type)
                    self.stubs.append(stub)

        def visit_MethodDef(self, node):
            args_list = []
            for arg in node.args.args:
                arg_type = self.get_arg_type(arg)
                args_list.append("%s: %s" % (arg.arg, arg_type))
            if node.returns:
                return_type = self.get_return_type(node.returns)
            else:
                return_type = "Any"
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("Any")
            indent = "    " * (self.indentation_level + 1)
            if node.name == "__init__":
                return_type = "None"
            if node.decorator_list:
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        if decorator.id == "classmethod":
                            args_list = args_list[1:]
                            stub = "%s@classmethod\n%sdef %s(cls, %s) -> %s: ...\n" % (indent, indent, node.name, ', '.join(args_list), return_type)
                            self.stubs.append(stub)
                            return
                        elif decorator.id == "staticmethod":
                            stub = "%s@staticmethod\n%sdef %s(%s) -> %s: ...\n" % (indent, indent, node.name, ', '.join(args_list), return_type)
                            self.stubs.append(stub)
                            return
                        else:
                            stub = "%sdef %s(%s) -> %s: ...\n" % (indent, node.name, ', '.join(args_list), return_type)
                            self.stubs.append(stub)
                            return
            stub = "%sdef %s(%s) -> %s: ...\n" % (indent, node.name, ', '.join(args_list), return_type)
            self.stubs.append(stub)

        def visit_RegularFunctionDef(self, node):
            args_list = []
            for arg in node.args.args:
                arg_type = self.get_arg_type(arg)
                args_list.append("%s: %s" % (arg.arg, arg_type))
            if node.returns:
                return_type = self.get_return_type(node.returns)
            else:
                return_type = "Any"
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("Any")
            stub = (
                "def %s(%s) -> %s:\n    ...\n" % (node.name, ', '.join(args_list), return_type)
            )
            self.stubs.append(stub)
            self.stubs.append("\n")

        def visit_ClassDef(self, node):
            previous_in_class = self.in_class
            self.in_class = True
            previous_indent = self.indentation_level
            if previous_in_class:
                self.indentation_level += 1
            class_name = node.name
            indent = "    " * self.indentation_level
            stub = ""
            case = self.special_cases(node)
            class_has_generic = False
            generic_types = []
            for base in node.bases:
                if (
                    isinstance(base, ast.Subscript)
                    and isinstance(base.value, ast.Name)
                    and (base.value.id == "Generic")
                ):
                    class_has_generic = True
                    if "typing" not in self.imports_helper_dict:
                        self.imports_helper_dict["typing"] = set()
                    self.imports_helper_dict["typing"].add("Generic")
                    if isinstance(base.slice, ast.Tuple):
                        for elt in base.slice.elts:
                            if isinstance(elt, ast.Name):
                                generic_types.append(elt.id)
                    elif isinstance(base.slice, ast.Name):
                        generic_types.append(base.slice.id)
                    for type_name in generic_types:
                        if type_name in self.typevars:
                            continue
                        self.typevars.add(type_name)
                        if "typing" not in self.imports_helper_dict:
                            self.imports_helper_dict["typing"] = set()
                        self.imports_helper_dict["typing"].add("TypeVar")
            if case == "TypedDict":
                stub = "%sclass %s(TypedDict):\n" % (indent, class_name)
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("TypedDict")
                for key in node.body:
                    if isinstance(key, ast.Assign):
                        for target in key.targets:
                            if isinstance(target, ast.Name):
                                target_name = target.id
                                target_type = ast.unparse(key.value).strip()
                                stub += "%s    %s: %s\n" % (indent, target_name, target_type)
                            elif isinstance(target, ast.Subscript):
                                if isinstance(target.value, ast.Name):
                                    target_name = target.value.id
                                target_type = ast.unparse(key.value).strip()
                                stub += "%s    %s: %s\n" % (indent, target_name, target_type)
                    elif isinstance(key, ast.AnnAssign):
                        target = key.target
                        if isinstance(target, ast.Name):
                            target_name = target.id
                            target_type = ast.unparse(key.annotation).strip()
                            stub += "%s    %s: %s\n" % (indent, target_name, target_type)
                        elif isinstance(target, ast.Subscript):
                            if isinstance(target.value, ast.Name):
                                target_name = target.value.id
                            target_type = ast.unparse(key.annotation).strip()
                            stub += "%s    %s: %s\n" % (indent, target_name, target_type)
            elif case == "Exception":
                if not any((isinstance(n, ast.FunctionDef) for n in node.body)):
                    stub = "%sclass %s(Exception): ..." % (indent, class_name)
                else:
                    stub = "%sclass %s(Exception):" % (indent, class_name)
            elif case == "NamedTuple":
                stub = "%sclass %s(NamedTuple):\n" % (indent, class_name)
                self.imports_output.add("from typing import NamedTuple")
            else:
                is_dataclass = any((isinstance(n, ast.AnnAssign) for n in node.body))
                if is_dataclass:
                    stub = "%s@dataclass\n" % indent
                    self.imports_output.add("from dataclasses import dataclass")
                class_def = "%sclass %s" % (indent, class_name)
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Subscript):
                        if (
                            isinstance(base.value, ast.Name)
                            and base.value.id == "Generic"
                        ):
                            continue
                        base_name = ast.unparse(base).strip()
                        bases.append(base_name)
                if class_has_generic:
                    bases.append("Generic[%s]" % ', '.join(generic_types))
                if bases:
                    class_def += "(%s)" % ', '.join(bases)
                class_def += ":"
                stub += class_def
            self.stubs.append(stub)
            methods_or_classes = [
                n for n in node.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
            ]
            if methods_or_classes:
                self.stubs.append("\n")
                class_nodes = []
                method_nodes = []
                for child in methods_or_classes:
                    if isinstance(child, ast.ClassDef):
                        class_nodes.append(child)
                    else:
                        method_nodes.append(child)
                for class_node in class_nodes:
                    self.visit(class_node)
                if class_nodes and method_nodes:
                    self.stubs.append("\n")
                for method_node in method_nodes:
                    self.visit(method_node)
            self.indentation_level = previous_indent
            self.in_class = previous_in_class
            if not previous_in_class:
                self.stubs.append("\n")

        def special_cases(self, node):
            for obj in node.bases:
                ob_instance = isinstance(obj, ast.Name)
                if ob_instance:
                    if obj.id == "TypedDict":
                        return "TypedDict"
                    elif obj.id == "Exception":
                        return "Exception"
                    elif obj.id == "NamedTuple":
                        return "NamedTuple"
                    else:
                        return False
            return False

        def get_arg_type(self, arg_node):
            selfs = ["self", "cls"]
            if arg_node.arg in selfs:
                if (
                    arg_node.arg == "self"
                    and "typing_extensions" not in self.imports_helper_dict
                ):
                    self.imports_helper_dict["typing_extensions"] = set()
                    self.imports_helper_dict["typing_extensions"].add("Self")
                return "Self" if arg_node.arg == "self" else arg_node.arg
            elif arg_node.annotation:
                unparsed = ast.unparse(arg_node.annotation).strip()
                if (
                    isinstance(arg_node.annotation, ast.Name)
                    and arg_node.annotation.id in self.typevars
                ):
                    return arg_node.annotation.id
                if unparsed.startswith("typing."):
                    type_name = unparsed.split(".")[-1]
                    if "typing" not in self.imports_helper_dict:
                        self.imports_helper_dict["typing"] = set()
                    self.imports_helper_dict["typing"].add(type_name)
                    return type_name
                return unparsed
            else:
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("Any")
                return "Any"

        def get_return_type(self, return_node):
            if return_node:
                unparsed = ast.unparse(return_node).strip()
                if (
                    isinstance(return_node, ast.Name)
                    and return_node.id in self.typevars
                ):
                    return return_node.id
                if unparsed.startswith("typing."):
                    type_name = unparsed.split(".")[-1]
                    if "typing" not in self.imports_helper_dict:
                        self.imports_helper_dict["typing"] = set()
                    self.imports_helper_dict["typing"].add(type_name)
                    return type_name
                return unparsed
            else:
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("Any")
                return "Any"

        def visit_AnnAssign(self, node):
            target = node.target
            if isinstance(node.annotation, ast.Name):
                target_type = node.annotation.id
            else:
                target_type = ast.unparse(node.annotation).strip()
                if target_type.startswith("typing."):
                    type_name = target_type.split(".")[-1]
                    if "typing" not in self.imports_helper_dict:
                        self.imports_helper_dict["typing"] = set()
                    self.imports_helper_dict["typing"].add(type_name)
                    target_type = type_name
            if not self.in_class:
                if isinstance(target, ast.Name):
                    target_name = target.id
                    if node.value is not None:
                        value_str = ast.unparse(node.value).strip()
                        stub = "%s: %s = %s\n" % (target_name, target_type, value_str)
                    else:
                        stub = "%s: %s\n" % (target_name, target_type)
                    self.stubs.append(stub)
                    return
            if self.in_class:
                indent = "    " * (self.indentation_level + 1)
                if isinstance(node.annotation, ast.Subscript):
                    if isinstance(target, ast.Name):
                        stub = "%s%s: %s\n" % (indent, target.id, target_type)
                    elif isinstance(target, ast.Subscript):
                        if isinstance(target.value, ast.Name):
                            target_name = target.value.id
                        stub = "%s%s: %s\n" % (indent, target_name, target_type)
                elif isinstance(node.annotation, ast.Name):
                    if isinstance(target, ast.Name):
                        stub = "%s%s: %s\n" % (indent, target.id, target_type)
                    elif isinstance(target, ast.Subscript):
                        if isinstance(target.value, ast.Name):
                            target_name = target.value.id
                        stub = "%s%s: %s\n" % (indent, target_name, target_type)
                elif isinstance(node.annotation, ast.BinOp):
                    if isinstance(target, ast.Name):
                        stub = "%s%s: %s\n" % (indent, target.id, target_type)
                    elif isinstance(target, ast.Subscript):
                        if isinstance(target.value, ast.Name):
                            target_name = target.value.id
                            stub = "%s%s: %s\n" % (indent, target_name, target_type)
                        else:
                            stub = "%s%s: %s\n" % (indent, ast.unparse(target), target_type)
                    else:
                        stub = "%s%s: %s\n" % (indent, ast.unparse(target), target_type)
                else:
                    raise NotImplementedError(
                        "Type %s not implemented, report this issue" % type(node.annotation)
                    )
                self.stubs.append(stub)

        def generate_imports(self):
            imports = []
            if sys.version_info >= (3, 7):
                imports.append("from __future__ import annotations\n")
            sorted_items = sorted(self.imports_helper_dict.items())
            for module, names in sorted_items:
                if names:
                    imports.append("from %s import %s\n" % (module, ', '.join(sorted(names))))
            for imp in sorted(self.imports_output):
                if imp != "from __future__ import annotations":
                    imports.append("%s\n" % imp)
            return "".join(imports) + "\n" if imports else ""

    stub_generator = StubGenerator()
    stub_generator.visit(tree)
    out_str = ""
    imports_str = stub_generator.generate_imports()
    if imports_str:
        out_str += imports_str
    for stub in stub_generator.stubs:
        out_str += stub
    if text_only:
        return out_str
    else:
        with open(output_file_path, "w") as output_file:
            output_file.write(out_str)
        return None


def generate_stub(source_file_path, output_file_path, text_only=False):
    with open(source_file_path, "r", encoding="utf-8") as source_file:
        source_code = source_file.read()
    return generate_stub_from_source(
        source_code=source_code, output_file_path=output_file_path, text_only=text_only
    )


def generate_text_stub(source_file_path):
    stubs = generate_stub(source_file_path, "", text_only=True)
    if stubs:
        return stubs
    else:
        raise ValueError("Stub generation failed")
