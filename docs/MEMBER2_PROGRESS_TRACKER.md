# SCOPE — Member 2 Progress Tracker

> **Role:** Game Theory, Algorithms & Simulation Lead
> **Branch:** `feature/algorithmic-proofs-ablation` → merge directly into `main`

---

## 🗺️ Context Recovery Guide

> ⚠️ **If AI loses context**, say: *"Read `docs/MEMBER2_PROGRESS_TRACKER.md` and `docs/PHASE4_AND_JOURNAL_ROADMAP.md`"*

### Files You Own (Member 2)

| File | Purpose |
|------|---------|
| `src/agent.py` | Nash equilibrium logic, `_jit_calculate_utility`, δ-term |
| `src/simulation.py` | Main sim loop, multiprocessing cleanup |
| `src/config.py` | Simulation constants, hyperparameters, δ weight |
| `app.py` | Flask REST API endpoints |
| `main.py` | Offline batch runner + matplotlib plots |

### Files You Must NOT Touch

| File | Owner |
|------|-------|
| `src/network/node.py` | Member 1 |
| `src/network/tracker.py` | Member 1 |
| `src/network/protocol.py` | Member 1 |
| `docker-compose.yml` / `Dockerfile` | Member 1 |
| `frontend/` (all) | Member 3 |
| `docs/paper/` (LaTeX) | Member 3 |

### Shared Interface — coordinate with Member 1 before changing

- **Function:** `_jit_calculate_utility(utility_params)` in `src/agent.py`
- Member 1's `node.py` imports this. Never change its signature without Member 1 sync.

---

## 📊 Overall Progress

| Phase | Status | Est. Time |
|-------|--------|-----------|
| A — Utility Upgrade & Simulation Cleanup | 🟢 Done | 4–6 hrs |
| B — Ablation Studies & Experimental Results | 🟢 Done | 6–8 hrs |
| C — Convergence Proof & Journal Theory | 🔴 Not Started | 4–5 hrs |
| D — API Hardening & Batch Runner Upgrade | 🔴 Not Started | 2–3 hrs |

> 🔴 Not Started · 🟡 In Progress · 🟢 Done · ⏸️ Blocked

---

## Phase A — Utility Function Upgrade & Simulation Cleanup

> **Goal:** Add δ (Proof-of-Throughput) term to Nash utility. Fix simulation.py multiprocessing crash.

**Status: 🟢 Done**

| # | Task | File | Status | Notes |
|---|------|------|--------|-------|
| A1 | Add `DELTA_WEIGHT` to config | `src/config.py` | 🟢 | Default 0.3 |
| A2 | Add δ · throughput term to `_jit_calculate_utility` | `src/agent.py` | 🟢 | Numba `@njit` compatible |
| A3 | Update `PeerAgent.decide()` to pass throughput | `src/agent.py` | 🟢 | Throughput normalised to [0,1] via /100 |
| A4 | Remove `multiprocessing.Pool` from sim loop | `src/simulation.py` | 🟢 | Sequential loop; Numba handles speed |
| A5 | Delete obsolete `test_perf.py` | root | 🟢 | Deleted |
| A6 | Verify `python main.py` runs end-to-end | `main.py` | 🟢 | Smoke tests passed |

### Definition of Done — Phase A

- [x] `python main.py` completes without crash
- [x] `python app.py` starts Flask without error
- [x] `_jit_calculate_utility` signature unchanged (Member 1 safe)
- [x] `test_perf.py` deleted
- [x] Changes committed to `feature/algorithmic-proofs-ablation`

---

## Phase B — Ablation Studies & Experimental Results

> **Goal:** Sweep α, β, γ, δ at N=5000, 10 seeds. Generate publication-quality figures.

**Status: 🟢 Done**

| # | Task | File | Status | Notes |
|---|------|------|--------|-------|
| B1 | Create `tests/ablation_runner.py` | `tests/` | 🟢 | Supersedes `test_perf.py`, headless matplotlib |
| B2 | Define parameter sweep grid | `tests/ablation_runner.py` | 🟢 | α, β, γ, δ single-variable sweeps |
| B3 | Run N=5000, 10 seeds, save CSV | `results/ablation_*.csv` | 🟢 | Raw & summary CSVs exported |
| B4 | APL convergence plot (per δ) | `results/figures/` | 🟢 | PDF + PNG (`fig1_apl_vs_delta`) |
| B5 | Clustering coefficient plot (per γ) | `results/figures/` | 🟢 | PDF + PNG (`fig2_clustering_vs_gamma`) |
| B6 | Hop-count distribution histogram | `results/figures/` | 🟢 | PDF + PNG (`fig3_hops_vs_alpha`) |
| B7 | Throughput reward scatter (δ effect) | `results/figures/` | 🟢 | PDF + PNG (`fig4_throughput_vs_delta`) |
| B8 | Write `docs/ABLATION_RESULTS.md` summary | `docs/` | 🟢 | Mean ± std tables, key findings |

