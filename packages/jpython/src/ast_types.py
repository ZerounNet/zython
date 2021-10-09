# vim:fileencoding=utf-8
# License: BSD Copyright: 2016, Kovid Goyal <kovid at kovidgoyal.net>
from __python__ import hash_literals

from utils import noop
from js import js_instanceof, js_new

def is_node_type(node, typ):
    return js_instanceof(node, typ)

# Basic classes

class AST:

    properties = {}

    def __init__(self, initializer):
        # Walk the prototype change and copy all defined properties from the
        # initializer object
        if initializer:
            obj = self
            while True:
                obj = Object.getPrototypeOf(obj)
                if obj is None:
                    break
                if obj.properties:
                    for i in obj.properties:
                        self[i] = initializer[i]

    def clone(self):
        return js_new(self.constructor(self))


class AST_Token(AST):
    ' Tokens generated by the tokenizer in the first stage of parsing '
    properties = {
        'type': 'The type of the token',
        'value': 'The value of the token',
        'line': 'The line number at which the token occurs',
        'col': 'The column number at which the token occurs',
        'pos': '',
        'endpos': '',
        'nlb':'True iff there was a newline before this token',
        'comments_before':'True iff there were comments before this token',
        'file':'The filename in which this token occurs',
        'leading_whitespace': 'The leading whitespace for the line on which this token occurs',
    }

class AST_Node(AST):
    "Base class of all AST nodes"
    properties = {
        'start': "[AST_Token] The first token of this node",
        'end': "[AST_Token] The last token of this node"
    }

    def _walk(self, visitor):
        return visitor._visit(self)

    def walk(self, visitor):
        return self._walk(visitor)

    def _dump(self, depth=100, omit={'start', 'end'}, offset=0, include_name=True):
        p = console.log
        reset = "\x1b[0m"
        yellow = "\x1b[33m"
        blue = "\x1b[34m"
        green = "\x1b[32m"
        red = "\x1b[31m"
        magenta = "\x1b[35m"
        pad = Array(offset + 1).join('  ')

        if include_name:
            p(pad + yellow + self.constructor.name.slice(4) + reset)
        for key in self:
            if key in omit:
                continue

            if Array.isArray(self[key]):
                if self[key].length:
                    p(pad + ' ' + blue + key + ': ' + reset + '[')
                    if depth > 1:
                        for element in self[key]:
                            element._dump(depth-1, omit, offset+1, True)
                    else:
                        for element in self[key]:
                            p(pad + '   ' + yellow + element.constructor.name.slice(4) + reset)
                    p(pad + ' ]')
                else:
                    p(pad + ' ' + blue + key + ': ' + reset + '[]')
            elif self[key]:
                if is_node_type(self[key], AST):
                    tname = self[key].constructor.name.slice(4)
                    if tname is 'Token':
                        p(pad + ' ' + blue + key + ': ' + magenta + tname + reset)
                        for property in self[key]:
                            p(pad + '   ' + blue + property + ': ' + reset + self[key][property])
                    else:
                        p(pad + ' ' + blue + key + ': ' + yellow + tname + reset)
                        if depth > 1:
                            self[key]._dump(depth-1, omit, offset+1, False)
                elif jstype(self[key]) is "string":
                    p(pad + ' ' + blue + key + ': ' + green + '"' + self[key] + '"' + reset)
                elif jstype(self[key]) is "number":
                    p(pad + ' ' + blue + key + ': ' + green + self[key] + reset)
                else:
                    # unexpected object
                    p(pad + ' ' + blue + key + ': ' + red + self[key] + reset)
            else:
                # none/undefined
                p(pad + ' ' + blue + key + ': ' + reset + self[key])

    def dump(self, depth=2, omit={}):
        ' a more user-friendly way to dump the AST tree than console.log'
        return self._dump(depth, omit, 0, True)

# Statements

class AST_Statement(AST_Node):
    "Base class of all statements"

class AST_Debugger(AST_Statement):
    "Represents a debugger statement"

class AST_Directive(AST_Statement):
    'Represents a directive, like "use strict";'
    properties = {
        'value': "[string] The value of this directive as a plain string (it's not an AST_String!)",
        'scope': "[AST_Scope/S] The scope that this directive affects"
    }

