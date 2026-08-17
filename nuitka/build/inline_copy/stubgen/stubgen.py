import ast
import re
import sys
from collections import OrderedDict

if sys.version_info < (3, 9):
    # Nuitka imports this file from the inline copy folder, temporarily adding
    # that folder to `sys.path`, so `import astunparse` resolves next to us.
    import astunparse

    _ast_unparse = astunparse.unparse
else:
    _ast_unparse = ast.unparse

TYPING_MODULES = frozenset({"typing", "typing_extensions"})
TYPEVAR_LIKE = frozenset({"TypeVar", "ParamSpec", "TypeVarTuple"})
PRESERVED_FUNCTION_DECORATORS = frozenset({"classmethod", "staticmethod", "property"})
KNOWN_TYPING_NAMES = frozenset(
    {
        "Any",
        "Optional",
        "Union",
        "List",
        "Dict",
        "Set",
        "Tuple",
        "TypeVar",
        "Generic",
        "Callable",
        "Iterable",
        "Iterator",
        "Generator",
        "Type",
        "AnyStr",
        "cast",
        "overload",
        "FrozenSet",
        "Mapping",
        "MutableMapping",
        "Sequence",
        "MutableSequence",
        "AbstractSet",
        "MutableSet",
        "TypeAlias",
        "Literal",
        "Annotated",
        "Protocol",
        "TypedDict",
        "NamedTuple",
        "ClassVar",
        "Final",
        "Text",
        "TYPE_CHECKING",
    }
)

AST_CONSTANT = getattr(ast, "Constant", ())
AST_STR = getattr(ast, "Str", ())
AST_NAME_CONSTANT = getattr(ast, "NameConstant", ())
AST_NUM = getattr(ast, "Num", ())
AST_ANN_ASSIGN = getattr(ast, "AnnAssign", ())
AST_ASYNC_FUNCTION_DEF = getattr(ast, "AsyncFunctionDef", ())

_IDENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")


def _max_lineno(node):
    return max((getattr(n, "lineno", 0) for n in ast.walk(node)), default=0)


class Source:
    def __init__(self, text):
        self.text = text
        self.lines = text.splitlines(keepends=True)

    def segment(self, node):
        get_segment = getattr(ast, "get_source_segment", None)
        if get_segment is not None:
            segment = get_segment(self.text, node)
            if segment is not None:
                return segment
        lineno = getattr(node, "lineno", None)
        if lineno is None:
            return ""
        start_line = lineno - 1
        col_offset = getattr(node, "col_offset", 0)
        end_lineno = getattr(node, "end_lineno", None) or _max_lineno(node)
        if end_lineno > lineno:
            lines = self.lines[start_line:end_lineno]
            first = lines[0][col_offset:]
            rest = [l[col_offset:] if l.startswith(" " * col_offset) else l.lstrip(" ") for l in lines[1:]]
            return first + "".join(rest)
        line = self.lines[start_line]
        return line[col_offset:].split("\n")[0]


class ImportInfo:
    def __init__(self):
        self.from_imports = OrderedDict()
        self.imports = OrderedDict()
        self.typing_names = set()
        self.typing_modules = set()
        self.imported_names = set()

    def add_import(self, module, alias=None):
        self.imports[module] = alias
        local_name = alias or module.split(".", maxsplit=1)[0]
        self.imported_names.add(local_name)
        if module in TYPING_MODULES:
            self.typing_modules.add(alias or module)

    def add_from_import(self, module, name, alias=None):
        self.from_imports.setdefault(module, OrderedDict())[name] = alias
        self.imported_names.add(alias or name)
        if module in TYPING_MODULES:
            self.typing_names.add(alias or name)

    def need_typing(self, name):
        self.add_from_import("typing", name)

    def render(self):
        lines = []
        for module, names in self.from_imports.items():
            rendered = []
            for name in sorted(names.keys()):
                alias = names[name]
                rendered.append(name if alias is None else "%s as %s" % (name, alias))
            lines.append("from %s import %s" % (module, ", ".join(rendered)))
        for module, alias in self.imports.items():
            lines.append("import %s" % module if alias is None else "import %s as %s" % (module, alias))
        return lines


def dotted_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        if base is None:
            return None
        return "%s.%s" % (base, node.attr)
    return None


def call_name(node):
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return None


