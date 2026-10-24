"""Paper figures from results/paper (static, light, print). Colour = controller identity,
marker shape = secondary encoding; direct labels where the aqua slot is under 3:1."""
import json, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

P = os.environ.get("STUDY_RESULTS", os.path.join(os.path.dirname(__file__), "..", "results"))
OUT = f"{P}/figures"
SURF, INK, INK2, GRID, REF = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#8a8984"
C = {"det": "#2a78d6", "det_bo": "#eb6834", "ua": "#1baf7a"}
M = {"det": "s", "det_bo": "^", "ua": "o"}
NAME = {"det": "Deterministic MPC", "det_bo": "Constant back-off", "ua": "Uncertainty-aware MPC"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False})

def save(fig, name):
    fig.tight_layout(); fig.savefig(f"{OUT}/{name}.png", dpi=300); fig.savefig(f"{OUT}/{name}.pdf"); plt.close(fig)

# 1. development-period fronts
f = pd.read_csv(f"{P}/dev_fronts/fronts_dev.csv")
reg = json.load(open(f"{P}/final_test/preregistration.json"))["selected"]["primary_threshold_pp_h"]
fig, ax = plt.subplots(figsize=(6.2, 3.8))
for c in ("det", "det_bo", "ua"):
    g = f[f.ctrl == c]
    ax.scatter(g.dev_cost, g.dev_viol, s=46, marker=M[c], color=C[c], edgecolor=SURF, linewidth=1.5,
               label=NAME[c], zorder=3)
    s = g[g.trial == reg[c]["trial"]].iloc[0]
    ax.scatter(s.dev_cost, s.dev_viol, s=150, marker=M[c], facecolor="none", edgecolor=INK, linewidth=1.1, zorder=4)
    ax.annotate(f"{c} t{int(s.trial):02d}", (s.dev_cost, s.dev_viol), xytext=(7, 4), textcoords="offset points",
                color=INK, fontsize=8)
jf = f[f.joint_front].sort_values("dev_cost")
ax.step(jf.dev_cost, jf.dev_viol, where="post", color=INK2, linewidth=1, linestyle="--", label="Joint front", zorder=2)
ax.axhline(0.5, color=REF, linewidth=1, linestyle=":")
ax.annotate("selection threshold 0.5 pp·h", (0.535, 0.5), xytext=(0, 3), textcoords="offset points",
            color=INK2, fontsize=7.5)
ax.set_yscale("log"); ax.set_ylim(0.02, 60); ax.set_xlabel("Net cost on the development period (EUR)")
ax.set_ylabel("SoC band violation (pp·h)"); ax.legend(loc="upper right", fontsize=8)
ax.set_title("Tuning-period Pareto points replayed on the development period", fontsize=9.5, loc="left", color=INK)
save(fig, "fig1_dev_fronts")

# 2. final test: two panels, one measure each (no dual axis)
s = pd.read_csv(f"{P}/final_test/summary.csv")
order = ["det", "ua_rho_only", "ua_margin_only", "det_bo", "ua", "oracle"]
label = {"det": "Deterministic", "ua_rho_only": "UA: ρ-weighting only", "ua_margin_only": "UA: margin only",
         "det_bo": "Constant back-off", "ua": "UA (full)", "oracle": "Oracle forecast"}
col = {"det": C["det"], "det_bo": C["det_bo"], "ua": C["ua"], "ua_rho_only": REF, "ua_margin_only": REF, "oracle": REF}
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
for ax, plant, key, xl in ((axs[0], "physical", "violation_pp_h", "SoC band violation (pp·h), physical plant"),
                           (axs[1], "bms", "protection_steps", "BMS protection steps, BMS plant")):
    g = s[s.plant == plant].set_index("variant").loc[order]
    y = np.arange(len(order))
    ax.barh(y, g[key], height=0.55, color=[col[o] for o in order], edgecolor=SURF, linewidth=2)
    for yi, v in zip(y, g[key]):
        ax.annotate(f"{v:.2f}" if key == "violation_pp_h" else f"{int(v)}", (v, yi), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=8, color=INK)
    ax.set_xlabel(xl, fontsize=8.5); ax.grid(axis="y", visible=False)
    ax.set_xlim(0, g[key].max() * 1.22)