class AST_SimpleStatement(AST_Statement):
    "A statement consisting of an expression, i.e. a = 1 + 2"
    properties =  {
        'body': "[AST_Node] an expression node (should not be instanceof AST_Statement)"
    }

    def _walk(self, visitor):
        return visitor._visit(self, lambda: self.body._walk(visitor))

class AST_Assert(AST_Statement):
    "An assert statement, e.g. assert True, 'an error message'"
    properties = {
        'condition': "[AST_Node] the expression that should be tested",
        'message': "[AST_Node*] the expression that is the error message or None",
    }

    def _walk(self, visitor):
        def f_assert():
            self.condition._walk(visitor)
            if self.message:
                self.message._walk(visitor)
        return visitor._visit(self, f_assert)


def walk_body(node, visitor):
    if is_node_type(node.body, AST_Statement):
        node.body._walk(visitor)
    elif node.body:
        for stat in node.body:
            stat._walk(visitor)

class AST_Block(AST_Statement):
    "A body of statements (usually bracketed)"
    properties =  {
        'body': "[AST_Statement*] an array of statements"
    }

    def _walk(self, visitor):
        return visitor._visit(self, lambda : walk_body(self, visitor))

class AST_BlockStatement(AST_Block):
    "A block statement"

class AST_EmptyStatement(AST_Statement):
    "The empty statement (empty block or simply a semicolon)"
    properties = {
        'stype': "[string] the type of empty statement. Is ; for semicolons",
    }

    def _walk(self, visitor):
        return visitor._visit(self)

class AST_StatementWithBody(AST_Statement):
    "Base class for all statements that contain one nested body: `For`, `ForIn`, `Do`, `While`, `With`"
    properties = {
        'body': "[AST_Statement] the body; this should always be present, even if it's an AST_EmptyStatement"
    }

    def _walk(self, visitor):
        return visitor._visit(self, lambda : self.body._walk(visitor))

class AST_DWLoop(AST_StatementWithBody):
    "Base class for do/while statements"
    properties = {
        'condition': "[AST_Node] the loop condition.  Should not be instanceof AST_Statement"
    }

    def _walk(self, visitor):
        return visitor._visit(self, lambda : [self.condition._walk(visitor), self.body._walk(visitor)])

class AST_Do(AST_DWLoop):
    "A `do` statement"

class AST_While(AST_DWLoop):
    "A `while` statement"

class AST_ForIn(AST_StatementWithBody):
    "A `for ... in` statement"
    properties = {
        'init': "[AST_Node] the `for/in` initialization code",
        'name': "[AST_SymbolRef?] the loop variable, only if `init` is AST_Var",
        'object': "[AST_Node] the object that we're looping through"
    }

    def _walk(self, visitor):
        def f_for_in():
            self.init._walk(visitor)
            if self.name: self.name._walk(visitor)
            self.object._walk(visitor)
            if self.body:
                self.body._walk(visitor)
        return visitor._visit(self, f_for_in)

class AST_ForJS(AST_StatementWithBody):
    "A `for ... in` statement"
    properties = {
        'condition': "[AST_Verbatim] raw JavaScript conditional"
    }

class AST_EllipsesRange(AST_Node):
    properties = {
        'first': "[AST_Node] the 'a' in [a..b] expression",
        'last': "[AST_Node] the 'b' in [a..b] expression"
    }


class AST_ListComprehension(AST_ForIn):
    "A list comprehension expression"
    properties = {
        'condition': "[AST_Node] the `if` condition",
        'statement': "[AST_Node] statement to perform on each element before returning it"
    }

    def _walk(self, visitor):
        def f_list_comprehension():
            self.init._walk(visitor)
            self.object._walk(visitor)
            self.statement._walk(visitor)
            if self.condition: self.condition._walk(visitor)
        return visitor._visit(self, f_list_comprehension)

class AST_SetComprehension(AST_ListComprehension):
    'A set comprehension'

class AST_DictComprehension(AST_ListComprehension):
    'A set comprehension'
    properties = {
        'value_statement': "[AST_Node] statement to perform on each value before returning it",
        'is_pydict': "[bool] True if this comprehension is for a python dict",
        'is_jshash': "[bool] True if this comprehension is for a js hash",
    }

    def _walk(self, visitor):
        def f_dict_comprehension():
            self.init._walk(visitor)
            self.object._walk(visitor)
            self.statement._walk(visitor)
            self.value_statement._walk(visitor)
            if self.condition: self.condition._walk(visitor)
        return visitor._visit(self, f_dict_comprehension)

