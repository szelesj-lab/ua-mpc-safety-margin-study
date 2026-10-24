"""Development-period ablation: every controller with its own tuned (balanced = safest) weights,
on both plants. Resumable: a run whose steps file exists is skipped."""
import json, os, sys, time, warnings
warnings.filterwarnings("ignore")
ROOT = os.environ.get("KAIROS_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uncertainty-aware-mpc")))
PAPER = os.environ.get("STUDY_RESULTS", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results")))
sys.path.insert(0, os.path.join(ROOT, "src"))
from concurrent.futures import ProcessPoolExecutor, as_completed
from replay import build_data, named_periods, simulate, metrics, with_overrides, load_config, TUNING_DIR

OUT = os.path.join(PAPER, "dev_ablation")
# SOC_RECOVERY=0 reproduces the runs made before mpc.soc_recovery existed (see docs/protocol.md)
SCEN = {"SoC": {"E_capacity": 72}, "degradation": {"c_deg": 2e-5},
        "mpc": {"soc_recovery": os.environ.get("SOC_RECOVERY", "1") == "1"}}
best = lambda c: json.loads((TUNING_DIR / f"{c}_best.json").read_text())["overrides"]
VARIANTS = {  # name: (controller, overrides)
    "grid_only": ("grid_only", {}),
    "rule": ("rule", {}),
    "det": ("det", best("det")),
    "det_bo": ("det_bo", best("det_bo")),
    "ua_rho_only": ("ua", with_overrides(best("ua"), {"mpc": {"soc_chance_z": 0.0}})),
    "ua_margin_only": ("ua", with_overrides(best("ua"), {"weights": {"lambda": 0.0}})),
    "ua": ("ua", best("ua")),
    "oracle": ("oracle", best("det")),
}

def job(a):
    name, plant, ctrl, data, cfg, t0, t1 = a
    t = time.perf_counter()
    df, st = simulate(data, cfg, ctrl, t0, t1)
    df.to_csv(f"{OUT}/steps/{plant}_{name}.csv")
    m = metrics(df, st, cfg)
    json.dump(m, open(f"{OUT}/steps/{plant}_{name}.json", "w"), default=float)
    return name, plant, m, time.perf_counter() - t

if __name__ == "__main__":
    os.makedirs(f"{OUT}/steps", exist_ok=True)
    base = with_overrides(load_config(), SCEN)
    data = build_data(base)
    t0, t1 = named_periods(data, base)["development"]
    json.dump({"period": [t0.isoformat(), t1.isoformat()], "scenario": SCEN,
               "variants": {k: {"controller": c, "overrides": o} for k, (c, o) in VARIANTS.items()},
               "replan_steps": base["replay"]["replan_steps"], "mpc": base["mpc"]},
              open(f"{OUT}/setup.json", "w"), indent=2, default=float)
    jobs = []
    for plant in ("physical", "bms"):
        for name, (ctrl, over) in VARIANTS.items():
            if os.path.exists(f"{OUT}/steps/{plant}_{name}.json"):
                continue
            cfg = with_overrides(with_overrides(base, over), {"replay": {"plant": plant}})
            jobs.append((name, plant, ctrl, data, cfg, t0, t1))
    print(f"period {t0} – {t1}: {len(jobs)} runs to do", flush=True)
    with ProcessPoolExecutor(int(sys.argv[1]) if len(sys.argv) > 1 else 2) as ex:
        for f in as_completed([ex.submit(job, j) for j in jobs]):
            n, p, m, s = f.result()
            print(f"done {p:<8} {n:<15} net {m['net_cost_eur']:.4f} viol {m['violation_pp_h']:.4f} "
                  f"prot {m.get('protection_steps', 0)} solver {m.get('solver_success_pct', 100):.1f}% {s:.0f}s", flush=True)
    print("ALL RUNS DONE", flush=True)
