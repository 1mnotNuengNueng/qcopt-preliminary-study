from qiskit.transpiler import CouplingMap


def get_coupling_map(name: str, n: int) -> CouplingMap:
    """coupling map ใหญ่กว่า n ได้ — transpiler จะเลือก layout ให้เอง"""
    if name == "linear":
        return CouplingMap.from_line(n)
    if name == "grid":
        rows = 2
        cols = -(-n // rows)                      # ceil
        return CouplingMap.from_grid(rows, cols)
    if name == "heavy_hex":
        return CouplingMap.from_heavy_hex(3)      # 19 qubits
    raise ValueError(f"unknown topology: {name}")


TOPOLOGIES = ["linear", "grid", "heavy_hex"]