class AST_GeneratorComprehension(AST_ListComprehension):
    'A generator comprehension'

class AST_With(AST_StatementWithBody):
    "A `with` statement"
    properties = {
        'clauses': "[AST_WithClause*] the `with` clauses (comma separated)"
    }

    def _walk(self, visitor):
        def f_with():
            for exp in self.clauses:
                exp._walk(visitor)
            self.body._walk(visitor)
        return visitor._visit(self, f_with)

class AST_WithClause(AST_Node):
    'A clause in a with statement'
    properties = {
        'expression': '[AST_Node] the expression',
        'alias': '[AST_SymbolAlias?] optional alias for this expression',
    }

    def _walk(self, visitor):
        def f_with_clause():
            self.expression._walk(visitor)
            if self.alias:
                self.alias._walk(visitor)
        return visitor._visit(self, f_with_clause)


# Scope and functions:

class AST_Scope(AST_Block):
    "Base class for all statements introducing a lexical scope"
    properties = {
        'localvars': "[SymbolDef*] list of variables local to this scope",
        'docstrings': "[AST_String*] list of docstrings for this scope",
    }


class AST_Toplevel(AST_Scope):
    "The toplevel scope"
    properties = {
        'globals': "[Object/S] a map of name -> SymbolDef for all undeclared names",
        'baselib': "[Object/s] a collection of used parts of baselib",
        'imports': "[Object/S] a map of module_id->AST_Toplevel for all imported modules (this represents all imported modules across all source files)",
        'imported_module_ids': "[string*] a list of module ids that were imported by this module, specifically",
        'nonlocalvars': "[String*] a list of all non-local variable names (names that come from the global scope)",
        'shebang': "[string] If #! line is present, it will be stored here",
        'import_order': "[number] The global order in which this scope was imported",
        'module_id': "[string] The id of this module",
        'exports': "[SymbolDef*] list of names exported from this module",
        'classes': "[Object/S] a map of class names to AST_Class for classes defined in this module",
        'filename': "[string] The absolute path to the file from which this module was read",
        'srchash': "[string] SHA1 hash of source code, used for caching",
        'comments_after': '[array] True iff there were comments before this token',
    }

class AST_Import(AST_Statement):
    "Container for a single import"

    properties = {
        'module': "[AST_SymbolVar] name of the module we're importing",
        'key':  "[string] The key by which this module is stored in the global modules mapping",
        'alias': "[AST_SymbolAlias] The name this module is imported as, can be None. For import x as y statements.",
        'argnames': "[AST_ImportedVar*] names of objects to be imported",
        'body': "[AST_TopLevel] parsed contents of the imported file",
    }

    def _walk(self, visitor):
        def f_import():
            if self.alias:
                self.alias._walk(visitor)
            if self.argnames:
                for arg in self.argnames:
                    arg._walk(visitor)
        return visitor._visit(self, f_import)

class AST_Imports(AST_Statement):
    "Container for any number of imports"
    properties = {
        'imports': "[AST_Import+] array of imports",
    }

    def _walk(self, visitor):
        def f_imports():
            for imp in self.imports:
                imp._walk(visitor)

        return visitor._visit(self, f_imports)

class AST_Decorator(AST_Node):
    "Class for function decorators"
    properties = {
        'expression': "[AST_Node] the decorator expression"
    }

    def _walk(self, visitor):
        def f_decorator():
            if self.expression:
                self.expression.walk(visitor)
        return visitor._visit(self, f_decorator)

