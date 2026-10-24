"""Every number and table of the manuscript, computed from the repository and results/paper.

Run from the repository root:  python paper/manuscript/scripts/make_numbers.py
Writes paper/manuscript/numbers.tex (one \\newcommand per number) and paper/manuscript/tables/*.tex.
Nothing in the manuscript is typed by hand: change a result, re-run this script, re-compile.
"""
import json
import os
import sys
from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("KAIROS_ROOT", Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(ROOT / "src"))
import warnings  # noqa: E402

warnings.filterwarnings("ignore")
from calibrate_uncertainty import calibrate, evaluate  # noqa: E402
from MPC_costfunction import _mpc_params, installed_renewable_w  # noqa: E402
from replay import build_data, load_config, named_periods, with_overrides  # noqa: E402

P = Path(os.environ.get("STUDY_RESULTS", ROOT / "results" / "paper"))
OUT = Path(__file__).resolve().parents[1]
SCEN = {"SoC": {"E_capacity": 72}, "degradation": {"c_deg": 2e-5}}
TZ = "Europe/Budapest"
macros = {}


def num(x, d=2):
    return f"{x:,.{d}f}".replace(",", "{,}")


def M(name, value):
    assert name.isalpha(), name
    macros[name] = value


def pct_change(a, b):
    return 100 * (a - b) / b


# ------------------------------------------------------------------ system and scenario
base = load_config()
cfg = with_overrides(base, SCEN)
p = _mpc_params(cfg)
M("Ecap", num(p["e_cap"], 0))
M("Ebase", num(base["SoC"]["E_capacity"], 0))
M("socmin", num(100 * p["soc_min"], 0))
M("socmax", num(100 * p["soc_max"], 0))
M("etabatt", num(p["eta"], 2))
M("pchmax", num(p["p_ch_max"], 0))
M("pdismax", num(p["p_dis_max"], 0))
M("cdegEurMWh", num(p["c_deg"] * 1e6, 0))
M("cdegBaseEurMWh", num(base["degradation"]["c_deg"] * 1e6, 1))
M("pvrated", num(cfg["pv"]["rated_power_w"], 0))
M("pveff", num(cfg["pv"]["efficiency"], 2))
w = cfg["wind"]
wind_rated = 0.5 * w["air_density"] * w["rotor_area_m2"] * w["power_coefficient"] * w["rated_speed_ms"] ** 3
M("windarea", num(w["rotor_area_m2"], 2))
M("windcp", num(w["power_coefficient"], 2))
M("windcutin", num(w["cut_in_speed_ms"], 0))
M("windrated", num(w["rated_speed_ms"], 0))
M("windcutout", num(w["cut_out_speed_ms"], 0))
M("windratedpower", num(wind_rated, 1))
M("sigmaref", num(installed_renewable_w(cfg), 1))
M("horizon", str(cfg["general"]["horizon"]))
M("dtmin", num(cfg["general"]["deltaT"] / 60, 0))
M("replansteps", str(cfg["replay"]["replan_steps"]))
M("replanmin", num(cfg["replay"]["replan_steps"] * cfg["general"]["deltaT"] / 60, 0))
M("unitpower", num(cfg["production"]["cat_power_w"], 0))
M("unittime", num(cfg["production"]["cat_time_s"], 0))
fixed_count_w = cfg["production"]["cat_power_w"] * 84 * cfg["production"]["cat_time_s"] / 3600
M("fixedcountw", num(fixed_count_w, 1))
M("violPenalty", num(cfg["replay"]["violation_penalty_eur_per_pp_h"], 2))
M("solverftol", "10^{-7}")
M("lat", num(cfg["openmeteo"]["latitude"], 3))
M("lon", num(cfg["openmeteo"]["longitude"], 3))
M("tilt", num(cfg["openmeteo"]["tilt"], 0))

