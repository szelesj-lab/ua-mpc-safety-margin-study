#!/bin/bash
# Re-run the whole study. Each stage is resumable: finished runs in results/*/steps are kept.
# Requirements: the code repository (KAIROS_ROOT) at the commit given in README.md, with
# patches/kairos-resume-and-soc-recovery.patch applied, its Python environment and its data/.
# Results are written to $STUDY_RESULTS (default: ../results).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
export KAIROS_ROOT="${KAIROS_ROOT:-$HERE/../../uncertainty-aware-mpc}"
export STUDY_RESULTS="${STUDY_RESULTS:-$HERE/../results}"
# single-threaded BLAS: results do not depend on the thread count (see docs/protocol.md, threading)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$KAIROS_ROOT"

# Stages 1-4 ran before mpc.soc_recovery was added to the code: reproduce them with it switched off.
export SOC_RECOVERY=0

# 1. tuning period: ParEGO, 30 trials, 4 x 2-day episodes, E = 72 Wh, c_deg = 2e-5
for c in det det_bo ua; do
  python src/tune_mpc.py --controller $c --trials 30 --episodes 4 --episode-days 2 \
         --set SoC.E_capacity=72 --set degradation.c_deg=2e-5 --set mpc.soc_recovery=false --resume
done
mkdir -p "$STUDY_RESULTS/tuning"; cp results/tuning/{det,det_bo,ua}_{pareto,best}.json results/tuning/{det,det_bo,ua}_trials.csv "$STUDY_RESULTS/tuning/"

# 2. development period: Pareto fronts and ablations
python "$HERE/front_dev.py"
python "$HERE/ablation.py" && python "$HERE/ablation_stats.py"

# 3. solver check and pre-registration (written once, never overwritten)
python "$HERE/stages.py" solver
python "$HERE/stages.py" prereg

# 4. final test (run once; replay.py --final logs every run)
python "$HERE/stages.py" final
python "$HERE/stages.py" map            # decision map without recovery (decision_map/)

# 5. with SoC recovery (the default of the patched code): decision map, recovery check, variability, capacity economics
export SOC_RECOVERY=1
python "$HERE/stages.py" map_recovery
python "$HERE/stages.py" dev_recovery
python "$HERE/stages.py" variability
python "$HERE/variability_stats.py"
python "$HERE/capacity_economics.py"

# 6. figures and manuscript numbers
python "$HERE/figures.py"
python "$HERE/../manuscript/scripts/make_numbers.py"
python "$HERE/../manuscript/scripts/fig_day.py"
python "$HERE/../manuscript/scripts/fig_var_cap.py"
cp "$STUDY_RESULTS"/figures/fig[1-4]*.pdf "$HERE/../manuscript/figures/"
echo "done; compile with: cd manuscript && latexmk -pdf manuscript"
