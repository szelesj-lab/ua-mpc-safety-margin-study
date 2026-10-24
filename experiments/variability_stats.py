"""kappa_sigma and mean sigma of the three sigma shapes of the variability experiment (development period).
Output: variability/sigma_shapes.csv"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from engine import PAPER, SCEN, reshape_sigma
from replay import build_data, load_config, named_periods, with_overrides

base = with_overrides(load_config(), SCEN)
data = build_data(base)
t0, t1 = named_periods(data, base)["development"]
rows = []
for shape in ("constant", "real", "amplified"):
    d = data if shape == "real" else reshape_sigma(data, shape, t0, t1)
    s = np.sqrt(d.solar_sd ** 2 + d.wind_sd ** 2).loc[t0:t1]
    rows.append(dict(shape=shape, sigma_mean_w=float(s.mean()), sigma_std_w=float(s.std()),
                     kappa_sigma=float(s.std() / s.mean()), sigma_p95_w=float(s.quantile(0.95)),
                     share_clipped_to_zero=float((s <= 0).mean())))
r = pd.DataFrame(rows)
r.to_csv(os.path.join(PAPER, "variability", "sigma_shapes.csv"), index=False)
print(r.round(4).to_string(index=False))