# ------------------------------------------------------------------ data and periods
data = build_data(cfg)
per = named_periods(data, cfg)
names = {"calibration": "Cal", "tuning": "Tun", "development": "Dev", "final_test": "Fin"}
rows = []
for k, (a, b) in per.items():
    tag = names[k]
    M(f"start{tag}", f"{a.tz_convert(TZ):%Y-%m-%d}")
    M(f"stop{tag}", f"{(b - pd.Timedelta(minutes=1)).tz_convert(TZ):%Y-%m-%d}")
    d = data.loc[a:b - pd.Timedelta(minutes=1)]
    days = len(d) * 0.25 / 24
    M(f"days{tag}", num(days, 0))
    ren_real = (d.solar_real + d.wind_real).clip(lower=0)
    ren_mu = (d.solar_mu + d.wind_mu)
    err = ren_mu - ren_real
    rows.append(dict(period=k, start=f"{a.tz_convert(TZ):%d %b}", end=f"{(b - pd.Timedelta(minutes=1)).tz_convert(TZ):%d %b}",
                     days=days, demand_kwh=d.demand_w.sum() * 0.25 / 1000, ren_kwh=ren_real.sum() * 0.25 / 1000,
                     pv_share=100 * d.solar_real.clip(lower=0).sum() / ren_real.sum(),
                     price=d.price_eur_mwh.mean(), price_sd=d.price_eur_mwh.std(),
                     rmse=float(np.sqrt(np.mean(err ** 2))), bias=float(err.mean())))
pt = pd.DataFrame(rows)
for _, r in pt.iterrows():
    tag = names[r.period]
    M(f"rmse{tag}", num(r.rmse, 2))
    M(f"price{tag}", num(r.price, 0))
    M(f"ren{tag}", num(r.ren_kwh, 2))
    M(f"dem{tag}", num(r.demand_kwh, 2))
wf = pd.read_csv(ROOT / "data" / "Past_Forecast_Values.csv")
M("weatherStart", str(pd.to_datetime(wf.date.min()).date()))
M("heldout", cfg["replay"]["heldout_start"])
M("gprsamples", str(cfg["gpr"]["max_train_samples"]))

with open(OUT / "tables" / "tab_periods.tex", "w") as f:
    lab = {"calibration": "Calibration", "tuning": "Tuning", "development": "Development", "final_test": "Final test"}
    use = {"calibration": "fit $\\kappa$, $\\phi$", "tuning": "ParEGO, $4\\times2$ days",
           "development": "point selection, ablation, map", "final_test": "run once"}
    for _, r in pt.iterrows():
        f.write(f"{lab[r.period]} & {r.start}--{r.end} & {r.days:.0f} & {r.demand_kwh:.2f} & {r.ren_kwh:.2f} & "
                f"{r.pv_share:.0f} & {r.price:.0f} & {r.rmse:.2f} & {use[r.period]} \\\\\n")

# ------------------------------------------------------------------ calibration
c0, c1 = per["calibration"]
cal = calibrate(data, cfg, c0, c1)
M("calhours", str(cal["hours"]))
M("calrmse", num(cal["rmse_w"], 2))
M("calrmssigma", num(cal["rms_sigma_w"], 2))
M("covRawOne", num(cal["coverage_1sigma_pct"], 1))
M("covRawTwo", num(cal["coverage_2sigma_pct"], 1))
M("sigmascale", num(cal["sigma_scale"], 3))
M("phihour", num(cal["error_autocorr_1h"], 2))
M("phistep", num(cal["error_autocorr_step"], 3))
M("swcorr", num(cal["solar_wind_error_corr_daytime"], 3))
assert abs(cal["sigma_scale"] - cfg["mpc"]["sigma_scale"]) < 5e-4, "config sigma_scale differs from the calibration"
coef = cal["sigma_weather_coef"]
for tag, (a, b) in (("Dev", per["development"]), ("Fin", per["final_test"])):
    ev = evaluate(data, cfg, a, b, cal["sigma_scale"], coef)
    for model, mt in (("constant", "C"), ("weather", "W")):
        for part, pp in (("all", "All"), ("hard_days", "Hard"), ("other_days", "Other")):
            M(f"cov{tag}{mt}{pp}One", num(ev[f"{model}_{part}_cov1"], 1))
            M(f"cov{tag}{mt}{pp}Two", num(ev[f"{model}_{part}_cov2"], 1))
            M(f"rts{tag}{mt}{pp}", num(ev[f"{model}_{part}_rmse_to_sigma"], 2))