class AST_Lambda(AST_Scope):
    "Base class for functions"
    properties = {
        'name': "[AST_SymbolDeclaration?] the name of this function",
        'argnames': "[AST_SymbolFunarg*] array of function arguments",
        'decorators': "[AST_Decorator*] function decorators, if any",
        'annotations': "[bool*] True iff this function should have annotations set",
        'is_generator': "[bool*] True iff this function is a generator",
        'is_lambda': "[bool*] True iff this function is a Python lambda function",
        'is_expression': "[bool*] True iff this function is a function expression",
        'is_anonymous': "[bool*] True iff this function is an anonymous function",
        "return_annotation": "[AST_Node?] The return type annotation provided (if any)",
    }

    def _walk(self, visitor):
        def f_lambda():
            if self.decorators:
                for d in self.decorators:
                    d.walk(visitor)
            if self.name:
                self.name._walk(visitor)

            for arg in self.argnames:
                arg._walk(visitor)
            if self.argnames.starargs:
                self.argnames.starargs._walk(visitor)
            if self.argnames.kwargs:
                self.argnames.kwargs._walk(visitor)
            walk_body(self, visitor)
        return visitor._visit(self, f_lambda)

class AST_Function(AST_Lambda):
    "A function expression"

class AST_Class(AST_Scope):
    "A class declaration"
    properties = {
        'name': "[AST_SymbolDeclaration?] the name of this class",
        'init': "[AST_Function] constructor for the class",
        'parent': "[AST_Symbol?] parent class this class inherits from",
        'bases': "[AST_Symbol*] list of base classes this class inherits from",
        "static": "[dict] A hash whose keys are names of static methods for this class",
        'external': "[boolean] true if class is declared elsewhere, but will be within current scope at runtime",
        'bound': "[string*] list of methods that need to be bound to self",
        'decorators': "[AST_Decorator*] function decorators, if any",
        'module_id': "[string] The id of the module this class is defined in",
        'statements': "[AST_Node*] list of statements in the class scope (excluding method definitions)",
        'dynamic_properties': '[dict] map of dynamic property names to property descriptors of the form {getter:AST_Method, setter:AST_Method',
        'classvars': '[dict] map containing all class variables as keys, to be used to easily test for existence of a class variable',
    }

    def _walk(self, visitor):
        def f_class():
            if self.decorators:
                for d in self.decorators:
                    d.walk(visitor)
            self.name._walk(visitor)
            walk_body(self, visitor)
            if self.parent: self.parent._walk(visitor)
        return visitor._visit(self, f_class)

class AST_Method(AST_Lambda):
    "A class method definition"
    properties = {
        "static": "[boolean] true if method is static",
        "is_getter": "[boolean] true if method is a property getter",
        "is_setter": "[boolean] true if method is a property setter",
    }

# Jumps(break/continue/etc)

class AST_Jump(AST_Statement):
    "Base class for “jumps” (for now that's `return`, `throw`, `break` and `continue`)"

class AST_Exit(AST_Jump):
    "Base class for “exits” (`return` and `throw`)"
    properties = {
        'value': "[AST_Node?] the value returned or thrown by this statement; could be null for AST_Return"
    }

    def _walk(self, visitor):
        def f_exit():
            if self.value:
                self.value._walk(visitor)
        return visitor._visit(self, f_exit)

class AST_Return(AST_Exit):
    "A `return` statement"

class AST_Yield(AST_Return):
    "A `yield` statement"
    properties = {
        'is_yield_from': "[bool] True iff this is a yield from, False otherwise"
    }

class AST_Throw(AST_Exit):
    "A `throw` statement"

class AST_LoopControl(AST_Jump):
    "Base class for loop control statements (`break` and `continue`)"

class AST_Break(AST_LoopControl):
    "A `break` statement"

class AST_Continue(AST_LoopControl):
    "A `continue` statement"

# If
class AST_If(AST_StatementWithBody):
    "A `if` statement"
    properties = {
        'condition': "[AST_Node] the `if` condition",
        'alternative': "[AST_Statement?] the `else` part, or null if not present"
    }

    def _walk(self, visitor):
        def f_if():
            self.condition._walk(visitor)
            self.body._walk(visitor)
            if self.alternative:
                self.alternative._walk(visitor)
        return visitor._visit(self, f_if)


# EXCEPTIONS

class AST_Try(AST_Block):
    "A `try` statement"
    properties = {
        'bcatch': "[AST_Catch?] the catch block, or null if not present",
        'bfinally': "[AST_Finally?] the finally block, or null if not present",
        'belse': '[AST_Else?] the else block for null if not present',
    }

    def _walk(self, visitor):
        def f_try():
            walk_body(self, visitor)
            if self.bcatch:
                self.bcatch._walk(visitor)

            if self.belse:
                self.belse._walk(visitor)

            if self.bfinally:
                self.bfinally._walk(visitor)
        return visitor._visit(self, f_try)

