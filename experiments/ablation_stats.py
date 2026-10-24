"""Summary table + paired circular block bootstrap (5-day blocks, 10 000 draws) of the daily
differences ua − other, on the development period, for both plants."""
import glob, json, os
import numpy as np, pandas as pd
OUT = os.path.join(os.environ.get("STUDY_RESULTS", os.path.join(os.path.dirname(__file__), "..", "results")), "dev_ablation")
TZ, DT, B, BL = "Europe/Budapest", 0.25, 10000, 5
SOC_MIN, SOC_MAX = 0.10, 0.90
ORDER = ["grid_only", "rule", "det", "det_bo", "ua_rho_only", "ua_margin_only", "ua", "oracle"]

rows = []
for f in sorted(glob.glob(f"{OUT}/steps/*.json")):
    plant, name = os.path.basename(f)[:-5].split("_", 1)
    rows.append({"plant": plant, "variant": name, **json.load(open(f))})
summ = pd.DataFrame(rows)
summ["order"] = summ.variant.map({k: i for i, k in enumerate(ORDER)})
summ = summ.sort_values(["plant", "order"]).drop(columns="order")
summ.to_csv(f"{OUT}/summary.csv", index=False)

def daily(plant, name):
    s = pd.read_csv(f"{OUT}/steps/{plant}_{name}.csv"); s.index = pd.to_datetime(s.t, utc=True)
    s["viol"] = 100 * ((SOC_MIN - s.soc).clip(lower=0) + (s.soc - SOC_MAX).clip(lower=0)) * DT
    s["cost"] = s.grid_eur + s.wear_eur
    s["prot"] = ((s.cut_discharge_w > 1e-3) | (s.cut_charge_w > 1e-3)).astype(float)
    s["extra"] = s.cut_discharge_w.clip(lower=0) * s.price_eur_wh * DT
    return s.groupby(s.index.tz_convert(TZ).date).agg(cost=("cost", "sum"), viol=("viol", "sum"),
                                                       prot=("prot", "sum"), extra=("extra", "sum"), n=("soc", "size"))
rng = np.random.default_rng(42)
out = []
for plant in ("physical", "bms"):
    have = set(summ[summ.plant == plant].variant)
    if "ua" not in have:
        continue
    D = {v: daily(plant, v) for v in have}
    full = D["ua"].n.values >= 92; n = int(full.sum())
    k = int(np.ceil(n / BL)); idx = ((rng.integers(0, n, (B, k))[:, :, None] + np.arange(BL)) % n).reshape(B, -1)[:, :n]
    kpis = ("cost", "viol") if plant == "physical" else ("cost", "viol", "prot", "extra")
    for b in [v for v in ORDER if v in have and v != "ua"]:
        for col in kpis:
            x = D["ua"][col].values[full] - D[b][col].values[full]; m = x[idx].mean(1)
            base = D[b][col].values[full].mean()
            out.append(dict(plant=plant, a="ua", b=b, kpi=col, b_per_day=base, diff_per_day=x.mean(),
                            diff_pct=100 * x.mean() / base if base else np.nan,
                            lo=np.percentile(m, 2.5), hi=np.percentile(m, 97.5), p_ua_better=(m < 0).mean(), days=n))
pr = pd.DataFrame(out); pr.to_csv(f"{OUT}/paired_bootstrap.csv", index=False)
pd.set_option("display.width", 220)
cols = ["plant", "variant", "net_cost_eur", "objective", "violation_pp_h", "max_violation_pp", "steps_below_soc_min_pct",
        "chance_target_below_pct", "protection_steps", "undelivered_discharge_kwh", "extra_grid_eur", "curtailed_pct",
        "cycles_per_day", "solver_success_pct"]
print(summ[[c for c in cols if c in summ]].round(4).to_string(index=False))
print(pr.round(5).to_string(index=False))
