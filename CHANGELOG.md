# Changelog

Notable changes to extractlab, grouped by backlog phase — see `docs/BACKLOG.md` for the full item list and
`docs/PRD.md` §4 for the gate each phase must close. Dates are commit dates (`git log`).

An entry marked **Verified:** closes or partially closes a gate, with the actual evidence behind it — not just
"tests pass." See `docs/PROCESS.md` for why a unit-test pass alone isn't trusted here before replaying against
real recorded data.

## [Unreleased]

### Mango-leaf NADES study (separate from the water–oil rig)

- **2026-11-24** — Added the working protocol for the β-alanine / citric acid monohydrate /
  water trial at **1:1 molar, 20 wt % total water** (the Design-Expert centre level), plus
  `nades_recipe.py`, which computes every mass in that document so the prose and the
  arithmetic cannot diverge. Scope, in the doc's §1: this is bench chemistry upstream of the
  rig, **not** part of the automated water–oil pipeline — no existing module was touched.
  - **Corrected three errors in the earlier, ad-hoc recipe drafts:** the making-the-solvent
    step had **no temperature and no time** (published synthesis for exactly this solvent is
    70 ± 2 °C, 120 min); the trial used 20 mL solvent per 0.50 g leaf = 1:40 g/mL where the
    published ratio is 1:60 (30 mL gives it exactly); and a 100 g batch is only ≈83 mL, short
    of the 120 mL needed for 3 samples + 1 blank.
  - **Two arithmetic errors of mine, caught by the tests rather than by review:** a claim
    that 20 wt % water is 1:1:2.46 molar (it is 1:1:3.90), and a claim that the monohydrate
    and anhydrous routes give different water wt % (both give 16.1 wt % — the hydrate changes
    only what you weigh, not the solvent). Both are now regression-tested, and the doc says so
    out loud rather than quietly deleting the wrong numbers.
  - **Verified:** `python3 -m pytest -q` — **75 passed** (57 new: 48 in
    `test_nades_recipe.py`, 9 in `test_docs_consistency.py`; plus the 18 pre-existing). The
    doc-consistency tests were themselves checked by deliberately corrupting a ladder row in
    `docs/MANGO_LEAF_TRIAL.md` and confirming 3 of them fail, then restoring it. The module's
    100 g / 20 wt % result reproduces the stated weighing (25.34 / 59.78 / 14.88 g) to
    0.01 g and both invariants to 1e-6.
<<<<<<< HEAD
  - **2026-11-24** — Typeset the same protocol to **`docs/MANGO_LEAF_TRIAL.pdf`**
=======
  - **2026-11-24** — Added **`docs/STEP_GUIDE.md`** / `.pdf`: a 21-step, start-to-finish bench
  walkthrough answering "guide me step by step, everything from scratch". Written for someone who
  is confused, so it is deliberately different in shape from the other two documents: **no choices,
  no reasoning to follow, one linear path**. Every step has the same four parts - what to do, what
  you should see, what to do if you do not, and why it matters - plus a tick-box record sheet at the
  end and a three-line explanation of where the numbers come from.
- **2026-11-24** — Added **`docs/TRIAL_RUNSHEET.md`** / `.pdf` ("How I would run this trial"):
  my own 3-day execution order, written as decisions rather than a restatement of the protocol.
  Two deliberate departures from the protocol, both argued in the document: make a **20 g scout
  batch first** (5.07 / 11.96 / 2.98 g) to prove the solvent forms at 20 wt % before committing
  240 g, and **start the leaf moisture test first thing** because it is the divisor in the final
  yield. It also ranks where the plan is most likely to fail - the honest first answer being
  that the static 3 h step may not reach equilibrium, with the triplicate SD as the diagnostic.
- **2026-11-24** — Renderer fixes found by rendering the second document: the footer and PDF
  metadata were **hardcoded to the first document's title**, so the run sheet's every page was
  footed "Mango-leaf NADES trial"; both are now derived from the source's first `h1`. A trailing
  build note also rendered as a one-line orphan page 5 - `<!-- ... -->` blocks are now stripped
  before parsing, and the note is an HTML comment instead of visible text. Run sheet went 5
  pages (with an orphan) -> 4 clean pages.
  **Verified:** both PDFs' text extracted and compared line by line against their Markdown
  (run sheet 134/134 lines, protocol 397/397 minus one line that legitimately continues across a
  page break); both titles correct in metadata; all pages of both rendered and inspected;
  `python3 -m pytest -q` - 75 passed.
- **2026-11-24** — Typeset the same protocol to **`docs/MANGO_LEAF_TRIAL.pdf`**
>>>>>>> bab1b26 (docs: add my own trial run sheet + fix renderer title/footer)
    (12 pages, A4, PDF bookmarks) with a purpose-built renderer, `tools/typeset_protocol.py`,
    because no pandoc / LaTeX / cairo exists in the target environment and there is no root
    to install them (ReportLab + the DejaVu fonts already present). Regenerate with
    `python3 tools/typeset_protocol.py`.
    - The renderer fails loudly rather than dropping content: unknown Markdown constructs
      raise, a table with a blank line inside it raises, and any character outside ASCII is
      checked against the embedded font's cmap first.
    - **Four document bugs were found by rendering it, three of which also broke the Markdown
      on GitHub:** a literal `≪` where "far below" was meant (glyph check caught it); a stray
      pipe that split a 3-cell row of the record-sheet table; an inline note that split that
      table into two; and a stale "66 passed (48 new)" that had drifted from the real 75.
    - **Renderer bugs found by reading the output, not by the build succeeding:** nested
      bold-inside-italic double-escaped into literal `<b>` tags; a code span wrapped across
      two blockquote lines rendered with visible backticks; a numeric-column heuristic
      collapsed a "5 mg" column to one letter per line; and section 10's heading was stranded
      as a widow at the foot of page 11. All fixed and re-checked page by page.
    - **Verified:** all 12 pages rendered to PNG and inspected; PDF text extracted and compared
      against the Markdown line by line (398 substantial lines, all present); bookmarks list all
      12 sections and 24 subsections; `python3 -m pytest -q` — 75 passed; `python3 demo.py` —
      `RESULT: PASS`.
  - **Not verified, and cannot be from here:** the solvent has not been made, no HPLC has
    been run, and the yield is not measured. `ASSUMED_DENSITY_G_ML = 1.20` in
    `nades_recipe.py` is a placeholder — §A6 of the protocol requires measuring it.

