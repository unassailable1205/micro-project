"""
FLAT Module: Abstract Syntax Tree (AST) Node Definitions
Represents syntactic structures parsed from source code.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


@dataclass
class ASTNode:
    def to_dict(self) -> Dict[str, Any]:
        result = {"node_type": self.__class__.__name__}
        for k, v in self.__dict__.items():
            if isinstance(v, ASTNode):
                result[k] = v.to_dict()
            elif isinstance(v, list):
                result[k] = [item.to_dict() if isinstance(item, ASTNode) else item for item in v]
            else:
                result[k] = v
        return result


@dataclass
class Program(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class VarDecl(ASTNode):
    name: str = ""
    expr: Optional[ASTNode] = None
    line: int = 0


@dataclass
class Assignment(ASTNode):
    name: str = ""
    expr: Optional[ASTNode] = None
    line: int = 0


@dataclass
class BinaryOp(ASTNode):
    left: Optional[ASTNode] = None
    op: str = ""
    right: Optional[ASTNode] = None
    line: int = 0


@dataclass
class UnaryOp(ASTNode):
    op: str = ""
    expr: Optional[ASTNode] = None
    line: int = 0


@dataclass
class Literal(ASTNode):
    value: Any = None
    val_type: str = "INTEGER"
    line: int = 0


@dataclass
class Identifier(ASTNode):
    name: str = ""
    line: int = 0


@dataclass
class IfStatement(ASTNode):
    condition: Optional[ASTNode] = None
    then_branch: List[ASTNode] = field(default_factory=list)
    else_branch: List[ASTNode] = field(default_factory=list)
    line: int = 0


@dataclass
class WhileStatement(ASTNode):
    condition: Optional[ASTNode] = None
    body: List[ASTNode] = field(default_factory=list)
    line: int = 0


@dataclass
class PrintStatement(ASTNode):
    expr: Optional[ASTNode] = None
    line: int = 0


@dataclass
class DncStatement(ASTNode):
    target: str = ""
    algorithm: str = ""  # karatsuba, fastpow, binsearch, minmax
    args: List[ASTNode] = field(default_factory=list)
    line: int = 0
