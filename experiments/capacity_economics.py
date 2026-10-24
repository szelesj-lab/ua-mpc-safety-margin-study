"""Capacity economics on the development period (BMS plant, replanning every hour).

Saving = grid-only cost - controller net cost (dev_ablation/summary.csv, decision_map_recovery/map.csv).
Output: capacity_economics/capacity_economics.csv
"""
import os
import pandas as pd

P = os.environ.get("STUDY_RESULTS", os.path.join(os.path.dirname(__file__), "..", "results"))
abl = pd.read_csv(os.path.join(P, "dev_ablation", "summary.csv"))
grid = float(abl[(abl.plant == "bms") & (abl.variant == "grid_only")].total_eur.iloc[0])
m = pd.read_csv(os.path.join(P, "decision_map_recovery", "map.csv"))
m = m[m.replan_steps == 4].sort_values(["error_scale", "cap_wh"])
rows = []
for es, g in m.groupby("error_scale"):
    big = g[g.cap_wh == g.cap_wh.max()].iloc[0]
    prev = None
    for _, r in g.iterrows():
        row = dict(error_scale=es, cap_wh=int(r.cap_wh), r_E=r.r_E, grid_only_eur=grid)
        for c in ("ua", "bo"):
            s = grid - r[f"{c}_cost"]
            row[f"{c}_cost_eur"] = r[f"{c}_cost"]
            row[f"{c}_saving_eur"] = s
            row[f"{c}_saving_per_wh_meur"] = 1e3 * s / r.cap_wh
            row[f"{c}_share_of_largest_saving"] = s / (grid - big[f"{c}_cost"])
            row[f"{c}_marginal_meur_per_wh"] = (None if prev is None else
                                                1e3 * (prev[f"{c}_cost"] - r[f"{c}_cost"]) / (r.cap_wh - prev.cap_wh))
            row[f"{c}_viol_pp_h"] = r[f"{c}_viol"]
        rows.append(row)
        prev = r
out = pd.DataFrame(rows)
out.to_csv(os.path.join(P, "capacity_economics", "capacity_economics.csv"), index=False)
print(out[["error_scale", "cap_wh", "r_E", "ua_saving_eur", "ua_saving_per_wh_meur", "ua_share_of_largest_saving",
           "ua_marginal_meur_per_wh", "ua_viol_pp_h", "bo_viol_pp_h"]].round(4).to_string(index=False))
