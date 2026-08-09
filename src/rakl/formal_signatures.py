from __future__ import annotations

from typing import Tuple

from .formalism import ExprOp, FormalExpression


def _simple_symbol(expression: FormalExpression) -> str | None:
    if expression.op is ExprOp.SYMBOL and expression.symbol:
        return expression.symbol
    return None


def scientific_motif_signature(expression: FormalExpression) -> Tuple[str, ...]:
    """Extract evaluator-side structural motifs from a mathematical expression.

    The signature is deliberately compact and semantic enough for hidden-world
    invention benchmarks. It is not a full symbolic-equivalence proof.
    """

    motifs: set[str] = set()

    def visit(node: FormalExpression) -> None:
        if node.op is ExprOp.POW and len(node.args) == 2:
            base, exponent = node.args
            symbol = _simple_symbol(base)
            if symbol and exponent.op is ExprOp.CONSTANT and exponent.value is not None:
                motifs.add(f"POWER:{symbol}:{exponent.value:g}")
        elif node.op is ExprOp.MUL:
            symbols = sorted(
                {
                    symbol
                    for arg in node.args
                    for symbol in arg.referenced_symbols()
                }
            )
            if len(symbols) >= 2:
                motifs.add(f"INTERACTION:{'*'.join(symbols)}")
        elif node.op is ExprOp.DIV and len(node.args) == 2:
            numerator = sorted(node.args[0].referenced_symbols())
            denominator = sorted(node.args[1].referenced_symbols())
            if numerator and denominator:
                motifs.add(
                    f"RATIO:{'*'.join(numerator)}/{'*'.join(denominator)}"
                )
        elif node.op is ExprOp.FUNCTION and node.function_name:
            symbols = sorted(node.referenced_symbols())
            motifs.add(
                f"FUNCTION:{node.function_name}:{'*'.join(symbols) if symbols else 'CONST'}"
            )
        elif node.op is ExprOp.DERIVATIVE and node.args:
            symbols = sorted(node.args[0].referenced_symbols())
            motifs.add(
                f"DERIVATIVE:{'*'.join(symbols)}:{node.variable}:order{node.order}"
            )
        elif node.op is ExprOp.PIECEWISE:
            motifs.add("PIECEWISE")

        for arg in node.args:
            visit(arg)

    visit(expression)
    return tuple(sorted(motifs))