def decorator_name(node):
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return dotted_name(node)


def is_main_guard(test):
    # Fast-path the most common shape(s) without a full tree walk.
    if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
        left = test.left
        comparators = test.comparators

        if isinstance(left, ast.Name) and left.id == "__name__":
            for comparator in comparators:
                if isinstance(comparator, AST_CONSTANT) and comparator.value == "__main__":
                    return True
                if isinstance(comparator, AST_STR) and comparator.s == "__main__":
                    return True

        # Also allow reversed order: "__main__" == __name__
        if (isinstance(left, AST_CONSTANT) and left.value == "__main__") or (
            isinstance(left, AST_STR) and left.s == "__main__"
        ):
            for comparator in comparators:
                if isinstance(comparator, ast.Name) and comparator.id == "__name__":
                    return True

    for node in ast.walk(test):
        if not isinstance(node, ast.Compare):
            continue
        if not isinstance(node.left, ast.Name) or node.left.id != "__name__":
            continue
        for comparator in node.comparators:
            if isinstance(comparator, AST_CONSTANT) and comparator.value == "__main__":
                return True
            if isinstance(comparator, AST_STR) and comparator.s == "__main__":
                return True
    return False


def static_string(source, node):
    if isinstance(node, AST_CONSTANT) and isinstance(node.value, str):
        return node.value
    if isinstance(node, AST_STR):
        return node.s
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = static_string(source, node.left)
        right = static_string(source, node.right)
        if left is not None and right is not None:
            return left + right
    return None


def static_all_names(source, node):
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return None
    names = set()
    for elt in node.elts:
        value = static_string(source, elt)
        if value is None:
            return None
        names.add(value)
    return names

def extract_exported_names(tree, source):
    accumulated = None
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and any((isinstance(t, ast.Name) and t.id == "__all__" for t in stmt.targets)):
            names = static_all_names(source, stmt.value)
            if names is not None:
                accumulated = names if accumulated is None else accumulated | names
        elif isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name) and (stmt.target.id == "__all__"):
            names = static_all_names(source, stmt.value)
            if names is not None:
                if accumulated is None:
                    accumulated = set()
                accumulated |= names
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if not isinstance(call.func, ast.Attribute):
                continue
            if not isinstance(call.func.value, ast.Name) or call.func.value.id != "__all__" or len(call.args) != 1:
                continue
            if call.func.attr == "extend":
                names = static_all_names(source, call.args[0])
                if names is not None:
                    if accumulated is None:
                        accumulated = set()
                    accumulated |= names
            elif call.func.attr == "append":
                name = static_string(source, call.args[0])
                if name is not None:
                    if accumulated is None:
                        accumulated = set()
                    accumulated.add(name)
    return frozenset(accumulated) if accumulated is not None else None


def _has_base(node, name):
    return any(isinstance(base, ast.Name) and base.id == name for base in node.bases)


def is_exception(node):
    return _has_base(node, "Exception")


def is_typed_dict(node):
    return _has_base(node, "TypedDict")


def is_named_tuple(node):
    return _has_base(node, "NamedTuple")


def _split_type_args(text):
    """Split on commas, but not inside ``[]`` brackets."""
    parts = []
    depth = 0
    current = []
    for ch in text:
        if ch == "[":
            depth += 1
            current.append(ch)
        elif ch == "]":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    remaining = "".join(current).strip()
    if remaining:
        parts.append(remaining)
    return parts