class AST_Catch(AST_Block):
    "A `catch` node; only makes sense as part of a `try` statement"

class AST_Except(AST_Block):
    "An `except` node for JPython, which resides inside the catch block"
    properties = {
        'argname': "[AST_SymbolCatch] symbol for the exception",
        'errors': "[AST_SymbolVar*] error classes to catch in this block"
    }

    def _walk(self, visitor):
        def f_except():
            if self.argname:
                self.argname.walk(visitor)
            if self.errors:
                for e in self.errors: e.walk(visitor)
            walk_body(self, visitor)
        return visitor._visit(this, f_except)

class AST_Finally(AST_Block):
    "A `finally` node; only makes sense as part of a `try` statement"

class AST_Else(AST_Block):
    'An `else` node; only makes sense as part of `try` statement'

# VAR/CONST
class AST_Definitions(AST_Statement):
    "Base class for `var` or `const` nodes (variable declarations/initializations)"
    properties = {
        'definitions': "[AST_VarDef*] array of variable definitions"
    }

    def _walk(self, visitor):
        def f_definitions():
            for def_ in self.definitions:
                def_._walk(visitor)
        return visitor._visit(self, f_definitions)

class AST_Var(AST_Definitions):
    "A `var` statement"

class AST_VarDef(AST_Node):
    "A variable declaration; only appears in a AST_Definitions node"
    properties = {
        'name': "[AST_SymbolVar|AST_SymbolNonlocal] name of the variable",
        'value': "[AST_Node?] initializer, or null if there's no initializer"
    }

    def _walk(self, visitor):
        def f_var_def():
            self.name._walk(visitor)
            if self.value:
                self.value._walk(visitor)
        return visitor._visit(self, f_var_def)

# Miscellaneous

class AST_BaseCall(AST_Node):
    "A base class for function calls"
    properties = {
        'args': "[AST_Node*] array of arguments"
    }

class AST_Call(AST_BaseCall):
    "A function call expression"
    properties = {
        'expression': "[AST_Node] expression to invoke as function"
    }

    def _walk(self, visitor):
        def f_call():
            self.expression._walk(visitor)
            for arg in self.args:
                arg._walk(visitor)
            if self.args.kwargs:
                for arg in self.args.kwargs:
                    arg[0]._walk(visitor)
                    arg[1]._walk(visitor)
            if self.args.kwarg_items:
                for arg in self.args.kwarg_items:
                    arg._walk(visitor)
        return visitor._visit(self, f_call)


class AST_ClassCall(AST_BaseCall):
    "A function call expression"
    properties = {
        "class": "[string] name of the class method belongs to",
        'method': "[string] class method being called",
        "static": "[boolean] defines whether the method is static"
    }

    def _walk(self, visitor):
        def f_class_call():
            if self.expression: self.expression._walk(visitor)
            for arg in self.args:
                arg._walk(visitor)
            for arg in self.args.kwargs:
                arg[0]._walk(visitor)
                arg[1]._walk(visitor)
            for arg in self.args.kwarg_items:
                arg._walk(visitor)
        return visitor._visit(self, f_class_call)

class AST_New(AST_Call):
    "An object instantiation. Derives from a function call since it has exactly the same properties"

class AST_Seq(AST_Node):
    "A sequence expression (two comma-separated expressions)"
    properties = {
        'car': "[AST_Node] first element in sequence",
        'cdr': "[AST_Node] second element in sequence"
    }

    def to_array(self):
        p = self
        a = []
        while p:
            a.push(p.car)
            if p.cdr and not (is_node_type(p.cdr, AST_Seq)):
                a.push(p.cdr)
                break
            p = p.cdr
        return a

    def add(self, node):
        p = self
        while p:
            if not (is_node_type(p.cdr, AST_Seq)):
                cell = AST_Seq.cons(p.cdr, node)
                p.cdr = cell
                return p.cdr
            p = p.cdr

    def _walk(self, visitor):
        def f_seq():
            self.car._walk(visitor)
            if self.cdr:
                self.cdr._walk(visitor)
        return visitor._visit(self, f_seq)

    def cons(self, x, y):
        # Should be called as a classmethod: AST_Seq.cons()
        seq = AST_Seq(x)
        seq.car = x
        seq.cdr = y
        return seq

    def from_array(self, array):
        # Should be called as a classmethod: AST_Seq.from_array()
        if array.length is 0:
            return None

        if array.length is 1:
            return array[0].clone()

        ans = None
        for i in range(array.length-1, -1, -1):
            ans = AST_Seq.cons(array[i], ans)

        p = ans
        while p:
            if p.cdr and not p.cdr.cdr:
                p.cdr = p.cdr.car
                break
            p = p.cdr
        return ans