# ------------------------------------------------------------------ tuning
ts = cfg["tuning"]
M("trials", str(len(pd.read_csv(P / "tuning" / "ua_trials.csv"))))
M("initpoints", str(ts["initial_points"]))
fronts = {}
for c in ("det", "det_bo", "ua"):
    pj = json.load(open(P / "tuning" / f"{c}_pareto.json"))
    fronts[c] = pj
    M("front" + c.replace("_", "").title().replace("Bo", "Bo"), str(len(pj["points"])))
ep = fronts["ua"]["episodes"]
M("episodes", str(len(ep)))
M("episodeDays", num((pd.Timestamp(ep[0][1]) - pd.Timestamp(ep[0][0])).days, 0))
M("episodeList", ", ".join(f"{pd.Timestamp(a).tz_convert(TZ):%d}--{(pd.Timestamp(b) - pd.Timedelta(minutes=1)).tz_convert(TZ):%d %b}" for a, b in ep))

# ------------------------------------------------------------------ development fronts + pre-registration
f = pd.read_csv(P / "dev_fronts" / "fronts_dev.csv")
reg = json.load(open(P / "final_test" / "preregistration.json"))
sel = reg["selected"]["primary_threshold_pp_h"]
sec = reg["selected"]["secondary_threshold_pp_h"]
M("thrPrimary", num(reg["primary_threshold_pp_h"], 1))
M("thrSecondary", num(reg["secondary_threshold_pp_h"], 1))
M("prereqDate", reg["written_utc"][:10])
for c, t in (("det", "Det"), ("det_bo", "Bo"), ("ua", "Ua")):
    M(f"sel{t}", f"t{sel[c]['trial']:02d}")
    M(f"selDev{t}Cost", num(sel[c]["dev_cost"], 4))
    M(f"selDev{t}Viol", num(sel[c]["dev_viol"], 2))
M("selUaSec", f"t{sec['ua']['trial']:02d}")
M("devFrontPoints", str(int(f.joint_front.sum())))
M("devFrontUa", str(int((f.joint_front & (f.ctrl == "ua")).sum())))
M("devPoints", str(len(f)))
ua15 = f[(f.ctrl == "ua") & (f.trial == 15)].iloc[0]
M("uaFifteenTun", num(ua15.tun_viol, 4))
M("uaFifteenDev", num(ua15.dev_viol, 1))
rk = f[["tun_viol", "dev_viol"]].rank()
M("rankCorr", num(rk.corr().iloc[0, 1], 2))
with open(OUT / "tables" / "tab_fronts.tex", "w") as fh:
    lab = {"det": "DET", "det_bo": "DET-BO", "ua": "UA"}
    for _, r in f.sort_values(["ctrl", "dev_cost"]).iterrows():
        mark = "$\\star$" if r.trial == sel[r.ctrl]["trial"] else ""
        fh.write(f"{lab[r.ctrl]} & t{int(r.trial):02d}{mark} & {r.tun_cost:.4f} & {r.tun_viol:.4f} & {r.dev_cost:.4f} & "
                 f"{r.dev_viol:.3f} & {'yes' if r.joint_front else ''} \\\\\n")

# selected weights
for c, t in (("det", "Det"), ("det_bo", "Bo"), ("ua", "Ua")):
    ov = next(x["overrides"] for x in fronts[c]["points"] if x["trial"] == sel[c]["trial"])
    wv = ov["weights"]
    M(f"w{t}x", f"{wv['w_x']:.2e}".replace("e-0", "\\times10^{-").replace("e-", "\\times10^{-") + "}")
    M(f"w{t}ff", f"{wv['w_ff']:.2e}".replace("e-0", "\\times10^{-").replace("e-", "\\times10^{-") + "}")
    M(f"w{t}du", f"{wv['w_delta_u']:.0e}".replace("e-0", "\\times10^{-").replace("e-", "\\times10^{-") + "}")
    if c == "det_bo":
        M("backoff", num(ov["mpc"]["soc_backoff"], 3))
        M("backoffPct", num(100 * ov["mpc"]["soc_backoff"], 1))
    if c == "ua":
        M("lambdaUa", num(wv["lambda"], 2))
        M("zUa", num(ov["mpc"]["soc_chance_z"], 2))
        M("alphaUa", num(100 * 0.5 * (1 - erf(ov["mpc"]["soc_chance_z"] / sqrt(2))), 1))

