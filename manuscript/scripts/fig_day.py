"""Fig. (one hard day): calibrated forecast band, the confidence weight rho_k and the closed-loop SoC of
DET, DET-BO and UA on the development day with the largest forecast-error energy.

Run from the repository root:  python paper/manuscript/scripts/fig_day.py
Uses results/paper/solver_check/steps (same code as the final test) and the replay data.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(os.environ.get("KAIROS_ROOT", Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(ROOT / "src"))
import warnings  # noqa: E402

warnings.filterwarnings("ignore")
from MPC_costfunction import installed_renewable_w  # noqa: E402
from replay import build_data, load_config, named_periods, with_overrides  # noqa: E402

P = Path(os.environ.get("STUDY_RESULTS", ROOT / "results" / "paper"))
OUT = Path(__file__).resolve().parents[1] / "figures"
TZ = "Europe/Budapest"
SURF, INK, INK2, GRID, REF = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#8a8984"
C = {"det": "#2a78d6", "det_bo": "#eb6834", "ua": "#1baf7a"}
NAME = {"det": "Deterministic MPC", "det_bo": "Constant back-off", "ua": "Uncertainty-aware MPC"}
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False})

cfg = with_overrides(load_config(), {"SoC": {"E_capacity": 72}, "degradation": {"c_deg": 2e-5}})
data = build_data(cfg)
t0, t1 = named_periods(data, cfg)["development"]
d = data.loc[t0:t1 - pd.Timedelta(minutes=1)].copy()
mu = d.solar_mu + d.wind_mu
real = (d.solar_real + d.wind_real).clip(lower=0)
day = d.index.tz_convert(TZ).date
err_day = (mu - real).abs().groupby(day).sum()
work = d.demand_w.groupby(day).sum() > 0          # production days only (weekends have no load)
err_day = err_day[work]
hard = err_day.idxmax()

reg = json.load(open(P / "final_test" / "preregistration.json"))["selected"]["primary_threshold_pp_h"]
ua = next(x["overrides"] for x in json.load(open(P / "tuning" / "ua_pareto.json"))["points"] if x["trial"] == reg["ua"]["trial"])
lam = ua["weights"]["lambda"]
sigma = cfg["mpc"]["sigma_scale"] * np.sqrt(d.solar_sd ** 2 + d.wind_sd ** 2)
rho = 1.0 / (1.0 + lam * (sigma / installed_renewable_w(cfg)) ** 2)
bo = next(x["overrides"] for x in json.load(open(P / "tuning" / "det_bo_pareto.json"))["points"]
          if x["trial"] == reg["det_bo"]["trial"])["mpc"]["soc_backoff"]

m = pd.Series(day, index=d.index) == hard
x = d.index[m].tz_convert(TZ)
fig, axs = plt.subplots(3, 1, figsize=(6.4, 5.6), sharex=True, gridspec_kw={"height_ratios": [1.3, 0.8, 1.2]})
ax = axs[0]
ax.fill_between(x, (mu - 2 * sigma)[m].clip(lower=0), (mu + 2 * sigma)[m], color=C["ua"], alpha=0.18, linewidth=0,
                label="Forecast ±2σ (calibrated)")
ax.plot(x, mu[m], color=C["ua"], linewidth=1.6, label="GPR forecast mean")
ax.plot(x, real[m], color=INK, linewidth=1.2, linestyle="--", label="Realised renewable power")
ax.set_ylabel("Power (W)")
ax.legend(loc="upper left", fontsize=7.5)
ax = axs[1]
rho_def = 1.0 / (1.0 + 1000.0 * (sigma / installed_renewable_w(cfg)) ** 2)
ax.plot(x, rho[m], color=C["ua"], linewidth=1.8, label=f"tuned λ = {lam:.2f}")
ax.plot(x, rho_def[m], color=INK2, linewidth=1.2, linestyle="--", label="λ = 1000 (illustration)")
ax.set_ylim(0, 1.05)
ax.legend(loc="lower right", fontsize=7.5, ncol=2)
ax.set_ylabel("Confidence ρ")
ax = axs[2]
for c, trial in (("det", reg["det"]["trial"]), ("det_bo", reg["det_bo"]["trial"]), ("ua", reg["ua"]["trial"])):
    st = pd.read_csv(P / "solver_check" / "steps" / f"{c}_t{trial:02d}.csv")
    st.index = pd.to_datetime(st.t, utc=True)
    sm = pd.Series(st.index.tz_convert(TZ).date, index=st.index) == hard
    ax.plot(st.index[sm].tz_convert(TZ), 100 * st.soc[sm], color=C[c], linewidth=1.6, label=NAME[c])
ax.axhline(100 * cfg["SoC"]["soc_min"], color=INK2, linewidth=1)
ax.axhline(100 * (cfg["SoC"]["soc_min"] + bo), color=C["det_bo"], linewidth=0.9, linestyle=":")
ax.annotate("soc_min", (x[0], 100 * cfg["SoC"]["soc_min"]), xytext=(2, -10), textcoords="offset points", fontsize=7, color=INK2)
ax.set_ylabel("SoC (%)")
ax.legend(loc="upper left", fontsize=7.5)
import matplotlib.dates as mdates  # noqa: E402
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=x.tz))
ax.set_xlabel(f"Local time, {hard:%d %b %Y} (hardest production day of the development period)")
fig.tight_layout()
OUT.mkdir(exist_ok=True)
fig.savefig(OUT / "fig5_hard_day.pdf")
fig.savefig(OUT / "fig5_hard_day.png", dpi=300)
print("hard day", hard, "error energy Wh", round(err_day.max() * 0.25, 1), "rho min", round(float(rho[m].min()), 3))
