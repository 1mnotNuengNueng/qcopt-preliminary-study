"""วงจรทดสอบ + นิยาม 'ผลลัพธ์ที่ถือว่าสำเร็จ' ของแต่ละวงจร"""
import math
from dataclasses import dataclass
from typing import Callable, Set

import networkx as nx
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFTGate


@dataclass
class CircuitSpec:
    name: str
    circuit: QuantumCircuit          # logical circuit, ยังไม่ measure
    success_states: Set[str]         # bitstring ที่นับว่าถูก (little-endian ตาม Qiskit)


def ghz(n: int) -> CircuitSpec:
    qc = QuantumCircuit(n)
    qc.h(0)
    for i in range(1, n):
        qc.cx(i - 1, i)
    return CircuitSpec("ghz", qc, {"0" * n, "1" * n})


def qft(n: int) -> CircuitSpec:
    """QFT บน uniform superposition -> ควรได้ |0...0> กลับมา"""
    qc = QuantumCircuit(n)
    qc.h(range(n))
    qc.append(QFTGate(n), range(n))
    return CircuitSpec("qft", qc, {"0" * n})


def qaoa_maxcut(n: int, gamma: float = 0.8, beta: float = 0.4) -> CircuitSpec:
    """QAOA p=1 บน ring graph, ใช้มุมคงที่ (ไม่ต้อง optimize)"""
    g = nx.cycle_graph(n)
    qc = QuantumCircuit(n)
    qc.h(range(n))
    for u, v in g.edges():
        qc.rzz(2 * gamma, u, v)
    qc.rx(2 * beta, range(n))

    # max cut ของ ring: n ถ้า n คู่, n-1 ถ้า n คี่
    best = _optimal_cuts(g, n)
    return CircuitSpec("qaoa", qc, best)


def _optimal_cuts(g: nx.Graph, n: int) -> Set[str]:
    best_val, best = -1, set()
    for x in range(2 ** n):
        bits = [(x >> i) & 1 for i in range(n)]
        val = sum(1 for u, v in g.edges() if bits[u] != bits[v])
        key = "".join(str(b) for b in reversed(bits))   # Qiskit little-endian
        if val > best_val:
            best_val, best = val, {key}
        elif val == best_val:
            best.add(key)
    return best


BUILDERS: dict[str, Callable[[int], CircuitSpec]] = {
    "ghz": ghz, "qft": qft, "qaoa": qaoa_maxcut,
}