# ------------------------------------------------------------------ final test
s = pd.read_csv(P / "final_test" / "summary.csv").set_index(["plant", "variant"])
b = pd.read_csv(P / "final_test" / "paired_bootstrap.csv")
M("finDaysBoot", str(int(b.days.iloc[0])))
V = ["grid_only", "rule", "det", "det_bo", "ua", "ua_rho_only", "ua_margin_only", "ua_secondary", "oracle"]
tag = {"grid_only": "Grid", "rule": "Rule", "det": "Det", "det_bo": "Bo", "ua": "Ua", "ua_rho_only": "Rho",
       "ua_margin_only": "Margin", "ua_secondary": "Sec", "oracle": "Oracle"}
for v in V:
    t = tag[v]
    ph, bm = s.loc[("physical", v)], s.loc[("bms", v)]
    M(f"fin{t}Cost", num(ph.net_cost_eur, 4))
    M(f"fin{t}Viol", num(ph.violation_pp_h, 2))
    M(f"fin{t}MaxViol", num(ph.max_violation_pp, 2))
    M(f"fin{t}BmsCost", num(bm.net_cost_eur, 4))
    M(f"fin{t}Prot", str(int(bm.protection_steps)))
    M(f"fin{t}Extra", num(1000 * bm.extra_grid_eur, 2))
    M(f"fin{t}Cyc", num(ph.cycles_per_day, 2))
    if not np.isnan(ph.solver_success_pct):
        M(f"fin{t}Solver", num(ph.solver_success_pct, 1))
        M(f"fin{t}Solve", num(ph.solve_median_s, 2))
M("finGridSaveUa", num(-pct_change(s.loc[("physical", "ua")].net_cost_eur, s.loc[("physical", "grid_only")].net_cost_eur), 1))
M("finRuleSaveUa", num(-pct_change(s.loc[("physical", "ua")].net_cost_eur, s.loc[("physical", "rule")].net_cost_eur), 1))
M("finOracleGap", num(-pct_change(s.loc[("physical", "oracle")].net_cost_eur, s.loc[("physical", "ua")].net_cost_eur), 1))
M("finDetOracleGap", num(pct_change(s.loc[("physical", "det")].net_cost_eur, s.loc[("physical", "oracle")].net_cost_eur), 1))
M("finDemand", num(s.loc[("physical", "ua")].demand_kwh, 2))
M("finRenew", num(s.loc[("physical", "ua")].renewable_kwh, 2))


def boot(plant, a, bb, kpi):
    return b[(b.plant == plant) & (b.a == a) & (b.b == bb) & (b.kpi == kpi)].iloc[0]


def bootcell(plant, a, bb, kpi, scale=1.0, d=1):
    r = boot(plant, a, bb, kpi)
    if r.b_total == 0 and r.a_total == 0:
        return "--"
    pc = "" if np.isnan(r.diff_pct) else ("$\\pm$0\\,\\% " if abs(r.diff_pct) < 0.005 else f"{r.diff_pct:+.{d}f}\\,\\% ")
    sig = r.lo_total > 0 or r.hi_total < 0
    return f"{pc}[{r.lo_total * scale:+.3g}, {r.hi_total * scale:+.3g}]{'$^{*}$' if sig else ''}"


for bb, t in (("det", "Det"), ("det_bo", "Bo"), ("ua_rho_only", "Rho"), ("ua_margin_only", "Margin"), ("oracle", "Oracle")):
    for plant, kp, mt in (("physical", "viol", "Viol"), ("physical", "cost", "Cost"), ("bms", "prot", "Prot"), ("bms", "extra", "Extra"), ("bms", "cost", "BmsCost")):
        r = boot(plant, "ua", bb, kp)
        if not np.isnan(r.diff_pct):
            M(f"bt{t}{mt}Pct", num(abs(r.diff_pct), 0 if abs(r.diff_pct) >= 10 else 2))
        M(f"bt{t}{mt}P", num(r.p_a_better, 3))