### Scope and hardware changes (documentation sync)

- **2026-10-13** — Three real-world changes, confirmed by the advisor/hardware in hand, synced across every doc
  (`README.md`, `CLAUDE.md`, `PRD.md`, `BACKLOG.md`, `docs/developments/*`):
  - **Solvent pair:** water-cyclohexane -> **water-oil, final** (not a rehearsal for cyclohexane) — the advisor
    only required a non-toxic organic solvent, not cyclohexane specifically. Epic P6 (switch to cyclohexane)
    removed entirely from `BACKLOG.md`; the P5-to-P7 numbering gap is intentional.
  - **Vessel:** cylindrical beaker -> **separatory funnel, 125 mL, stopcock physically removed** — the pump now
    draws from a tube entering through the top. `P1-07`'s resolution (no new motion-differencing detector
    needed) still holds, but the reasoning changed: not "switched to a beaker" but "removed the stopcock from
    the funnel." Volume model reverts to frustum/multi-point calibration (a funnel is not a cylinder).
  - **Pump + driver:** MINTLLAB 12V via relay -> **GROTHEN G928, 24V, via an HW-039 (BTS7960) motor driver**
    (PSU: S-50-24, 24V 2A — confirmed matching). `P3-02` done (hardware in hand); the rest of P3 still open.
  **Verified:** `python3 -m pytest -q` (11 passed), `python3 demo.py` (`RESULT: PASS`) — no code touched, this
  was a documentation-only correction pass.

### Phase P1 — Detect and track the interface on real liquids (in progress)

- **2026-10-08** — Translated all documentation to English; added `docs/BACKLOG.md` and `docs/PROCESS.md`; moved
  `PRD.md` / `BACKLOG.md` / `PROCESS.md` into `docs/` (`c991272`, `abb3121`)
  **Verified:** `python3 -m pytest -q` — 11 passed; `python3 demo.py` — `RESULT: PASS` (reorg broke nothing)
- **2026-09-04** — **P1-06** Tested the detector against a real separatory funnel (not the beaker used for the
  drain test) and found it locking onto a metal stopcock instead of the water/oil interface
  **Verified:** direct gradient measurement — stopcock `|grad|` ≈ 13, the real interface never registered as a
  gradient peak at all. Root-caused against Chem-SDI (`docs/PROCESS.md`, second worked example): their
  row-gradient step always runs after an ML segmentation mask, which this project deliberately omits.
- **2026-09-04** — **P1-04** First fix hypothesis for `Tracker` (re-seed gated on confidence) written and
  unit-tested, then invalidated by replaying it against the real drain recording — reverted, not merged
  **Verified (failed):** replay of `records/rec_20260904_115249.csv` — max jump got *worse*, 151 → 194 px
- **2026-09-04** — **P1-03 / P1-05** Extracted `Tracker` into `tracking.py` with spec clauses S1-S6
  (`tests/test_tracking.py`, `1fd938c` RED); fixed it to never re-seed while draining (`7adef09` GREEN)
  **Verified:** replay of the same recording — max jump 151 → **12 px**, jumps over 20 px: 14 → **0**
  (`python3 -m pytest tests/test_tracking.py` — 6 passed)
- **2026-09-04** — **P1-02** First live drain test, 219s, recorded and analyzed — correct trend (interface moved
  104 px, matching the water drained), but spiked up to 151 px on false locks (see P1-04/P1-05 above)
- **2026-09-04** — **P1-01** Black background + a tight ROI → the detector locks the real water/oil interface
  **Verified:** `conf` ≈ 12 against a threshold of 3

Still open in this phase: choosing between narrowing the ROI further vs. a motion-differencing detector
(P1-07), and a fresh live drain to confirm the gate formally (P1-08) — see `docs/BACKLOG.md`.

### Phase P0 — System & algorithm setup (done)

- **2026-09-04** — **P0-06** Watchdog + `run_stream.sh` supervisor (`c9d2a38`) — self-heals a stalled camera
- **2026-09-04** — **P0-04 / P0-05** In-browser drain recording, CSV browse page, `boundary_y_smooth`
  (median-of-9 + jump rejection) (`a1fd81c`, `28aea1c`)
- **2026-08-29** — **P0-01 / P0-02 / P0-03 / P0-07** Initial commit: classical-CV LLE vision pipeline
  (`a727b30`) — `boundary_detection`, `turbidity_dct`, `volume_model`, `synthetic_data`, `demo.py`
  (`RESULT: PASS`), `realtime_stream.py` live view, git init + push to GitHub (`Cherrpxp/extractlab`)
  **Verified:** `python3 demo.py` — `RESULT: PASS` against synthetic data
