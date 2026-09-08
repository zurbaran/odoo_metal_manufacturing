import ast
import math
import operator

_MAX_EXPRESSION_LENGTH = 1000
_MAX_AST_NODES = 100
_MAX_POWER = 100
_MAX_INT_BITS = 4096

_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}
_COMPARE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}
_SAFE_FUNCTIONS = {
    name: value
    for name, value in math.__dict__.items()
    if not name.startswith("_") and callable(value)
}
_SAFE_FUNCTIONS.update({"abs": abs, "min": min, "max": max, "round": round})
_SAFE_CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}


def _validate_numeric(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value.bit_length() > _MAX_INT_BITS:
            raise ValueError("El resultado entero es demasiado grande")
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("El resultado debe ser un número finito")
        return value
    raise ValueError("Las fórmulas solo pueden trabajar con valores numéricos")


class _MathExpressionEvaluator:
    def __init__(self, variables):
        self.variables = dict(variables)

    def evaluate(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, bool)):
                return _validate_numeric(node.value)
            raise ValueError("Constante no permitida")

        if isinstance(node, ast.Name):
            if node.id in self.variables:
                return _validate_numeric(self.variables[node.id])
            if node.id in _SAFE_CONSTANTS:
                return _SAFE_CONSTANTS[node.id]
            raise ValueError(f"Nombre no permitido: {node.id}")

        if isinstance(node, ast.Attribute):
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == "math"
                and node.attr in _SAFE_CONSTANTS
            ):
                return _SAFE_CONSTANTS[node.attr]
            raise ValueError("Acceso a atributos no permitido")

        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > _MAX_POWER:
                raise ValueError("Exponente demasiado grande")
            return _validate_numeric(_BINARY_OPERATORS[type(node.op)](left, right))

        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
            return _validate_numeric(
                _UNARY_OPERATORS[type(node.op)](self.evaluate(node.operand))
            )

        if isinstance(node, ast.Compare):
            left = self.evaluate(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                if type(op) not in _COMPARE_OPERATORS:
                    raise ValueError("Comparador no permitido")
                right = self.evaluate(comparator)
                if not _COMPARE_OPERATORS[type(op)](left, right):
                    return False
                left = right
            return True

        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            for value in node.values:
                if not self.evaluate(value):
                    return False
            return True

        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            for value in node.values:
                if self.evaluate(value):
                    return True
            return False

        if isinstance(node, ast.IfExp):
            branch = node.body if self.evaluate(node.test) else node.orelse
            return self.evaluate(branch)

        if isinstance(node, ast.Call):
            if node.keywords:
                raise ValueError("Los argumentos con nombre no están permitidos")
            function_name = None
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
            elif (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "math"
            ):
                function_name = node.func.attr
            if function_name not in _SAFE_FUNCTIONS:
                raise ValueError("Función no permitida")
            args = [self.evaluate(arg) for arg in node.args]
            return _validate_numeric(_SAFE_FUNCTIONS[function_name](*args))

        raise ValueError(f"Expresión no permitida: {type(node).__name__}")


def evaluate_math_expression(expression, variables):
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("La fórmula está vacía")
    if len(expression) > _MAX_EXPRESSION_LENGTH:
        raise ValueError("La fórmula es demasiado larga")

    tree = ast.parse(expression, mode="eval")
    if sum(1 for _ in ast.walk(tree)) > _MAX_AST_NODES:
        raise ValueError("La fórmula es demasiado compleja")

    return _MathExpressionEvaluator(variables).evaluate(tree.body)