with open(OUT / "tables" / "tab_final.tex", "w") as fh:
    lab = {"grid_only": "Grid only", "rule": "Rule-based", "det": "DET (t%02d)" % sel["det"]["trial"],
           "det_bo": "DET-BO (t%02d)" % sel["det_bo"]["trial"], "ua": "UA (t%02d)" % sel["ua"]["trial"],
           "ua_rho_only": "UA, $\\rho$ only", "ua_margin_only": "UA, margin only",
           "ua_secondary": "UA (t%02d, secondary)" % sec["ua"]["trial"], "oracle": "Oracle forecast"}
    for v in V:
        ph, bm = s.loc[("physical", v)], s.loc[("bms", v)]
        solver = "--" if np.isnan(ph.solver_success_pct) else f"{ph.solver_success_pct:.1f}"
        fh.write(f"{lab[v]} & {ph.net_cost_eur:.4f} & {ph.violation_pp_h:.2f} & {ph.max_violation_pp:.2f} & "
                 f"{bm.net_cost_eur:.4f} & {int(bm.protection_steps)} & {1000 * bm.extra_grid_eur:.2f} & {solver} \\\\\n")
        if v in ("rule", "ua_secondary"):
            fh.write("\\midrule\n")
with open(OUT / "tables" / "tab_boot.tex", "w") as fh:
    lab = {"det": "DET", "det_bo": "DET-BO", "ua_rho_only": "UA, $\\rho$ only", "ua_margin_only": "UA, margin only",
           "oracle": "Oracle"}
    for bb in ("det", "det_bo", "ua_rho_only", "ua_margin_only", "oracle"):
        fh.write(f"{lab[bb]} & {bootcell('physical', 'ua', bb, 'cost', 1000, 2)} & {bootcell('physical', 'ua', bb, 'viol')} & "
                 f"{bootcell('bms', 'ua', bb, 'prot', 1, 0)} & {bootcell('bms', 'ua', bb, 'extra', 1000)} \\\\\n")

# ------------------------------------------------------------------ development ablation (before the final test)
da = pd.read_csv(P / "dev_ablation" / "summary.csv").set_index(["plant", "variant"])
for v in ("det", "det_bo", "ua", "ua_rho_only", "ua_margin_only", "oracle"):
    M(f"devAbl{tag[v]}Viol", num(da.loc[("physical", v)].violation_pp_h, 2))
    M(f"devAbl{tag[v]}Prot", str(int(da.loc[("bms", v)].protection_steps)))

# ------------------------------------------------------------------ solver analysis and SoC recovery
sc = pd.read_csv(P / "solver_check" / "solver_vs_violation.csv").set_index("run")
M("solverFailMin", num(sc.failed_solves_pct.min(), 1))
M("solverFailMax", num(sc.failed_solves_pct.max(), 1))
M("onsetsTotal", str(int(sc.onsets.sum())))
M("onsetsFailed", str(int(sc.onsets_under_failed.sum())))
M("violFailedMin", num(sc.viol_under_failed_pct.min(), 0))
M("violFailedMax", num(sc.viol_under_failed_pct.max(), 0))
M("iterFailedMin", num(sc.median_iter_failed.min(), 0))
M("iterFailedMax", num(sc.median_iter_failed.max(), 0))
M("iterOkMin", num(sc.median_iter_ok.min(), 0))
M("iterOkMax", num(sc.median_iter_ok.max(), 0))
rc = pd.read_csv(P / "recovery_check" / "before_after.csv").set_index("run")
for run, t in (("det_t%02d" % sel["det"]["trial"], "Det"), ("det_bo_t%02d" % sel["det_bo"]["trial"], "Bo"),
               ("ua_t%02d" % sel["ua"]["trial"], "Ua")):
    r = rc.loc[run]
    M(f"rec{t}Before", num(r.viol_before, 2))
    M(f"rec{t}After", num(r.viol_after, 2))
    M(f"rec{t}SolBefore", num(r.solver_before, 1))
    M(f"rec{t}SolAfter", num(r.solver_after, 1))
    M(f"rec{t}CostChange", num(abs(pct_change(r.cost_after, r.cost_before)), 2))