class AST_PropAccess(AST_Node):
    'Base class for property access expressions, i.e. `a.foo` or `a["foo"]`'
    properties = {
        'expression': "[AST_Node] the “container” expression",
        'property': "[AST_Node|string] the property to access.  For AST_Dot this is always a plain string, while for AST_Sub it's an arbitrary AST_Node",
    }

class AST_Dot(AST_PropAccess):
    "A dotted property access expression"

    def _walk(self, visitor):
        return visitor._visit(self, lambda : self.expression._walk(visitor))

class AST_Sub(AST_PropAccess):
    'Index-style property access, i.e. `a["foo"]`'

    def _walk(self, visitor):
        return visitor._visit(self, lambda: [self.expression._walk(visitor), self.property._walk(visitor)])

class AST_ItemAccess(AST_PropAccess):
    'Python index-style property access, i.e. `a.__getitem__("foo")`'
    properties = {
        'assignment': "[AST_Node or None] Not None if this is an assignment (a[x] = y) rather than a simple access",
    }

    def _walk(self, visitor):
        def f_item_access():
            self.expression._walk(visitor)
            self.property._walk(visitor)
            if self.assignment:
                self.assignment._walk(visitor)
        return visitor._visit(self, f_item_access)

class AST_Splice(AST_PropAccess):
    'Index-style property access, i.e. `a[3:5]`'
    properties = {
        'property2': "[AST_Node] the 2nd property to access - typically ending index for the array.",
        'assignment': "[AST_Node] The data being spliced in."
    }

    def _walk(self, visitor):
        def f_prop_access():
            self.expression._walk(visitor)
            self.property._walk(visitor)
            self.property2._walk(visitor)
        return visitor._visit(self, f_prop_access)

class AST_Unary(AST_Node):
    "Base class for unary expressions"
    properties = {
        'operator': "[string] the operator",
        'expression': "[AST_Node] expression that this unary operator applies to",
        'parenthesized': "[bool] Whether this unary expression was parenthesized",
    }

    def _walk(self, visitor):
        return visitor._visit(self, lambda:self.expression._walk(visitor))

class AST_UnaryPrefix(AST_Unary):
    "Unary prefix expression, i.e. `typeof i` or `del i`"

class AST_Binary(AST_Node):
    "Binary expression, i.e. `a + b`"
    properties = {
        'left': "[AST_Node] left-hand side expression",
        'operator': "[string] the operator",
        'right': "[AST_Node] right-hand side expression"
    }

    def _walk(self, visitor):
        return visitor._visit(self, lambda:[self.left._walk(visitor), self.right._walk(visitor)])

# TODO: eliminate this -- it's useful but not syntactically valid python.
class AST_Existential(AST_Node):
    "Existential operator a?"
    properties = {
        'expression': "[AST_Node] The expression whose existence we need to check",
    'after': "[None|string|AST_Node] is None when there is nothing following this operator, is a string when there is as AST_PropAccess following this operator, is an AST_Node if it is used a a shorthand for the conditional ternary, i.e. a ? b == a if a? else b",
    }

    def _walk(self, visitor):
        def f_existential():
            self.expression._walk(visitor)
            if self.after is not None and jstype(self.after) is 'object':
                self.after._walk(visitor)
        return visitor._visit(self, f_existential)

class AST_Conditional(AST_Node):
    "Conditional expression using the ternary operator, i.e. `a if b else c`"
    properties = {
        'condition': "[AST_Node]",
        'consequent': "[AST_Node]",
        'alternative': "[AST_Node]",
    }

    def _walk(self, visitor):
        def f_conditional():
            self.condition._walk(visitor)
            self.consequent._walk(visitor)
            self.alternative._walk(visitor)
        return visitor._visit(self, f_conditional)


