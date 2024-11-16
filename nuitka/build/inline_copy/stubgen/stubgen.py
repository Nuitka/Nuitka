from __future__ import annotations
import ast
import sys
import typing

if sys.version_info < (3, 9):
    from astunparse import unparse

    ast.unparse = unparse

def generate_stub_from_source(source_code, output_file_path, text_only=False):
    tree = ast.parse(source_code)

    class StubGenerator(ast.NodeVisitor):
        def __init__(self):
            self.stubs = []
            self.imports_helper_dict = {}
            self.imports_output = set()
            self.typing_imports = typing.__all__

        def visit_Import(self, node: ast.Import):
            for alias in node.names:
                self.imports_output.add(f"import {alias.name}")

        def visit_ImportFrom(self, node):
            module = node.module if node.module is not None else "."
            for alias in node.names:
                name = alias.name

                if module not in self.imports_helper_dict:
                    self.imports_helper_dict[module] = set()
                self.imports_helper_dict[module].add(name)

        def visit_FunctionDef(self, node):
            if any(isinstance(n, ast.ClassDef) for n in ast.walk(tree)):
                if self.is_method(node):
                    self.visit_MethodDef(node)
                else:
                    self.visit_RegularFunctionDef(node)
            else:
                self.visit_RegularFunctionDef(node)

        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    target_name = target.id
                    target_type = ast.unparse(node.value).strip()
                    if target_type in self.typing_imports:
                        self.imports_output.add(target_type)
                    if target_type in self.typing_imports:
                        stub = f"{target_name}: {target_type}\n"
                        self.stubs.append(stub)
                    else:
                        if isinstance(node.value, ast.Call):
                            if isinstance(node.value.func, ast.Name):
                                if node.value.func.id == "frozenset":
                                    stub = f"{target_name} = frozenset({', '.join([ast.unparse(arg).strip() for arg in node.value.args])})\n"
                                    self.stubs.append(stub)
                                elif node.value.func.id == "namedtuple":
                                    tuple_name = ast.unparse(node.value.args[0]).strip()

                                    stub = f"{target_name} =  namedtuple({tuple_name}, {', '.join([ast.unparse(arg).strip() for arg in node.value.args[1:]])})\n"
                                    self.stubs.append(stub)
                        elif isinstance(node.value, ast.Subscript):
                            if isinstance(node.value.value, ast.Name):
                                target_name = node.value.value.id
                            target_type = ast.unparse(node.value).strip()
                            if "typing_extensions" not in self.imports_helper_dict:
                                self.imports_helper_dict["typing_extensions"] = set()
                            self.imports_helper_dict["typing_extensions"].add(
                                "TypeAlias"
                            )
                            stub = f"{target_name}: TypeAlias = {target_type}\n"
                            self.stubs.append(stub)

                elif isinstance(target, ast.Subscript):
                    if isinstance(target.value, ast.Name):
                        target_name = target.value.id
                    else:
                        continue
                    target_type = ast.unparse(node.value).strip()
                    stub = f"{target_name}: {target_type}\n"
                    self.stubs.append(stub)

        def is_method(self, node):
            for parent_node in ast.walk(tree):
                if isinstance(parent_node, ast.ClassDef):
                    for child_node in parent_node.body:
                        if (
                            isinstance(child_node, ast.FunctionDef)
                            and child_node.name == node.name
                        ):
                            return True
            return False

        def visit_MethodDef(self, node):
            args_list = []
            for arg in node.args.args:
                arg_type = self.get_arg_type(arg)
                args_list.append(f"{arg.arg}: {arg_type}")
            if node.returns:
                return_type = self.get_return_type(node.returns)
            else:
                return_type = "typing.Any"

            if return_type in self.typing_imports:
                self.imports_output.add(return_type)
            # handle the case where the node.name is __init__, __init__ is a special case which always returns None
            if node.name == "__init__":
                return_type = "None"
            if node.decorator_list:
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        if decorator.id == "classmethod":
                            args_list = args_list[1:]
                            stub = f"    @classmethod\n    def {node.name}(cls, {', '.join(args_list)}) -> {return_type}: ...\n"

                            self.stubs.append(stub)
                            return

                        elif decorator.id == "staticmethod":
                            stub = f"    @staticmethod\n    def {node.name}({', '.join(args_list)}) -> {return_type}: ...\n"
                            self.stubs.append(stub)
                            return
                        else:
                            stub = f"    def {node.name}({', '.join(args_list)}) -> {return_type}: ...\n"
                            self.stubs.append(stub)
                            return
            stub = (
                f"    def {node.name}({', '.join(args_list)}) -> {return_type}: ...\n"
            )
            self.stubs.append(stub)

        def visit_RegularFunctionDef(self, node):
            args_list = []
            for arg in node.args.args:
                arg_type = self.get_arg_type(arg)
                args_list.append(f"{arg.arg}: {arg_type}")
            if node.returns:
                return_type = self.get_return_type(node.returns)
            else:
                return_type = "typing.Any"
            stub = (
                f"def {node.name}({', '.join(args_list)}) -> {return_type}:\n    ...\n"
            )
            self.stubs.append(stub)

        def visit_ClassDef(self, node):
            class_name = node.name
            stub = ""
            case = self.special_cases(node)
            if case == "TypedDict":
                stub = f"class {class_name}(TypedDict):\n"
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("TypedDict")
                for key in node.body:
                    if isinstance(key, ast.Assign):
                        for target in key.targets:
                            if isinstance(target, ast.Name):
                                target_name = target.id
                                target_type = ast.unparse(key.value).strip()
                                stub += f"    {target_name}: {target_type}\n"
                            elif isinstance(target, ast.Subscript):
                                if isinstance(target.value, ast.Name):
                                    target_name = target.value.id
                                target_type = ast.unparse(key.value).strip()
                                stub += f"    {target_name}: {target_type}\n"
                    elif isinstance(key, ast.AnnAssign):
                        target = key.target
                        if isinstance(target, ast.Name):
                            target_name = target.id
                            target_type = ast.unparse(key.annotation).strip()
                            stub += f"    {target_name}: {target_type}\n"
                        elif isinstance(target, ast.Subscript):
                            if isinstance(target.value, ast.Name):
                                target_name = target.value.id
                            target_type = ast.unparse(key.annotation).strip()
                            stub += f"    {target_name}: {target_type}\n"
                stub += "\n"
            elif case == "Exception":
                if not any(isinstance(n, ast.FunctionDef) for n in node.body):
                    stub = f"\nclass {class_name}(Exception): ..."
                else:
                    stub = f"\nclass {class_name}(Exception):"
            elif case == "NamedTuple":
                stub = f"class {class_name}(NamedTuple):\n"
                self.imports_output.add("from typing import NamedTuple")
            else:
                is_dataclass = any(isinstance(n, ast.AnnAssign) for n in node.body)
                if is_dataclass:
                    stub = "@dataclass\n"
                    self.imports_output.add("from dataclasses import dataclass")
                stub += f"class {class_name}:"

            self.stubs.append(stub)
            methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
            if methods:
                self.stubs.append("\n")
                for method in methods:
                    self.visit_FunctionDef(method)

        def special_cases(self, node):
            for obj in node.bases:
                ob_instance = isinstance(obj, ast.Name)
                if ob_instance:
                    if obj.id == "TypedDict":  # type: ignore
                        return "TypedDict"
                    elif obj.id == "Exception":  # type: ignore
                        return "Exception"
                    elif obj.id == "NamedTuple":  # type: ignore
                        return "NamedTuple"
                    else:
                        return False
            return False

        def get_arg_type(self, arg_node):
            selfs = ["self", "cls"]
            if arg_node.arg in selfs:
                if "typing_extensions" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing_extensions"] = set()
                self.imports_helper_dict["typing_extensions"].add("Self")
                return "Self"
            elif arg_node.annotation:
                unparsed = ast.unparse(arg_node.annotation).strip()
                return unparsed
            else:
                return "typing.Any"

        def get_return_type(self, return_node):
            if return_node:
                unparsed = ast.unparse(return_node).strip()
                return unparsed
            else:
                return "typing.Any"

        def visit_AnnAssign(self, node):
            target = node.target
            if isinstance(node.annotation, ast.Name):
                target_type = node.annotation.id
            else:
                target_type = ast.unparse(node.annotation).strip()

            if isinstance(node.annotation, ast.Subscript):
                if isinstance(target, ast.Name):
                    stub = f"{target.id}: {target_type}\n"
                elif isinstance(target, ast.Name):
                    stub = f"{target.id}: {target_type}\n"
            elif isinstance(node.annotation, ast.Name):
                if isinstance(target, ast.Name):
                    stub = f"{target.id}: {target_type}\n"
                elif isinstance(target, ast.Subscript):
                    if isinstance(target.value, ast.Name):
                        target_name = target.value.id
                    stub = f"{target_name}: {target_type}\n"
            else:
                raise NotImplementedError(
                    f"Type {type(node.annotation)} not implemented, report this issue"
                )

            self.stubs.append(stub)

        def generate_imports(self):
            imports_helper = set()
            sorted_items = sorted(self.imports_helper_dict.items())
            for module, names in sorted_items:
                imports_helper.add(f"from {module} import {', '.join(sorted(names))}")

            imports_helper.update(self.imports_output)

            self.imports_output.add("from __future__ import annotations")

            imports = "".join([f"{imp}\n" for imp in imports_helper])

            return imports + "\n"

    stub_generator = StubGenerator()
    stub_generator.visit(tree)
    out_str = ""
    sempt = stub_generator.generate_imports()
    if sempt:
        out_str += sempt
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

    return generate_stub_from_source(source_code=source_code, output_file_path=output_file_path, text_only=text_only)


def generate_text_stub(source_file_path):
    stubs = generate_stub(source_file_path, "", text_only=True)
    if stubs:
        return stubs
    else:
        raise ValueError("Stub generation failed")
