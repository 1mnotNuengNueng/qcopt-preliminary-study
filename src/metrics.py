from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, hellinger_fidelity

SKIP = {"barrier", "measure", "delay"}


def gate_profile(qc: QuantumCircuit) -> dict:
    one_q = two_q = total = 0
    for inst in qc.data:
        op = inst.operation
        if op.name in SKIP:
            continue
        total += 1
        if op.num_qubits == 1:
            one_q += 1
        elif op.num_qubits == 2:
            two_q += 1
    return {"total_gates": total, "one_qubit_gates": one_q, "two_qubit_gates": two_q}


def reference_distribution(logical: QuantumCircuit) -> dict:
    """distribution อ้างอิงจาก statevector: ไม่ transpile ไม่มี noise"""
    return Statevector.from_instruction(logical).probabilities_dict()


def fidelity(ref_probs: dict, counts: dict, shots: int) -> float:
    return hellinger_fidelity(
        {k: v * shots for k, v in ref_probs.items()}, counts
    )


def success_probability(counts: dict, success_states: set, shots: int) -> float:
    return sum(counts.get(s, 0) for s in success_states) / shots