axs[0].set_yticks(np.arange(len(order)), [label[o] for o in order]); axs[0].invert_yaxis()
fig.suptitle("Final test (44 days, pre-registered selection, run once)", fontsize=9.5, x=0.01, ha="left", color=INK)
save(fig, "fig2_final_test")

# 3. decision map (with SoC recovery): violation vs r_E
m = pd.read_csv(f"{P}/decision_map_recovery/map.csv")
bo_backoff = json.load(open(f"{P}/tuning/det_bo_pareto.json"))
bo = next(p for p in bo_backoff["points"] if p["trial"] == reg["det_bo"]["trial"])["overrides"]["mpc"]["soc_backoff"]
fig, ax = plt.subplots(figsize=(6.2, 3.8))
for _, r in m.iterrows():
    ax.plot([r.r_E, r.r_E], [max(r.ua_viol, 1e-3), max(r.bo_viol, 1e-3)], color=GRID, linewidth=1.5, zorder=1)
ax.scatter(m.r_E, m.bo_viol.clip(lower=1e-3), marker=M["det_bo"], s=46, color=C["det_bo"], edgecolor=SURF,
           linewidth=1.5, label=NAME["det_bo"], zorder=3)
ax.scatter(m.r_E, m.ua_viol.clip(lower=1e-3), marker=M["ua"], s=46, color=C["ua"], edgecolor=SURF,
           linewidth=1.5, label=NAME["ua"], zorder=3)
for k, (_, r) in enumerate(m[m.r_E >= 0.04].sort_values(["r_E", "bo_viol"]).iterrows()):
    tag = f"{int(r.cap_wh)} Wh, {r.error_scale:g}×" + (", 4 h" if r.replan_steps == 16 else "")
    dy = -6 if (k == 0 and abs(r.r_E - 0.0468) < 1e-3) else 4
    ax.annotate(tag, (r.r_E, max(r.bo_viol, 1e-3)), xytext=(5, dy), textcoords="offset points", fontsize=7, color=INK2,
                va="center")
ax.axvline(bo, color=INK2, linestyle="--", linewidth=1)
ax.annotate(f"tuned constant back-off = {bo:.3f}", (bo, 0.006), xytext=(4, 0), textcoords="offset points",
            fontsize=7.5, color=INK2)
ax.set_yscale("log"); ax.set_ylim(5e-3, 60)
ax.set_xlabel("r_E = 95 % energy deficit until the next re-plan / usable capacity")
ax.set_ylabel("SoC band violation (pp·h)"); ax.legend(loc="upper left", fontsize=8, bbox_to_anchor=(0.2, 1.0))
ax.set_title("Decision map: same weights, other capacity / error level / re-planning interval", fontsize=9.5,
             loc="left", color=INK)
save(fig, "fig3_decision_map")

# 4. nominal vs empirical chance level
z = pd.read_csv(f"{P}/decision_map_recovery/chance_calibration.csv")
fig, ax = plt.subplots(figsize=(4.2, 3.6))
e = z.empirical_below_pct.clip(lower=0.01)
zero = z.empirical_below_pct == 0
ax.plot([0.01, 50], [0.01, 50], color=REF, linestyle=":", linewidth=1, label="Calibrated (empirical = nominal)")
ax.plot(z.nominal_alpha_pct, e, marker=M["ua"], color=C["ua"], markeredgecolor=SURF, markersize=8, linewidth=2,
        label=NAME["ua"])
ax.scatter(z.nominal_alpha_pct[zero], e[zero], s=70, facecolor=SURF, edgecolor=C["ua"], linewidth=2, zorder=4)
for _, r in z.iterrows():
    ax.annotate(f"z = {r.z:g}" + ("\n(no step below;\ndrawn at 0.01 %)" if r.empirical_below_pct == 0 else ""),
                (r.nominal_alpha_pct, max(r.empirical_below_pct, 0.01)),
                xytext=(6, 16) if r.empirical_below_pct == 0 else (4, -14), textcoords="offset points",
                fontsize=7.5, color=INK, ha="right" if r.empirical_below_pct == 0 else "left")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(0.5, 50); ax.set_ylim(0.008, 50)
ax.set_xlabel("Nominal per-step α (%)"); ax.set_ylabel("Steps below soc_min (%)")
ax.legend(loc="upper left", fontsize=7.5)
ax.set_title("Chance level: nominal vs closed loop", fontsize=9.5, loc="left", color=INK)
save(fig, "fig4_chance_calibration")
print("ok", sorted(os.listdir(OUT)))