# ------------------------------------------------------------------ decision map
mp = pd.read_csv(P / "decision_map_recovery" / "map.csv").sort_values(["r_E", "cap_wh", "error_scale"])
old = pd.read_csv(P / "decision_map" / "map.csv")
bo = float(macros["backoff"])
M("kappaSigma", num(mp.kappa_sigma.iloc[0], 2))
lo, hi = mp[mp.r_E <= bo * 1.25], mp[mp.r_E > 2 * bo]
M("mapLowMaxViol", num(max(lo.bo_viol.max(), lo.ua_viol.max()), 2))
M("mapLowCostAbs", num(lo.cost_diff_pct.abs().max(), 1))
M("mapHighBoMin", num(hi.bo_viol.min(), 1))
M("mapHighBoMax", num(hi.bo_viol.max(), 1))
M("mapHighUaMin", num(hi.ua_viol.min(), 2))
M("mapHighUaMax", num(hi.ua_viol.max(), 2))
ratio = hi.bo_viol / hi.ua_viol
M("mapHighRatioMin", num(ratio.min(), 0))
M("mapHighRatioMax", num(ratio.max(), 0))
M("mapHighCostMin", num(hi.cost_diff_pct.min(), 1))
M("mapHighCostMax", num(hi.cost_diff_pct.max(), 1))
M("mapLowThr", num(lo.r_E.max(), 3))
M("mapHighThr", num(hi.r_E.min(), 3))
M("mapCells", str(len(mp)))
M("rEbase", num(mp[(mp.cap_wh == 72) & (mp.error_scale == 1.0) & (mp.replan_steps == 4)].r_E.iloc[0], 3))
oo = old.merge(mp, on=["cap_wh", "error_scale", "replan_steps"], suffixes=("_old", ""))
w1 = oo.loc[oo.bo_viol_old.idxmax()]
w2 = oo.loc[oo.ua_viol_old.idxmax()]
M("oldOutBo", num(w1.bo_viol_old, 1))
M("mapBaseBoSingle", num(old[(old.cap_wh == 72) & (old.error_scale == 1.0) & (old.replan_steps == 4)].bo_viol.iloc[0], 2))
M("newOutBo", num(w1.bo_viol, 2))
M("oldOutUa", num(w2.ua_viol_old, 1))
M("newOutUa", num(w2.ua_viol, 2))
with open(OUT / "tables" / "tab_map.tex", "w") as fh:
    for _, r in mp.iterrows():
        fh.write(f"{int(r.cap_wh)} & {r.error_scale:g} & {int(r.replan_steps) * 15 // 60} & {r.r_E:.3f} & {r.r_P:.3f} & "
                 f"{r.bo_viol:.3f} & {r.ua_viol:.3f} & {r.cost_diff_pct:+.2f} \\\\\n")
z = pd.read_csv(P / "decision_map_recovery" / "chance_calibration.csv")
with open(OUT / "tables" / "tab_chance.tex", "w") as fh:
    for _, r in z.iterrows():
        fh.write(f"{r.z:g} & {r.nominal_alpha_pct:.1f} & {r.empirical_below_pct:.2f} & {r.viol_pp_h:.3f} & {r.net_cost_eur:.4f} \\\\\n")
nz = z[z.empirical_below_pct > 0]
fac = nz.nominal_alpha_pct / nz.empirical_below_pct
M("chanceFacMin", num(fac.min(), 0))
M("chanceFacMax", num(fac.max(), 0))

# ------------------------------------------------------------------ the confidence weight on this system
dd = data.loc[per["development"][0]:per["development"][1] - pd.Timedelta(minutes=1)]
sig = cfg["mpc"]["sigma_scale"] * np.sqrt(dd.solar_sd ** 2 + dd.wind_sd ** 2)
ratio_s = sig[sig > 0] / installed_renewable_w(cfg)
M("sigRatioMed", num(100 * ratio_s.median(), 1))
M("sigRatioNinetyFive", num(100 * ratio_s.quantile(0.95), 1))
lam = float(macros["lambdaUa"])
M("rhoMinUa", num(float((1 / (1 + lam * ratio_s ** 2)).min()), 3))
M("rhoMinDefault", num(float((1 / (1 + 1000 * ratio_s ** 2)).min()), 2))
lams = [x["overrides"]["weights"]["lambda"] for x in fronts["ua"]["points"]]
M("frontLowLambda", str(sum(1 for v in lams if v < 10)))
M("frontLambdaMax", num(max(lams), 0))

