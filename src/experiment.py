import itertools
import time
from pathlib import Path

import pandas as pd
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator

from circuits import BUILDERS
from metrics import (fidelity, gate_profile, reference_distribution,
                     success_probability)
from noise_models import BASIS_GATES, depolarizing_readout
from topologies import TOPOLOGIES, get_coupling_map

SIZES = [5, 8, 10]
LEVELS = [0, 1, 2, 3]
SEEDS = [11, 22, 33]
SHOTS = 4096
OUT = Path("results")


def _build_pm(level, cmap, seed, routing=None):
    kwargs = dict(optimization_level=level, basis_gates=BASIS_GATES,
                  coupling_map=cmap, seed_transpiler=seed)
    if routing:
        kwargs["routing_method"] = routing
    return generate_preset_pass_manager(**kwargs)


def main_sweep(ideal, noisy) -> pd.DataFrame:
    rows = []
    for cname, n, level, topo, seed in itertools.product(
            BUILDERS, SIZES, LEVELS, TOPOLOGIES, SEEDS):

        spec = BUILDERS[cname](n)
        ref = reference_distribution(spec.circuit)
        logical_2q = gate_profile(spec.circuit.decompose(reps=3))["two_qubit_gates"]

        meas = spec.circuit.copy()
        meas.measure_all()

        pm = _build_pm(level, get_coupling_map(topo, n), seed)
        t0 = time.perf_counter()
        isa = pm.run(meas)
        transpile_time = time.perf_counter() - t0

        prof = gate_profile(isa)
        base = dict(
            circuit=cname, num_qubits=n, optimization_level=level,
            topology=topo, seed=seed, routing="preset_default",
            depth=isa.depth(), transpile_time=transpile_time,
            routing_overhead_2q=prof["two_qubit_gates"] - logical_2q,
            **prof,
        )

        for mode, backend in (("ideal", ideal), ("noisy", noisy)):
            t0 = time.perf_counter()
            counts = backend.run(isa, shots=SHOTS,
                                 seed_simulator=seed).result().get_counts()
            counts = {k.replace(" ", ""): v for k, v in counts.items()}
            rows.append({
                **base, "mode": mode,
                "exec_time": time.perf_counter() - t0,
                "fidelity": fidelity(ref, counts, SHOTS),
                "success_prob": success_probability(counts, spec.success_states, SHOTS),
            })
        print(f"[main] {cname}-{n}q L{level} {topo} s{seed}")
    return pd.DataFrame(rows)


def routing_study(noisy) -> pd.DataFrame:
    """side-study: แยกผลของ routing method ที่ optimization level คงที่ = 1"""
    rows = []
    for cname, n, routing, seed in itertools.product(
            BUILDERS, SIZES, ["sabre", "basic", "lookahead"], SEEDS):

        spec = BUILDERS[cname](n)
        ref = reference_distribution(spec.circuit)
        meas = spec.circuit.copy()
        meas.measure_all()

        pm = _build_pm(1, get_coupling_map("linear", n), seed, routing=routing)
        t0 = time.perf_counter()
        isa = pm.run(meas)
        elapsed = time.perf_counter() - t0

        counts = noisy.run(isa, shots=SHOTS, seed_simulator=seed).result().get_counts()
        counts = {k.replace(" ", ""): v for k, v in counts.items()}
        rows.append({
            "circuit": cname, "num_qubits": n, "routing": routing, "seed": seed,
            "optimization_level": 1, "topology": "linear", "mode": "noisy",
            "depth": isa.depth(), "transpile_time": elapsed,
            **gate_profile(isa),
            "fidelity": fidelity(ref, counts, SHOTS),
            "success_prob": success_probability(counts, spec.success_states, SHOTS),
        })
        print(f"[routing] {cname}-{n}q {routing} s{seed}")
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    nm = depolarizing_readout()
    ideal = AerSimulator(basis_gates=BASIS_GATES)
    noisy = AerSimulator(basis_gates=BASIS_GATES, noise_model=nm)

    main_sweep(ideal, noisy).to_csv(OUT / "raw_results.csv", index=False)
    routing_study(noisy).to_csv(OUT / "routing_study.csv", index=False)
    print("saved -> results/")