class AST_Assign(AST_Binary):
    "An assignment expression — `a = b + 5`"

    def is_chained(self):
        return is_node_type(self.right, AST_Assign) or (
            is_node_type(self.right, AST_Seq) and (
                is_node_type(self.right.car, AST_Assign) or is_node_type(self.right.cdr, AST_Assign))
        )

    def traverse_chain(self):
        right = self.right
        while True:
            if is_node_type(right, AST_Assign):
                right = right.right
                continue
            if is_node_type(right, AST_Seq):
                if is_node_type(right.car, AST_Assign):
                    right = AST_Seq({'car':right.car.right, 'cdr': right.cdr})
                    continue
                if is_node_type(right.cdr, AST_Assign):
                    right = right.cdr.right
                    continue
            break
        left_hand_sides = r'%js [self.left]'
        next = self.right
        while True:
            if is_node_type(next, AST_Assign):
                left_hand_sides.push(next.left)
                next = next.right
                continue
            if is_node_type(next, AST_Seq):
                if is_node_type(next.cdr, AST_Assign):
                    assign = next.cdr
                    left_hand_sides.push(AST_Seq({'car':next.car, 'cdr':assign.left}))
                    next = assign.right
                    continue
            break
        return left_hand_sides, right


# LITERALS

class AST_Array(AST_Node):
    "An array literal"
    properties = {
        'elements': "[AST_Node*] array of elements"
    }

    def _walk(self, visitor):
        def f_array():
            for el in self.elements:
                el._walk(visitor)
        return visitor._visit(self, f_array)

    def flatten(self):
        def flatten(arr):
            ans = []
            for value in arr:
                if is_node_type(value, AST_Seq):
                    value = value.to_array()
                elif is_node_type(value, AST_Array):
                    value = value.elements
                if Array.isArray(value):
                    ans = ans.concat(flatten(value))
                else:
                    ans.push(value)
            return ans
        return flatten(self.elements)

class AST_Object(AST_Node):
    "An object literal"
    properties = {
        'properties': "[AST_ObjectProperty*] array of properties",
        'is_pydict': "[bool] True if this object is a python dict literal",
        'is_jshash': "[bool] True if this object is a js hash literal",
    }

    def _walk(self, visitor):
        def f_object():
            for prop in self.properties:
                prop._walk(visitor)
        return visitor._visit(self, f_object)

class AST_ExpressiveObject(AST_Object):
    'An object literal with expressions for some keys'

class AST_ObjectProperty(AST_Node):
    "Base class for literal object properties"
    properties = {
        'key': "[AST_Node] the property expression",
        'value': "[AST_Node] property value.  For setters and getters this is an AST_Function.",
        'quoted': '',
    }

    def _walk(self, visitor):
        def f_object_property():
            self.key._walk(visitor)
            self.value._walk(visitor)
        return visitor._visit(self, f_object_property)

class AST_ObjectKeyVal(AST_ObjectProperty):
    "A key: value object property"

class AST_Set(AST_Node):
    "A set literal"
    properties = {
        'items': "[AST_SetItem*] array of items"
    }

    def _walk(self, visitor):
        def f_node():
            for prop in self.items:
                prop._walk(visitor)
        return visitor._visit(self, f_node)

class AST_SetItem(AST_Node):
    "An item in a set literal"
    properties = {
        'value': "[AST_Node] The value of this item",
    }

    def _walk(self, visitor):
        return visitor._visit(self, lambda : self.value._walk(visitor)        )

class AST_Symbol(AST_Node):
    "Base class for all symbols"
    properties = {
        'name': "[string] name of this symbol",
        'scope': "[AST_Scope/S] the current scope (not necessarily the definition scope)",
        'thedef': "[SymbolDef/S] the definition of this symbol"
    }

class AST_SymbolAlias(AST_Symbol):
    "An alias used in an import statement or with statement"

class AST_SymbolDeclaration(AST_Symbol):
    "A declaration symbol (symbol in var/const, function name or argument, symbol in catch)"
    properties = {
        'init': "[AST_Node*/S] array of initializers for this declaration."
    }

class AST_SymbolVar(AST_SymbolDeclaration):
    "Symbol defining a variable"

class AST_ImportedVar(AST_SymbolVar):
    "Symbol defining an imported symbol"
    properties = {
        'alias': "AST_SymbolAlias the alias for this imported symbol"
    }