# ------------------------------------------------------------------ hardest production day of the development period (Fig. 5)
mu_d = dd.solar_mu + dd.wind_mu
real_d = (dd.solar_real + dd.wind_real).clip(lower=0)
dayk = dd.index.tz_convert(TZ).date
err_day = (mu_d - real_d).abs().groupby(dayk).sum()
err_day = err_day[dd.demand_w.groupby(dayk).sum() > 0]
hard = err_day.idxmax()
M("hardDay", f"{pd.Timestamp(hard):%d %B %Y}")
M("hardErrWh", num(err_day.max() * 0.25, 1))
for c, t in (("det", "Det"), ("det_bo", "Bo"), ("ua", "Ua")):
    st = pd.read_csv(P / "solver_check" / "steps" / f"{c}_t{sel[c]['trial']:02d}.csv")
    st.index = pd.to_datetime(st.t, utc=True)
    m_ = pd.Series(st.index.tz_convert(TZ).date, index=st.index) == hard
    M(f"hard{t}MinSoc", num(100 * st.soc[m_].min(), 1))

# ------------------------------------------------------------------ tables: selected weights, development ablation
with open(OUT / "tables" / "tab_weights.tex", "w") as fh:
    for c, t, lab in (("det", "Det", "DET"), ("det_bo", "Bo", "DET-BO"), ("ua", "Ua", "UA")):
        extra = {"det": "--", "det_bo": f"$b={macros['backoff']}$", "ua": f"$\\lambda={macros['lambdaUa']}$, $z={macros['zUa']}$"}[c]
        fh.write(f"{lab} & {macros['sel' + t]} & ${macros['w' + t + 'x']}$ & ${macros['w' + t + 'ff']}$ & ${macros['w' + t + 'du']}$ & {extra} & "
                 f"{macros['selDev' + t + 'Cost']} & {macros['selDev' + t + 'Viol']} \\\\\n")
with open(OUT / "tables" / "tab_devabl.tex", "w") as fh:
    lab = {"grid_only": "Grid only", "rule": "Rule-based", "det": "DET", "det_bo": "DET-BO", "ua": "UA",
           "ua_rho_only": "UA, $\\rho$ only", "ua_margin_only": "UA, margin only", "oracle": "Oracle forecast"}
    for v in lab:
        ph, bm = da.loc[("physical", v)], da.loc[("bms", v)]
        fh.write(f"{lab[v]} & {ph.net_cost_eur:.4f} & {ph.violation_pp_h:.2f} & {bm.net_cost_eur:.4f} & {int(bm.protection_steps)} \\\\\n")

# ------------------------------------------------------------------ search space of the tuning
from tune_mpc import VIOLATION_NOISE_PP_H, tuning_settings  # noqa: E402
M("violNoise", num(VIOLATION_NOISE_PP_H, 2))
spaces = {c: tuning_settings(cfg, c)["params"] for c in ("det", "det_bo", "ua")}
sym = {"weights.w_x": "$w_x$", "weights.w_ff": "$w_{\\mathrm{ff}}$", "weights.w_delta_u": "$w_{\\Delta u}$",
       "weights.lambda": "$\\lambda$", "mpc.soc_chance_z": "$z$", "mpc.soc_backoff": "$b$"}


def rng_txt(lo, hi, kind):
    f = (lambda v: f"10^{{{int(np.log10(v))}}}") if kind == "log" else (lambda v: f"{v:g}")
    return f"$[{f(lo)}, {f(hi)}]$" + ("$^\\dagger$" if kind == "lin" else "")


with open(OUT / "tables" / "tab_space.tex", "w") as fh:
    for k in sym:
        cells = [rng_txt(*spaces[c][k]) if k in spaces[c] else "--" for c in ("det", "det_bo", "ua")]
        fh.write(f"{sym[k]} & " + " & ".join(cells) + " \\\\\n")

# ------------------------------------------------------------------ variability of the uncertainty
va = pd.read_csv(P / "variability" / "variability.csv")
sh = pd.read_csv(P / "variability" / "sigma_shapes.csv").set_index("shape")
M("kappaAmplified", num(sh.loc["amplified", "kappa_sigma"], 2))
M("varCells", str(len(va)))
va["ratio_const"] = va.constant_viol / va.ua_viol
va["ratio_amp"] = va.ua_viol / va.amplified_viol
va["cost_spread_pct"] = 100 * (va[["constant_cost", "ua_cost", "amplified_cost"]].max(axis=1)
                               / va[["constant_cost", "ua_cost", "amplified_cost"]].min(axis=1) - 1)
