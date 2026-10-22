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
| C — Convergence Proof & Journal Theory | 🟢 Done | 4–5 hrs |
| D — API Hardening & Batch Runner Upgrade | 🟢 Done | 2–3 hrs |

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

**Status: 🟢 Done**

| # | Task | File | Status | Notes |
|---|------|------|--------|-------|
| C1 | Write Lemma + Theorem (convergence proof) | `docs/paper/theory_draft.md` | 🟢 | Monotone convergence argument; finite improvement property |
| C2 | Formal definition of strategy space S_i | `docs/paper/theory_draft.md` | 🟢 | Drop-set × Add-set per agent; bounded memory |M_i| ≤ 100 |
| C3 | Proof of Pure-Strategy Nash Equilibrium existence | `docs/paper/theory_draft.md` | 🟢 | Exact potential game — Lemma 4.1 + Theorem 5.1 |
| C4 | δ term theoretical bound (throughput gain) | `docs/paper/theory_draft.md` | 🟢 | Upper bound ΔU_i^δ < δ; Theorem 7.1 with logistic throughput model |
| C5 | Write Game Theory journal section | `docs/paper/journal_section_gametheory.md` | 🟢 | LaTeX-convertible markdown; IEEE Transactions style |
| C6 | Write Experimental Analysis journal section | `docs/paper/journal_section_experiments.md` | 🟢 | All 4 Phase B figures referenced; comparative baseline table |

### Definition of Done — Phase C

- [x] `theory_draft.md` has Lemma + Theorem with full proof sketch
- [x] `journal_section_gametheory.md` written (LaTeX-ready)
- [x] `journal_section_experiments.md` written with figure references
- [x] Member 3 notified to drop into LaTeX template

---

## Phase D — API Hardening & Batch Runner Upgrade

> **Goal:** Harden Flask API for Phase 4 demo. Add δ CLI flag to `main.py`.

**Status: 🟢 Done**

> ⚠️ **HANDOFF CONTEXT (for next agent):** If this session was interrupted, read this section carefully before touching any code.
> - Branch: `feature/algorithmic-proofs-ablation` (already checked out)
> - All changes go to `app.py` (root) and `main.py` (root)
> - Do NOT touch `src/network/`, `frontend/`, or `docs/paper/`
> - After all tasks done: `git add app.py main.py docs/MEMBER2_PROGRESS_TRACKER.md && git commit -m "feat(phase-d): API hardening & batch runner upgrade"`
> - Then push: `git push origin feature/algorithmic-proofs-ablation`

### Exact Code Locations in app.py

| Location | Line # | What to do |
|----------|--------|------------|
| `runtime_config` dict | ~L81–92 | Add `'delta': DEFAULT_DELTA_WEIGHT` key |
| `from src.config import ...` | ~L38–49 | Add `DELTA_WEIGHT as DEFAULT_DELTA_WEIGHT` to import |
| `GET /api/config` | ~L222–235 | Add `'delta': runtime_config['delta']` to response |
| `POST /api/config` | ~L238–285 | Add delta clamp block; add 400 validation for all bad floats |
| `_execute_parallel_step()` | ~L54–67 | Pass `delta=runtime_config['delta']` to `agent.decide()` |
| New endpoint | after L723 | Add `GET /api/results/export` returning CSV of history |

### Exact Code Plan for main.py

- Import `argparse` and `DELTA_WEIGHT` at top
- Add `argparse.ArgumentParser` with flags: `--delta` (float, default=DELTA_WEIGHT), `--nodes` (int), `--iterations` (int), `--seed` (int)
- Pass `args.delta` into `run_simulation()` — need to update `run_simulation()` signature in `simulation.py` to accept optional `delta` override (just pass through to `DELTA_WEIGHT` in config temporarily, or use monkeypatch approach)
- Simplest approach: patch `src.config.DELTA_WEIGHT` at runtime before calling `run_simulation()`