class StubRenderer:
    def __init__(self, source_text):
        self.source = Source(source_text)
        kwargs = {}
        if sys.version_info >= (3, 8):
            kwargs["type_comments"] = True
        self.tree = ast.parse(source_text, **kwargs)
        self.exported = extract_exported_names(self.tree, self.source)
        self.imports = ImportInfo()
        self._overloaded_stack = [set()]
        self._in_class = False

    def render(self):
        body = self.render_body(self.tree.body, indent="", module_scope=True)
        used_names = set()
        if self.exported is not None:
            used_names.update(self.exported)

        # Avoid parsing the rendered stub output. Instead, do a quick identifier
        # scan over the emitted lines. This is conservative (may keep extra
        # imports) but is stable and much faster than parse+walk.
        for line in body:
            for ident in _IDENT_RE.findall(line):
                used_names.add(ident)

        body_str = "\n".join(body)
        import_lines = ["from __future__ import annotations"]
        pruned_from_imports = OrderedDict()
        for module, names in self.imports.from_imports.items():
            pruned_names = OrderedDict()
            for name, alias in names.items():
                local_name = alias or name
                force_alias = False
                if self.exported is not None and local_name in self.exported and (alias is None):
                    if module not in TYPING_MODULES:
                        alias = name
                        force_alias = True
                is_reexport = alias is not None and alias == name
                if local_name in used_names or is_reexport:
                    pruned_names[name] = alias
            if pruned_names:
                pruned_from_imports[module] = pruned_names
        pruned_imports = OrderedDict()
        for module, alias in self.imports.imports.items():
            local_name = alias or module.split(".")[0]
            if local_name in used_names:
                pruned_imports[module] = alias
        rendered_from = []
        for module, names in pruned_from_imports.items():
            rendered = []
            for name in sorted(names.keys()):
                alias = names[name]
                rendered.append(name if alias is None else "%s as %s" % (name, alias))
            rendered_from.append("from %s import %s" % (module, ", ".join(rendered)))
        rendered_imports = []
        for module, alias in pruned_imports.items():
            rendered_imports.append("import %s" % module if alias is None else "import %s as %s" % (module, alias))
        import_lines.extend(rendered_from)
        import_lines.extend(rendered_imports)
        if self.exported is not None:
            all_list = ", ".join(('"%s"' % name for name in sorted(self.exported)))
            if len(import_lines) > 1:
                import_lines.append("")
            import_lines.append("__all__ = [%s]" % all_list)
        if len(import_lines) > 1:
            return "\n".join(import_lines) + "\n\n\n" + body_str.rstrip() + "\n"
        return import_lines[0] + "\n" + ("\n" + body_str.rstrip() + "\n" if body_str else "")

    def _note_typing_names_in_text(self, text):
        for ident in _IDENT_RE.findall(text):
            if ident in KNOWN_TYPING_NAMES and ident not in self.imports.imported_names:
                self.imports.need_typing(ident)

    def is_exported(self, name):
        return self.exported is None or name in self.exported or name == "__all__"

    def render_body(self, body, indent, module_scope=False):
        self._overloaded_stack.append(set())
        lines = []
        previous_stmt = None
        for stmt in body:
            if isinstance(stmt, ast.If) and is_main_guard(stmt.test):
                continue
            if isinstance(stmt, (ast.FunctionDef, AST_ASYNC_FUNCTION_DEF)):
                has_overload = False
                for decorator in stmt.decorator_list:
                    name = decorator_name(decorator)
                    if name in ("overload", "typing.overload", "typing_extensions.overload"):
                        has_overload = True
                        break
                if has_overload:
                    self._overloaded_stack[-1].add(stmt.name)
                elif stmt.name in self._overloaded_stack[-1]:
                    continue
            rendered = self.render_stmt(stmt, indent, module_scope)
            if lines and previous_stmt is not None:
                lines.extend(self.separator(previous_stmt, stmt, module_scope))
            lines.extend(rendered)
            previous_stmt = stmt
        self._overloaded_stack.pop()
        return lines

    def get_type_comment(self, stmt):
        type_comment = getattr(stmt, "type_comment", None)
        if type_comment:
            return type_comment
        start_line = getattr(stmt, "lineno", None)
        if start_line is None:
            return None
        if isinstance(stmt, ast.Assign):
            line = self.source.lines[start_line - 1]
            match = re.search("#\\s*type:\\s*(.*)$", line)
            return match.group(1).strip() if match else None
        if isinstance(stmt, (ast.FunctionDef, AST_ASYNC_FUNCTION_DEF)):
            # Note: On Python < 3.8, `lineno` for a function can point at the
            # first decorator rather than the `def` line. We scan forward, but
            # we must not stop at the `def` line itself.
            saw_signature = False
            for i in range(start_line - 1, min(start_line + 20, len(self.source.lines))):
                line = self.source.lines[i]
                if "# type:" in line:
                    match = re.search("#\\s*type:\\s*(.*)$", line)
                    if match:
                        return match.group(1).strip()

                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue

                # Keep scanning past the function signature line.
                if stripped.startswith("@"):
                    continue
                if stripped.startswith("def ") or stripped.startswith("async def "):
                    if not saw_signature:
                        saw_signature = True
                        continue
                    # Nested function/class definition reached.
                    break

                # First real statement reached without a type comment.
                break
        return None

    def separator(self, previous_stmt, stmt, module_scope):
        if module_scope:
            if self.is_simple_variable(previous_stmt) and self.is_simple_variable(stmt):
                return []
            return ["", ""]
        if self.is_simple_variable(previous_stmt) and self.is_simple_variable(stmt):
            return []
        return [""]

    def is_simple_variable(self, stmt):
        if isinstance(stmt, AST_ANN_ASSIGN):
            return True
        return isinstance(stmt, ast.Assign) and (
            not (len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name) and (stmt.targets[0].id == "__all__"))
        )

    def render_stmt(self, stmt, indent, module_scope):
        if isinstance(stmt, ast.ImportFrom):
            return self.render_import_from(stmt, indent, module_scope)
        if isinstance(stmt, ast.Import):
            return self.render_import(stmt, indent, module_scope)
        if isinstance(stmt, (ast.FunctionDef, AST_ASYNC_FUNCTION_DEF)):
            return self.render_function(stmt, indent, module_scope)
        if isinstance(stmt, ast.ClassDef):
            return self.render_class(stmt, indent, module_scope)
        if isinstance(stmt, AST_ANN_ASSIGN):
            return self.render_ann_assign(stmt, indent, module_scope)
        if isinstance(stmt, ast.Assign):
            return self.render_assign(stmt, indent, module_scope)
        if isinstance(stmt, ast.If):
            return self.render_if(stmt, indent, module_scope)
        if isinstance(stmt, ast.Try):
            return self._render_raw_block(stmt, indent)
        if isinstance(stmt, (ast.Pass, ast.Expr)) and self.is_placeholder(stmt):
            return [indent + "..."]
        return []

    def is_placeholder(self, stmt):
        if isinstance(stmt, ast.Pass):
            return True
        if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, (AST_CONSTANT, getattr(ast, "Ellipsis", ())))):
            return False
        if isinstance(stmt.value, AST_CONSTANT):
            return getattr(stmt.value, "value", None) is Ellipsis
        return True

    def render_import(self, stmt, indent, module_scope):
        if not module_scope:
            return [indent + self.source.segment(stmt).strip()]
        for alias in stmt.names:
            self.imports.add_import(alias.name, alias.asname)
        return []

    def render_import_from(self, stmt, indent, module_scope):
        if stmt.module == "__future__" or any((alias.name == "*" for alias in stmt.names)):
            return []
        if not module_scope:
            return [indent + self.source.segment(stmt).strip()]
        level = getattr(stmt, "level", 0)
        dots = "." * level if level else ""
        module = dots + (stmt.module or "")
        for alias in stmt.names:
            self.imports.add_from_import(module, alias.name, alias.asname)
        return []

    def render_decorators(self, decorators, indent, for_function):
        lines = []
        for decorator in decorators:
            name = decorator_name(decorator)
            if for_function and name is not None and (name.rsplit(".", 1)[-1] not in PRESERVED_FUNCTION_DECORATORS):
                if name.rsplit(".", 1)[-1] != "overload" and "contextmanager" not in name:
                    lines.append(indent + "@" + self.source.segment(decorator).strip())
                    continue
            lines.append(indent + "@" + self.rewrite_annotation(decorator))
        return lines

    def render_class(self, stmt, indent, module_scope):
        if module_scope and (not self.is_exported(stmt.name)):
            return []
        decorators = self.render_decorators(stmt.decorator_list, indent, for_function=False)
        if is_typed_dict(stmt):
            self.imports.need_typing("TypedDict")
            bases_and_keywords = []
            for base in stmt.bases:
                bases_and_keywords.append(self.rewrite_annotation(base))
            for kw in stmt.keywords:
                bases_and_keywords.append("%s=%s" % (kw.arg, self.rewrite_annotation(kw.value)))
            suffix = "(%s)" % ", ".join(bases_and_keywords) if bases_and_keywords else ""
            header = indent + "class %s%s:" % (stmt.name, suffix)
            body = []
            for item in stmt.body:
                if isinstance(item, AST_ANN_ASSIGN):
                    rendered = self.render_ann_assign(item, indent + "    ", False)
                    if rendered:
                        body.extend(rendered)
                elif isinstance(item, ast.Assign):
                    for target_node in item.targets:
                        target = dotted_name(target_node) or self.source.segment(target_node).strip()
                        ann = self.rewrite_annotation(item.value)
                        body.append(indent + "    %s: %s" % (target, ann))
            if not body:
                return decorators + [header + " ..."]
            return decorators + [header] + body
        if is_named_tuple(stmt):
            self.imports.need_typing("NamedTuple")
        bases = [self.rewrite_annotation(base) for base in stmt.bases]
        for keyword in stmt.keywords:
            bases.append("%s=%s" % (keyword.arg, self.source.segment(keyword.value).strip()))
        header = indent + "class %s" % stmt.name
        if bases:
            header += "(%s)" % ", ".join(bases)
        header += ":"
        old_in_class = self._in_class
        self._in_class = True
        body = self.render_body(stmt.body, indent + "    ", module_scope=False)
        self._in_class = old_in_class
        if not body:
            return decorators + [header + " ..."]
        return decorators + [header] + body

    def render_arg(self, arg, default, skip_any, type_override=None):
        text = arg.arg
        type_comment = getattr(arg, "type_comment", None)
        if arg.annotation is not None:
            text += ": " + self.rewrite_annotation(arg.annotation)
        elif type_override:
            text += ": " + type_override
        elif type_comment:
            text += ": " + type_comment
        elif not skip_any:
            self.imports.need_typing("Any")
            text += ": Any"
        if default is not None:
            text += " = ..."
        return text

    def is_multiline_signature(self, stmt):
        args = self.rendered_ast_args(stmt.args)
        signature_lineno = getattr(stmt, "lineno", 0)
        # On Python < 3.8, decorated functions can have `lineno` pointing at the
        # first decorator. In that case, use the arg line numbers (usually the
        # actual `def` line) as the signature baseline.
        if getattr(stmt, "decorator_list", None):
            signature_lineno = (
                max(getattr(arg, "lineno", signature_lineno) for arg in args) if args else signature_lineno
            )
        for arg in args:
            if getattr(arg, "lineno", signature_lineno) != signature_lineno:
                return True
        return False

    def rendered_ast_args(self, args):
        rendered = list(getattr(args, "posonlyargs", [])) + list(args.args) + list(args.kwonlyargs)
        if args.vararg is not None:
            rendered.append(args.vararg)
        if args.kwarg is not None:
            rendered.append(args.kwarg)
        return rendered

    def render_argument_list(self, args, arg_types_from_comment):
        rendered = []
        posonlyargs = list(getattr(args, "posonlyargs", []))
        positional = posonlyargs + list(args.args)
        defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
        for index, (arg, default) in enumerate(zip(positional, defaults)):
            override = arg_types_from_comment.get(arg.arg)
            rendered.append(self.render_arg(arg, default, skip_any=arg.arg in ("self", "cls"), type_override=override))
            if posonlyargs and index == len(posonlyargs) - 1:
                rendered.append("/")
        if args.vararg is not None:
            override = arg_types_from_comment.get(args.vararg.arg)
            rendered.append("*" + self.render_arg(args.vararg, None, skip_any=False, type_override=override))
        elif args.kwonlyargs:
            rendered.append("*")
        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            override = arg_types_from_comment.get(arg.arg)
            rendered.append(self.render_arg(arg, default, skip_any=False, type_override=override))
        if args.kwarg is not None:
            override = arg_types_from_comment.get(args.kwarg.arg)
            rendered.append("**" + self.render_arg(args.kwarg, None, skip_any=False, type_override=override))
        return rendered

    def render_function(self, stmt, indent, module_scope):
        if module_scope and (not self.is_exported(stmt.name)):
            return []
        dec_lines = self.render_decorators(stmt.decorator_list, indent, for_function=True)
        arg_types_from_comment = {}
        returns_from_comment = None
        type_comment = self.get_type_comment(stmt)
        if type_comment:
            try:
                if sys.version_info >= (3, 8):
                    ftype = ast.parse(type_comment, mode="func_type")
                    returns_from_comment = self.rewrite_annotation(ftype.returns, synthetic=True)
                    if returns_from_comment == "...":
                        returns_from_comment = None
                    comment_arg_types = ftype.argtypes
                else:
                    if "->" in type_comment:
                        args_part, returns_part = type_comment.split("->", 1)
                        returns_from_comment = returns_part.strip()
                        if returns_from_comment == "...":
                            returns_from_comment = None
                        args_str = args_part.strip().strip("()")
                        if args_str == "...":
                            comment_arg_types = [ast.Ellipsis()]
                        else:
                            comment_arg_types = _split_type_args(args_str)
                    else:
                        comment_arg_types = []
                    if returns_from_comment:
                        if "Any" in returns_from_comment:
                            self.imports.need_typing("Any")
                        if "Optional" in returns_from_comment:
                            self.imports.need_typing("Optional")
                is_method = self._in_class
                ast_args = self.rendered_ast_args(stmt.args)
                if not (
                    len(comment_arg_types) == 1
                    and isinstance(comment_arg_types[0], AST_CONSTANT)
                    and (comment_arg_types[0].value is Ellipsis)
                ):
                    if is_method and len(ast_args) > 0 and (ast_args[0].arg in ("self", "cls")):
                        for i, t_node in enumerate(comment_arg_types):
                            if i + 1 < len(ast_args):
                                name = ast_args[i + 1].arg
                                if isinstance(t_node, str):
                                    t_str = t_node
                                    self._note_typing_names_in_text(t_str)
                                else:
                                    t_str = self.rewrite_annotation(t_node, synthetic=True)
                                arg_types_from_comment[name] = t_str
                    else:
                        for i, t_node in enumerate(comment_arg_types):
                            if i < len(ast_args):
                                name = ast_args[i].arg
                                if isinstance(t_node, str):
                                    t_str = t_node
                                    self._note_typing_names_in_text(t_str)
                                else:
                                    t_str = self.rewrite_annotation(t_node, synthetic=True)
                                arg_types_from_comment[name] = t_str
            except Exception:
                if "->" in type_comment:
                    returns_from_comment = type_comment.split("->")[-1].strip()
        args = ", ".join(self.render_argument_list(stmt.args, arg_types_from_comment))
        returns = " -> Any"
        if returns_from_comment is not None:
            returns = " -> " + returns_from_comment
        elif getattr(stmt, "returns", None) is not None:
            returns = " -> " + self.rewrite_annotation(stmt.returns)
        elif stmt.name == "__init__":
            returns = " -> None"
        if returns == " -> Any":
            self.imports.need_typing("Any")
        prefix = "async def " if isinstance(stmt, AST_ASYNC_FUNCTION_DEF) else "def "
        if self.is_multiline_signature(stmt):
            return (
                dec_lines
                + [indent + "%s%s(" % (prefix, stmt.name)]
                + [indent + "    " + arg + "," for arg in self.render_argument_list(stmt.args, arg_types_from_comment)]
                + [indent + ")%s: ..." % returns]
            )
        return dec_lines + [indent + "%s%s(%s)%s: ..." % (prefix, stmt.name, args, returns)]

    def render_ann_assign(self, stmt, indent, module_scope):
        if module_scope and isinstance(stmt.target, ast.Name) and (not self.is_exported(stmt.target.id)):
            return []
        # Use dotted_name to avoid greedy line extraction on Python < 3.8 where
        # ast.get_source_segment is unavailable and end_col_offset is not set.
        target = dotted_name(stmt.target)
        if target is None:
            target = self.source.segment(stmt.target).strip()
        ann = self.rewrite_annotation(stmt.annotation)
        suffix = " = ..." if stmt.value is not None else ""
        return [indent + "%s: %s%s" % (target, ann, suffix)]

    def render_assign(self, stmt, indent, module_scope):
        target_name = stmt.targets[0].id if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name) else None
        if module_scope and target_name is not None and (not self.is_exported(target_name)):
            return []
        if target_name == "__all__":
            if self.exported is not None:
                return []
            return [indent + self.source.segment(stmt).strip()]
        call = call_name(stmt.value)
        effective = call.rsplit(".", 1)[-1] if call else None
        if effective in TYPEVAR_LIKE:
            self.imports.need_typing(effective)
            return [indent + self.source.segment(stmt).strip()]
        if effective == "namedtuple":
            self.imports.add_from_import("collections", "namedtuple")
            return [indent + self.source.segment(stmt).strip()]
        if effective == "frozenset":
            return [indent + self.source.segment(stmt).strip()]
        if target_name is not None:
            type_comment = self.get_type_comment(stmt)
            if type_comment:
                if "Any" in type_comment:
                    self.imports.need_typing("Any")
                if "Optional" in type_comment:
                    self.imports.need_typing("Optional")
                return [indent + "%s: %s = ..." % (target_name, type_comment)]
            if self.is_typing_expr(stmt.value):
                return [indent + "%s: %s" % (target_name, self.rewrite_annotation(stmt.value))]
        return [indent + self.source.segment(stmt).strip()]

    def _render_raw_block(self, stmt, indent):
        segment = self.source.segment(stmt)
        lines = segment.rstrip().splitlines()
        if not lines:
            return []
        col_offset = getattr(stmt, "col_offset", 0)
        adjusted_lines = []
        for i, line in enumerate(lines):
            if i == 0:
                adjusted_lines.append(indent + line)
            else:
                if col_offset > 0:
                    if line.startswith(" " * col_offset):
                        adjusted_line = line[col_offset:]
                    else:
                        adjusted_line = line.lstrip(" ")
                else:
                    adjusted_line = line
                if not adjusted_line:
                    adjusted_lines.append("")
                else:
                    adjusted_lines.append(indent + adjusted_line)
        return adjusted_lines

    def render_if(self, stmt, indent, module_scope):
        if is_main_guard(stmt.test):
            return []
        return self._render_raw_block(stmt, indent)

    def is_typing_expr(self, node):
        root = node
        while isinstance(root, ast.Subscript):
            root = root.value
        name = dotted_name(root)
        if name is None:
            return False
        if "." in name:
            return name.split(".", 1)[0] in self.imports.typing_modules
        return name in self.imports.typing_names or name in KNOWN_TYPING_NAMES

    def rewrite_annotation(self, node, synthetic=False):
        if node is None:
            return "Any"
        if isinstance(node, str):
            return node
        if isinstance(node, AST_CONSTANT):
            if node.value is None:
                return "None"
            if node.value is Ellipsis:
                return "..."
            return repr(node.value)
        if isinstance(node, AST_STR):
            return repr(node.s)
        # Python 3.5-3.7 constant node types not covered by AST_CONSTANT
        if isinstance(node, AST_NAME_CONSTANT):
            return repr(node.value)
        if isinstance(node, AST_NUM):
            return repr(node.n)
        name = dotted_name(node)
        if name is not None:
            if "." in name:
                module, attr = name.split(".", 1)
                if module in self.imports.typing_modules and attr:
                    self.imports.need_typing(attr)
                    return attr
            elif name in self.imports.typing_names or (
                name in KNOWN_TYPING_NAMES and name not in self.imports.imported_names
            ):
                self.imports.need_typing(name)
            return name
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return "%s | %s" % (
                self.rewrite_annotation(node.left, synthetic=synthetic),
                self.rewrite_annotation(node.right, synthetic=synthetic),
            )
        if isinstance(node, ast.Subscript):
            root_name = dotted_name(node.value)
            if root_name is not None:
                if "." in root_name:
                    module, attr = root_name.split(".", 1)
                    if module in self.imports.typing_modules:
                        self.imports.need_typing(attr)
                        root_name = attr
                elif root_name in self.imports.typing_names or (
                    root_name in KNOWN_TYPING_NAMES and root_name not in self.imports.imported_names
                ):
                    self.imports.need_typing(root_name)
                if type(node.slice).__name__ == "Index":
                    slice_node = node.slice.value
                else:
                    slice_node = node.slice
                return "%s[%s]" % (root_name, self.rewrite_slice(slice_node, synthetic=synthetic))
        try:
            return _ast_unparse(node).strip()
        except (AttributeError, Exception):
            if isinstance(node, ast.Name):
                return node.id
            return "Any"

    def rewrite_slice(self, node, synthetic=False):
        if isinstance(node, ast.Tuple):
            if not node.elts:
                return "()"
            return ", ".join((self.rewrite_annotation(elt, synthetic=synthetic) for elt in node.elts))
        return self.rewrite_annotation(node, synthetic=synthetic)


def generate_stub_from_source(source_code, output_file_path=None, text_only=True):
    result = StubRenderer(source_code).render()
    if output_file_path is not None:
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(result)
    return result