M("varConstRatioMin", num(va.ratio_const.min(), 1))
M("varConstRatioMax", num(va.ratio_const.max(), 1))
imp = va[va.amplified_viol < va.ua_viol]
M("varAmpLower", str(len(imp)))
M("varAmpRatioMin", num(imp.ratio_amp.min(), 1))
M("varAmpRatioMax", num(imp.ratio_amp.max(), 1))
w = va[va.amplified_viol >= va.ua_viol]
M("varAmpWorseUa", num(w.ua_viol.iloc[0], 3) if len(w) else "--")
M("varAmpWorseAmp", num(w.amplified_viol.iloc[0], 3) if len(w) else "--")
M("varCostSpreadMax", num(va.cost_spread_pct.max(), 2))
b = va[(va.cap_wh == 72) & (va.error_scale == 1.0) & (va.replan_steps == 4)].iloc[0]
M("varBaseConst", num(b.constant_viol, 2))
M("varBaseUa", num(b.ua_viol, 2))
M("varBaseAmp", num(b.amplified_viol, 3))
M("varConstBelowBo", str(int((va.constant_viol < va.bo_viol).sum())))
with open(OUT / "tables" / "tab_var.tex", "w") as fh:
    for _, r in va.sort_values("r_E").iterrows():
        fh.write(f"{int(r.cap_wh)} & {r.error_scale:g} & {int(r.replan_steps) * 15 // 60} & {r.r_E:.3f} & "
                 f"{r.bo_viol:.3f} & {r.constant_viol:.3f} & {r.ua_viol:.3f} & {r.amplified_viol:.3f} & "
                 f"{r.ua_cost:.4f} \\\\\n")

# ------------------------------------------------------------------ capacity economics
ce = pd.read_csv(P / "capacity_economics" / "capacity_economics.csv")
M("gridOnlyDev", num(ce.grid_only_eur.iloc[0], 4))
c1 = ce[ce.error_scale == 1.0].set_index("cap_wh")
for cap, nm in ((36, "S"), (72, "M"), (144, "L")):
    M(f"cap{nm}Save", num(c1.loc[cap, "ua_saving_eur"], 3))
    M(f"cap{nm}PerWh", num(c1.loc[cap, "ua_saving_per_wh_meur"], 1))
    M(f"cap{nm}Share", num(100 * c1.loc[cap, "ua_share_of_largest_saving"], 0))
M("capMargMS", num(c1.loc[72, "ua_marginal_meur_per_wh"], 1))
M("capMargLM", num(c1.loc[144, "ua_marginal_meur_per_wh"], 2))
M("capShareMin", num(100 * ce[ce.cap_wh == 36].ua_share_of_largest_saving.min(), 0))
M("capShareMax", num(100 * ce[ce.cap_wh == 36].ua_share_of_largest_saving.max(), 0))
with open(OUT / "tables" / "tab_cap.tex", "w") as fh:
    for _, r in ce.iterrows():
        marg = "--" if pd.isna(r.ua_marginal_meur_per_wh) else f"{r.ua_marginal_meur_per_wh:.2f}"
        fh.write(f"{int(r.cap_wh)} & {r.error_scale:g} & {r.r_E:.3f} & {r.ua_saving_eur:.3f} & "
                 f"{100 * r.ua_share_of_largest_saving:.0f} & {r.ua_saving_per_wh_meur:.2f} & {marg} & "
                 f"{r.bo_viol_pp_h:.2f} & {r.ua_viol_pp_h:.2f} \\\\\n")

# ------------------------------------------------------------------ write
with open(OUT / "numbers.tex", "w") as fh:
    fh.write("% generated by scripts/make_numbers.py - do not edit\n")
    for k, v in macros.items():
        fh.write(f"\\newcommand{{\\{k}}}{{{v}\\xspace}}\n")
print(f"{len(macros)} numbers, tables in {OUT / 'tables'}")