| # | Task | File | Status | Notes |
|---|------|------|--------|-------|
| D1 | Add `delta` to `runtime_config` + GET `/api/config` response | `app.py` | 🟢 | Imported `DELTA_WEIGHT as DEFAULT_DELTA_WEIGHT`; added to dict; exposed in GET |
| D2 | Add `delta` to POST `/api/config` with clamp `[0.0, 2.0]`; add 400 validation for all params | `app.py` | 🟢 | Full `try/except ValueError` blocks; errors list; returns 400 with `{errors:[...]}` |
| D3 | Pass `delta` from `runtime_config` to `_execute_parallel_step` → `agent.decide()` | `app.py` | 🟢 | Added `delta=runtime_config['delta']` to `_execute_parallel_step` |
| D4 | Add `GET /api/results/export` endpoint (CSV download) | `app.py` | 🟢 | `flask.Response` with `text/csv`; columns: `step,apl,clustering_coefficient`; 400 if no data |
| D5 | Add `--delta`, `--nodes`, `--iterations`, `--seed`, `--no-plot` CLI flags to `main.py` | `main.py` | 🟢 | `argparse`; runtime-patches `src.config` before `run_simulation()`; fully backward-compatible |
| D6 | Update progress tracker + commit | `docs/MEMBER2_PROGRESS_TRACKER.md` | 🟢 | Done in this step |

### Definition of Done — Phase D

- [x] All Flask endpoints return correct HTTP codes (400 on bad input, 200/success on valid)
- [x] `GET /api/config` returns `delta` field
- [x] `POST /api/config` with `{"delta": -5}` returns HTTP 400
- [x] `GET /api/results/export` returns valid CSV with `step,apl,clustering` columns
- [x] `python main.py --delta 0.5` runs without error
- [x] `python main.py --nodes 200 --iterations 10 --seed 42` runs without error
- [x] Member 3 notified of new `delta` field in `/api/config`

---

## 📝 Execution Log

| Date | Phase | What was done |
|------|-------|--------------|
| 2025-01 | Phase A | Added `DELTA_WEIGHT=0.3` to config; extended `_jit_calculate_utility` with δ·throughput; removed `multiprocessing.ProcessPoolExecutor` from simulation loop (sequential, crash-free); deleted `test_perf.py`; all smoke tests passed |
| 2025-01 | Phase B | Built `tests/ablation_runner.py` with multi-seed single-variable sweeps across α, β, γ, δ; implemented churn-free `run_simulation_parameterized()` in `simulation.py`; added default args to `_jit_calculate_utility` for Member 1 backward compatibility; generated vector publication figures (PDF+PNG) in `results/figures/` (Fig 1: APL vs δ, Fig 2: CC vs γ, Fig 3: Hops vs α, Fig 4: Throughput vs δ); populated `docs/ABLATION_RESULTS.md` with mean ± std tables and research findings |
| 2026-10 | Phase C | Created `docs/paper/` directory; wrote `theory_draft.md` with formal potential game proof (Lemma 4.1), Finite Convergence Theorem (5.1), Core-Periphery Corollary (6.1), and δ-term upper bound Theorem (7.1); wrote `journal_section_gametheory.md` (IEEE Transactions style, LaTeX-ready) covering PSNE existence via exact potential game, OODA convergence dynamics, and defector exclusion proposition; wrote `journal_section_experiments.md` referencing all 4 Phase B figures with full ablation tables, comparative baseline analysis, and discussion; committed all to `feature/algorithmic-proofs-ablation` |
| 2026-10 | Phase D | Hardened `app.py`: added `DELTA_WEIGHT` to `runtime_config` + exposed in `GET /api/config`; full input validation with `try/except` on all 10 params returning `HTTP 400` with error list on bad input; wired `delta=runtime_config['delta']` into `_execute_parallel_step` so live simulation uses the slider value; added `GET /api/results/export` endpoint returning `text/csv` with `step,apl,clustering_coefficient` columns (400 if no data). Upgraded `main.py` with `argparse` CLI (`--delta`, `--nodes`, `--iterations`, `--seed`, `--no-plot`) via runtime config patching — fully backward-compatible; printed delta in summary output |

---

## 🔗 Cross-References

- Full team roadmap: `docs/PHASE4_AND_JOURNAL_ROADMAP.md`
- Ablation results & figures: `docs/ABLATION_RESULTS.md`
- Walkthrough & Theory: `docs/walkthrough_and_theory.md`
- Assessment Report: `docs/assessment_report.md`
- Defense Q&A: `docs/defense_qna_master.md`
