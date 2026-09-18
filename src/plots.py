from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

FIG = Path("results/figures")
FIG.mkdir(parents=True, exist_ok=True)
df = pd.read_csv("results/raw_results.csv")


def errline(data, metric, ylabel, fname, hue="circuit", title=None):
    fig, ax = plt.subplots(figsize=(6, 4))
    for key, g in data.groupby(hue):
        s = g.groupby("optimization_level")[metric].agg(["mean", "std"])
        ax.errorbar(s.index, s["mean"], yerr=s["std"], marker="o",
                    capsize=3, label=str(key))
    ax.set_xlabel("Optimization level"); ax.set_ylabel(ylabel)
    ax.set_xticks([0, 1, 2, 3]); ax.legend(title=hue); ax.grid(alpha=.3)
    if title: ax.set_title(title)
    fig.tight_layout(); fig.savefig(FIG / f"{fname}.png", dpi=150); plt.close(fig)


noisy = df[df["mode"] == "noisy"]

errline(df, "total_gates", "Total gates", "01_gates")
errline(df, "depth", "Circuit depth", "02_depth")
errline(df, "two_qubit_gates", "Two-qubit gates", "03_2q_by_circuit")
errline(df, "two_qubit_gates", "Two-qubit gates", "04_2q_by_topology", hue="topology")
errline(noisy, "fidelity", "Hellinger fidelity", "05_fidelity", hue="topology",
        title="Noisy simulation")
errline(df, "transpile_time", "Transpile time (s)", "06_time", hue="num_qubits")

# routing overhead แยกตาม topology
fig, ax = plt.subplots(figsize=(6, 4))
p = df.groupby(["topology", "optimization_level"])["routing_overhead_2q"].mean().unstack()
p.plot(kind="bar", ax=ax)
ax.set_ylabel("Extra 2Q gates from routing"); ax.set_xlabel("Topology")
ax.legend(title="Opt level"); ax.grid(alpha=.3, axis="y")
fig.tight_layout(); fig.savefig(FIG / "07_routing_overhead.png", dpi=150); plt.close(fig)

# 2Q gates vs fidelity
fig, ax = plt.subplots(figsize=(6, 4))
for key, g in noisy.groupby("circuit"):
    ax.scatter(g["two_qubit_gates"], g["fidelity"], label=key, alpha=.6)
ax.set_xlabel("Two-qubit gate count"); ax.set_ylabel("Fidelity (noisy)")
ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(FIG / "08_2q_vs_fidelity.png", dpi=150); plt.close(fig)

# routing side-study
r = pd.read_csv("results/routing_study.csv")
fig, ax = plt.subplots(figsize=(6, 4))
r.groupby(["circuit", "routing"])["two_qubit_gates"].mean().unstack().plot(kind="bar", ax=ax)
ax.set_ylabel("Two-qubit gates"); ax.set_title("Routing methods @ opt level 1, linear")
ax.grid(alpha=.3, axis="y"); fig.tight_layout()
fig.savefig(FIG / "09_routing_methods.png", dpi=150); plt.close(fig)
print("figures ->", FIG)