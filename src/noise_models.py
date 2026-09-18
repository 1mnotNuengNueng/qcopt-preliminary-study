from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

BASIS_GATES = ["rz", "sx", "x", "cx"]


def depolarizing_readout(p1: float = 1e-3, p2: float = 1e-2,
                         p_ro: float = 0.02) -> NoiseModel:
    nm = NoiseModel(basis_gates=BASIS_GATES)
    # ไม่ใส่ error ให้ rz เพราะเป็น virtual gate บน hardware จริง
    nm.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["sx", "x"])
    nm.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cx"])
    nm.add_all_qubit_readout_error(
        ReadoutError([[1 - p_ro, p_ro], [p_ro, 1 - p_ro]])
    )
    return nm