# Literature review: uncertainty-aware battery MPC, variability, ratios and small batteries

This review organises the 124 records of `literature.csv` (BibTeX keys in `references.bib`) around the questions of
the study. Keys in square brackets refer to `references.bib`. The column `verified` in `literature.csv` says how each
record was checked (see `README.md`).

## 1. Deterministic MPC for storage and energy management

Receding-horizon economic control of batteries and microgrids is mature. The theory of constrained and economic MPC
[mayne2000constrained, rawlings2017model, angeli2012average, ellis2014tutorial] underpins energy-management systems
for microgrids [parisio2014mpc, palmabehnke2013microgrid, silvente2015rolling, kriett2012residential,
bruni2015domestic, garciatorres2016hydrogen, torreglosa2015energy]; its stochastic counterpart is [silvente2018rolling], buildings with PV and storage
[cai2019aging, tarragona2020model, drgona2020allyouneed, serale2018mpc] and real commercial sites
[goldsworthy2022cloud]. Reviews [hu2021mpcmicrogrid, garciatorres2021mpcfunctionalities] show that most deployed
schemes are deterministic: the forecast is used as if it were exact and robustness comes from re-planning.
This is the DET baseline of the study.

## 2. Stochastic, chance-constrained and robust MPC; back-offs

Chance-constrained programming [charnes1959chance] and its stochastic-MPC forms [mesbah2016stochastic,
farina2016stochastic, lorenzen2017constraint, kouvaritakis2016model, hewing2020learning,
hewing2020cautious] tighten constraints by
quantiles of the predicted uncertainty; scenario methods [calafiore2006scenario, schildbach2014scenario] use samples.
Energy applications include buildings [oldewurtel2012use, oldewurtel2014stochastic, parisio2013scenario,
parisio2014implementation], microgrids [velarde2017comparison, wu2021mpcev, cheng2020probabilistic, arnold2011mpc]
and stationary batteries [kumar2018stochastic, kumar2019benchmarking]. Robust alternatives bound the worst case
[bemporad1999robust, mayne2005robust, zhang2013robust, hu2024improved]; risk measures bound the depth of violations
[lei2021optimal, narayan2017risk, rockafellar2000optimization]. In power systems, chance constraints with renewable
uncertainty are standard [bienstock2014chance, roald2018chance].

A constant back-off is the simplest tightening. Kumar et al. [kumar2019benchmarking] include it as a baseline and call
it ad hoc; GP-based back-offs [bradford2020backoffs] and adaptive tightening under time-varying uncertainty
[bujarbaruah2021adaptive] make it uncertainty-dependent. Schildbach et al. [schildbach2014scenario] show that
closed-loop violation frequencies are far below the open-loop chance level, which our chance-level experiment
confirms (nominal α 36–106 times the observed frequency).

**Gap.** Few studies compare an uncertainty-aware margin with a constant back-off tuned with the same effort, and
none we found maps when the two differ.

## 3. Forecasts and their calibration

Physical, statistical and hybrid PV forecasting are reviewed in [antonanzas2016review, voyant2017machine,
vandermeer2018review]; wind in [pinson2013wind]; the future of renewable forecasting in [sweeney2020future] and
probabilistic energy forecasting in [hong2016probabilistic]. Gaussian processes give a predictive distribution
[rasmussen2006gaussian, najibi2021enhanced]; heteroscedastic GPs let the uncertainty vary with the input
[kersting2007most]. Calibration and sharpness [gneiting2007probabilistic] and proper scores [gneiting2007scoring] are
the evaluation standard. Price forecasting is reviewed in [weron2014electricity, lago2021forecasting]; data come
from ENTSO-E [hirth2018entsoe] and Open-Meteo [zippenfenig2023openmeteo].

The value of forecasts for storage is documented: perfect forecasts overstate PV-battery value by 1–8 %
[mirletz2023impacts]; forecast-error costs are substantial against PV levelised costs [gandhi2024value]; reviews of
forecasting in storage operation and sizing [sharma2021use, seervi2021renewable]; MPC with real forecast errors
[manzano2022economic] and forecast-driven decision support [tariq2026pvforecasting].

## 4. Why the variability of the uncertainty matters

Renewable output varies on all time scales [widen2015variability, engeland2017spacetime, krakauer2017interannual].
Variability metrics — the variability index [stein2012variability], fleet variability [hoff2010quantifying,
mills2010implications] and wavelet variability [lave2013wavelet] — show that quiet and turbulent periods alternate.
A constant safety margin must be sized for the turbulent periods and is then too large in the quiet ones, or sized
for the average and too small in the turbulent ones. A margin proportional to the time-varying σ resolves this.

