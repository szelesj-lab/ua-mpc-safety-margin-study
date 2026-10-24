"""Fig. 6: (a) variability of the forecast uncertainty, (b) saving against capacity. From results/paper."""
import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(os.environ.get("KAIROS_ROOT", Path(__file__).resolve().parents[3]))
P = Path(os.environ.get("STUDY_RESULTS", ROOT / "results" / "paper"))
OUT = Path(__file__).resolve().parents[1] / "figures"
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BO = "#eb6834"
UA = {"constant": "#9fdcc3", "ua": "#1baf7a", "amplified": "#0b5e40"}   # one hue, light -> dark = kappa_sigma
plt.rcParams.update({"font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "font.family": "DejaVu Sans"})

va = pd.read_csv(P / "variability" / "variability.csv").sort_values("r_E")
sh = pd.read_csv(P / "variability" / "sigma_shapes.csv").set_index("shape")
ce = pd.read_csv(P / "capacity_economics" / "capacity_economics.csv")

fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"width_ratios": [1.5, 1]})
for ax in (a, b):
    ax.set_facecolor(SURF); ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
fig.patch.set_facecolor(SURF)

lab = [f"{int(r.cap_wh)} Wh, s={r.error_scale:g}\n{int(r.replan_steps) * 15 // 60}-h re-plan\n$r_E$={r.r_E:.3f}"
       for _, r in va.iterrows()]
series = [("bo_viol", "Constant back-off", BO),
          ("constant_viol", f"UA, constant σ (κσ={sh.loc['constant','kappa_sigma']:.2f})", UA["constant"]),
          ("ua_viol", f"UA, real σ (κσ={sh.loc['real','kappa_sigma']:.2f})", UA["ua"]),
          ("amplified_viol", f"UA, doubled variability (κσ={sh.loc['amplified','kappa_sigma']:.2f})", UA["amplified"])]
x = np.arange(len(va)); w = 0.2
for i, (col, name, c) in enumerate(series):
    a.bar(x + (i - 1.5) * w, va[col], w - 0.02, color=c, label=name, edgecolor=SURF, lw=0.5)
a.set_yscale("log"); a.set_ylabel("SoC-band violation (pp·h, log)")
a.set_xticks(x); a.set_xticklabels(lab, fontsize=6.5)
a.legend(frameon=False, fontsize=6.5, loc="upper left")
a.set_ylim(0.01, 60)
a.set_title("(a) Same mean σ, different variability in time", fontsize=8, loc="left", color=INK)

c = ce[ce.error_scale == 1.0].sort_values("cap_wh")
b.plot(c.cap_wh, c.ua_saving_eur, color=UA["ua"], lw=2, marker="o", ms=6, mec=SURF, mew=1.5)
for _, r in c.iterrows():
    b.annotate(f"{100 * r.ua_share_of_largest_saving:.0f} %\n{r.ua_saving_per_wh_meur:.1f} m€/Wh",
               (r.cap_wh, r.ua_saving_eur), textcoords="offset points", xytext=(0, -26), ha="center",
               fontsize=6.5, color=INK2)
b.set_xticks(c.cap_wh); b.set_xlabel("Usable capacity (Wh)"); b.set_ylabel("Saving vs. grid only (€, 22 days)")
b.set_ylim(0.15, 0.4); b.set_xlim(20, 160)
b.set_title("(b) UA-MPC saving against capacity", fontsize=8, loc="left", color=INK)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(OUT / f"fig6_variability_capacity.{ext}", dpi=200, facecolor=SURF)
print("written", OUT / "fig6_variability_capacity.pdf")