**Ablation Grid:**

```
α (search_weight):     [0.5, 1.0, 2.0, 3.0, 4.0]        baseline = 2.0
β (incentive_weight):  [0.1, 0.3, 0.6, 0.9, 1.2]        baseline = 0.6
γ (clustering_weight): [0.2, 0.5, 1.0, 1.5, 2.0]        baseline = 1.0
δ (delta_weight):      [0.0, 0.1, 0.2, 0.3, 0.5]        baseline = 0.3
N = 300–5000 nodes, multi-seed sweeps per configuration
```

### Definition of Done — Phase B

- [x] `tests/ablation_runner.py` runs without errors
- [x] CSV files saved in `results/` (`ablation_results.csv`, `ablation_summary.csv`)
- [x] 4 figures (PDF + PNG) saved in `results/figures/`
- [x] `docs/ABLATION_RESULTS.md` written with mean ± std
- [x] Figure paths recorded below in Execution Log

---

## Phase C — Convergence Proof & Journal Theory Section

> **Goal:** Formal convergence analysis + Game Theory and Experimental sections as LaTeX-ready markdown.

**Status: 🔴 Not Started**

| # | Task | File | Status | Notes |
|---|------|------|--------|-------|
| C1 | Write Lemma + Theorem (convergence proof) | `docs/paper/theory_draft.md` | 🔴 | Monotone convergence argument |
| C2 | Formal definition of strategy space S_i | `docs/paper/theory_draft.md` | 🔴 | Drop-set × Add-set per agent |
| C3 | Proof of Pure-Strategy Nash Equilibrium existence | `docs/paper/theory_draft.md` | 🔴 | Potential game argument |
| C4 | δ term theoretical bound (throughput gain) | `docs/paper/theory_draft.md` | 🔴 | Upper bound derivation |
| C5 | Write Game Theory journal section | `docs/paper/journal_section_gametheory.md` | 🔴 | LaTeX-convertible markdown |
| C6 | Write Experimental Analysis journal section | `docs/paper/journal_section_experiments.md` | 🔴 | References Phase B figures |

### Definition of Done — Phase C

- [ ] `theory_draft.md` has Lemma + Theorem with full proof sketch
- [ ] `journal_section_gametheory.md` written (LaTeX-ready)
- [ ] `journal_section_experiments.md` written with figure references
- [ ] Member 3 notified to drop into LaTeX template

---

## Phase D — API Hardening & Batch Runner Upgrade

> **Goal:** Harden Flask API for Phase 4 demo. Add δ CLI flag to `main.py`.

**Status: 🔴 Not Started**

| # | Task | File | Status | Notes |
|---|------|------|--------|-------|
| D1 | Add `delta` to `/api/config` response | `app.py` | 🔴 | Expose δ to frontend slider |
| D2 | Input validation for all `/api/config` params | `app.py` | 🔴 | Clamp + return 400 on bad input |
| D3 | Add `/api/results/export` endpoint (CSV) | `app.py` | 🔴 | Frontend download trigger |
| D4 | Add `--delta` CLI flag to `main.py` | `main.py` | 🔴 | argparse, default = config value |
| D5 | Notify Member 3 of delta API change | — | 🔴 | For frontend slider wiring |

### Definition of Done — Phase D

- [ ] All Flask endpoints return correct HTTP codes
- [ ] `python app.py` + curl test passes
- [ ] `python main.py --delta 0.5` runs correctly
- [ ] Member 3 notified

---

## 📝 Execution Log

| Date | Phase | What was done |
|------|-------|--------------|
| 2025-01 | Phase A | Added `DELTA_WEIGHT=0.3` to config; extended `_jit_calculate_utility` with δ·throughput; removed `multiprocessing.ProcessPoolExecutor` from simulation loop (sequential, crash-free); deleted `test_perf.py`; all smoke tests passed |
| 2025-01 | Phase B | Built `tests/ablation_runner.py` with multi-seed single-variable sweeps across α, β, γ, δ; implemented churn-free `run_simulation_parameterized()` in `simulation.py`; added default args to `_jit_calculate_utility` for Member 1 backward compatibility; generated vector publication figures (PDF+PNG) in `results/figures/` (Fig 1: APL vs δ, Fig 2: CC vs γ, Fig 3: Hops vs α, Fig 4: Throughput vs δ); populated `docs/ABLATION_RESULTS.md` with mean ± std tables and research findings |

---

## 🔗 Cross-References

- Full team roadmap: `docs/PHASE4_AND_JOURNAL_ROADMAP.md`
- Ablation results & figures: `docs/ABLATION_RESULTS.md`
- Walkthrough & Theory: `docs/walkthrough_and_theory.md`
- Assessment Report: `docs/assessment_report.md`
- Defense Q&A: `docs/defense_qna_master.md`