**Evidence from this study.** The UA-MPC was replayed with the same weights and the same mean σ, but with σ held
constant in time (κσ = 0) or with its deviation from the mean doubled (κσ = 0.61 instead of 0.31), in four cells of the
decision map. Holding σ constant raised the violation 2.3–3.8-fold in every cell; doubling the variability lowered it
3–5-fold in three cells and raised it in one (4-h re-planning). The costs differed by at most 0.11 %
(`results/variability/variability.csv`). Where σ is large matters, not only how large it is on average. The
constant-σ variant still beat the tuned constant back-off in three of the four cells, because its margin still grows
with the capacity, the error level and the re-planning window.

## 5. Ratios as design rules

Storage design is routinely reduced to dimensionless ratios:

| Ratio | Meaning | Sources |
|---|---|---|
| Self-consumption / self-sufficiency | share of PV used on site / share of load covered | [luthander2015selfconsumption, quoilin2016quantifying, alnaser2021transition] |
| Normalised capacity (kWh per MWh/a, kWh per kWp) | battery size relative to annual load or PV size | [weniger2014sizing, quoilin2016quantifying, mason2016energetic] |
| Energy-to-power ratio, C-rate | storage duration per application | [hesse2017lithium, dowling2020role] |
| Battery size vs. ramp limit | capacity needed for a ramp-rate limit | [makibar2017relation, gonzalezmoreno2022pv] |
| PV-to-inverter / battery-to-PV | configuration of PV-plus-storage plants | [diorio2020model] |
| Variability index | irradiance variability relative to clear sky | [stein2012variability] |
| Design space (cost × duration × efficiency) | where long-duration storage pays | [sepulveda2021design] |
| Capacity × uncertainty × horizon map | where battery scheduling performs well | [demiguel2026mapping] |

The study adds **r_E**: the 95 % energy deficit that can build up until the next re-plan, divided by the usable
capacity. It is directly comparable with a constant back-off (also a fraction of the capacity) and predicts when the
back-off stops being enough.

## 6. Why small batteries must be made usable

Battery costs fall [schmidt2017future, kittner2017energy, ziegler2021reexamining, schmidt2019projecting], but
capacity remains the dominant investment, and life-cycle costs [zakeri2015electrical] and ageing
[xu2018factoring, wu2022optimal] grow with it. Sizing studies find diminishing returns of capacity
[weniger2014sizing, quoilin2016quantifying, mulleriyawage2020optimally, linssen2017techno, laksahapsoro2025optimisation,
secchi2021multi, yang2018bess, zhang2022gridconnected], and Makibar et al. [makibar2017relation] show that a battery
can be about 30 % of the worst-case size because large fluctuations are rare. System studies reach the same conclusion
for the grid [zerrahn2018economics, dowling2020role, sepulveda2021design].

**Evidence from this study.** On the development period (UA-MPC, nominal forecast error), a 36-Wh battery saved
0.259 € against grid-only operation, 71 % of the 0.364 € saved by a 144-Wh battery with a quarter of the capacity.
The first 36 Wh earned 7.2 m€ per Wh, the next 36 Wh 1.6 m€/Wh and the last 72 Wh 0.65 m€/Wh
(`results/capacity_economics/capacity_economics.csv`). The small battery is where the constant back-off tuned for
72 Wh fails: at 36 Wh it violated the band by 3.9 pp·h (19.1 pp·h with doubled forecast error), the UA margin by
0.69 pp·h (1.25 pp·h), without re-tuning. A smaller battery has a larger r_E for the same forecast; making it safe is
exactly what the self-adjusting margin does.

## 7. Industrial context

Energy-aware production scheduling and industrial demand response [gahm2016energy, shoreh2016survey,
zhang2016enterprise, golmohamadi2022demand] and energy-flexible manufacturing with variable renewables
[beier2017energy] motivate the production-cell setting.

## 8. Software

The study uses SLSQP [kraft1988software] through SciPy [virtanen2020scipy], GP regression fitted with scikit-learn
[pedregosa2011scikit], a wind power curve following [manwell2009wind], and support-vector regression
[smola2004tutorial] for missing future prices in operation. Open tools for physical PV modelling are available in pvlib
[holmgren2018pvlib].

## 9. Tuning and evaluation

Controller weights are tuned by Bayesian optimisation [jones1998efficient, knowles2006parego, shahriari2016taking,
marco2016automatic, sorourifar2021data] from Latin-hypercube starts [mckay1979comparison]. Chronological splits avoid
leakage [bergmeir2012use, lago2021forecasting]; dependent daily results need block bootstraps [kunsch1989jackknife,
politis1992circular, lahiri2003resampling].
