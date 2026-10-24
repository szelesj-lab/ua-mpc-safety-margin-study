# Experimental protocol

## System and data

- Production cell with PV and wind supply, a 15-min resolution, and a battery of usable capacity E (72 Wh unless
  stated otherwise), degradation cost c_deg = 2·10⁻⁵ €/Wh throughput; SoC band 0.1–0.9.
- Forecasts: GPR mean and standard deviation per source (models trained once, not retrained in this study);
  day-ahead prices from ENTSO-E (HU), weather from Open-Meteo.
- Plants: *physical* (the SoC may leave the band; the excursion is measured) and *BMS* (a battery-management system
  blocks charging or discharging at the band edges; the cost of blocked steps appears as extra grid energy).

## Controllers

| Name | Description |
|---|---|
| `det` | deterministic MPC on the forecast mean |
| `det_bo` | `det` with a constant back-off b from both band edges |
| `ua` | uncertainty-aware MPC: ρ weight on the renewable term (λ) and a chance margin z·σ on the SoC band |
| `ua_rho_only` | `ua` with z = 0 (ablation) |
| `ua_margin_only` | `ua` with λ = 0 (ablation) |
| `oracle` | `det` weights with perfect forecasts (lower bound) |
| `grid_only`, `rule` | no battery; a rule-based battery |

All MPCs: SLSQP, horizon 96 steps (24 h), re-planning every 4 steps (1 h) unless stated otherwise.

## Periods (chronological, no overlap)

| Period | Dates (2026) | Use |
|---|---|---|
| calibration | 06-16 – 07-07 | σ calibration of the GPR |
| tuning | 07-07 – 08-11 | ParEGO weight tuning |
| development | 08-11 – 09-02 (22 days) | selection of the operating point, ablations, all sensitivity maps |
| final test | 09-02 – 10-15 (44 days) | run **once**, after the pre-registration was written |

## Tuning (equal budget)

ParEGO, 30 trials (8 LHS starts), 4 episodes of 2 days from the tuning period, objectives net cost, band violation
and curtailment; the same budget for `det`, `det_bo` and `ua`.

## Pre-registered selection (`results/final_test/preregistration.json`, written 2026-10-23T22:20:34Z)

Per controller, among its tuning Pareto points replayed on the development period (physical plant): the cheapest
point with development violation ≤ 0.5 pp·h; if none, the lowest violation. Secondary threshold 1.0 pp·h reported
for `ua`. Selected: `det` trial 5, `det_bo` trial 13 (b = 0.019), `ua` trial 17 (λ = 2.55, z = 1.53).

## Metrics

- band violation: Σ_k 100·(max(0.1 − SoC_k, 0) + max(SoC_k − 0.9, 0))·Δt in pp·h (physical plant);
- protection steps and extra grid cost (BMS plant);
- net cost: grid cost + wear − value of the final stored energy;
- statistics: paired circular block bootstrap of daily differences, 5-day blocks, B = 10 000.

## Indicators

- r_E: the 95 % quantile of the renewable energy deficit that can build up until the next re-plan, divided by E;
- r_P: the same for power; κσ = std(σ)/mean(σ) over the period.

## Sensitivity experiments (development period only)

- decision map: E ∈ {36, 72, 144} Wh × forecast-error scale ∈ {0.5, 1, 2} × re-planning 4 steps, plus 72 Wh / 1 / 16
  steps; the pre-registered `det_bo` and `ua` points are **not** re-tuned;
- variability: the same cells with σ held at its period mean (κσ = 0) or with its deviation from the mean doubled;
- capacity economics: savings against grid-only per Wh and marginal savings from the decision map.

## Code changes after the final test

`mpc.soc_recovery` (relaxes the band only where it cannot be reached from the current SoC) was added after the final
test, to remove a solver lock-in found on the development period. The final test, the tuning, the development fronts
and ablations and `decision_map/` were run **without** it; `decision_map_recovery/`, `recovery_check/` and
`variability/` with it. `experiments/run_all.sh` sets `SOC_RECOVERY` accordingly.

## Threading

The final-test runs of `det`, `det_bo`, `ua_rho_only`, `grid_only` and `rule` on the physical plant were run with
multi-threaded BLAS, all others single-threaded. One development cell showed 0.45 vs 0.18 pp·h for `det_bo` between
the two settings; `run_all.sh` uses single-threaded BLAS throughout.