class AST_SymbolNonlocal(AST_SymbolDeclaration):
    "A nonlocal declaration"

class AST_SymbolFunarg(AST_SymbolVar):
    "Symbol naming a function argument, possibly with an annotation."
    properties = {
        'annotation': "[AST_Node?] The annotation provided for this argument (if any)"
    }

class AST_SymbolDefun(AST_SymbolDeclaration):
    "Symbol defining a function"

class AST_SymbolLambda(AST_SymbolDeclaration):
    "Symbol naming a function expression"

class AST_SymbolCatch(AST_SymbolDeclaration):
    "Symbol naming the exception in catch"

class AST_SymbolRef(AST_Symbol):
    "Reference to some symbol (not definition/declaration)"
    properties = {
        'parens': "[boolean/S] if true, this variable is wrapped in parentheses"
    }

class AST_This(AST_Symbol):
    "The `this` symbol"

class AST_Constant(AST_Node):
    "Base class for all constants"

class AST_String(AST_Constant):
    "A string literal"
    properties = {
        'value': "[string] the contents of this string"
    }

class AST_Verbatim(AST_Constant):
    "Raw JavaScript code"
    properties = {
        'value': "[string] A string of raw JS code"
    }

class AST_Number(AST_Constant):
    "A number literal"
    properties = {
        'value': "[number] the numeric value"
    }

class AST_RegExp(AST_Constant):
    "A regexp literal"
    properties = {
        'value': "[RegExp] the actual regexp"
    }

class AST_Atom(AST_Constant):
    "Base class for atoms"
    def __init__(self, initializer):
        if initializer:
            self.start = initializer.start
            self.end = initializer.end

class AST_Null(AST_Atom):
    "The `null` atom"
    value = None

class AST_NaN(AST_Atom):
    "The impossible value"
    value = r'%js NaN'

class AST_Undefined(AST_Atom):
    "The `undefined` value"
    value = r'%js undefined'

class AST_Hole(AST_Atom):
    "A hole in an array"
    value = r'%js undefined'

class AST_Infinity(AST_Atom):
    "The `Infinity` value"
    value = r'%js Infinity'

class AST_Boolean(AST_Atom):
    "Base class for booleans"

class AST_False(AST_Boolean):
    "The `false` atom"
    value = False

class AST_True(AST_Boolean):
    "The `true` atom"
    value = True

# TreeWalker

class TreeWalker:

    def __init__(self, callback):
        self.visit = callback
        self.stack = []

    def _visit(self, node, descend):
        self.stack.push(node)
        ret = self.visit(node,
                         (lambda: descend.call(node)) if descend else noop)
        if not ret and descend:
            descend.call(node)

        self.stack.pop()
        return ret

    def parent(self, n):
        return self.stack[self.stack.length - 2 - (n or 0)]

    def push(self, node):
        self.stack.push(node)

    def pop(self):
        return self.stack.pop()

    def self(s):
        return s.stack[s.stack.length - 1]

    def find_parent(self, type):
        stack = self.stack
        for i in range(stack.length-1, -1, -1):
            x = stack[i]
            if is_node_type(x, type):
                return x

    def in_boolean_context(self):
        stack = self.stack
        i = stack.length
        i -= 1
        self = stack[i]
        while i > 0:
            i -= 1
            p = stack[i]
            if (is_node_type(p, AST_If) and p.condition is self
            or is_node_type(p, AST_Conditional) and p.condition is self
            or is_node_type(p, AST_DWLoop) and p.condition is self
            or is_node_type(p, AST_UnaryPrefix) and p.operator is "!" and p.expression is self):
                return True
            if not (is_node_type(p, AST_Binary) and (p.operator is "&&" or p.operator is "||")):
                return False
            self = p

class Found(Exception):
    pass

def has_calls(expression):
    # Technically, in JavaScript property access is also dynamic and can
    # involve function calls. However, there is no way to determine which
    # property accesses are dynamic, so we ignore them, as they would lead to
    # too many false positives.
    if not expression:
        return False
    try:
        def is_call(node):
            if is_node_type(node, AST_BaseCall) or is_node_type(node, AST_ItemAccess):
                raise Found()
        expression.walk(TreeWalker(is_call))
    except Found:
        return True
    return False
