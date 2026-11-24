# Mango-leaf NADES trial — complete working protocol

**β-alanine : citric acid monohydrate : water, 1:1 molar, 20 wt % water**
Prepared 2026-11-24 · supersedes the earlier, fragmentary recipe drafts · companion code:
[`nades_recipe.py`](../nades_recipe.py) · tests: [`tests/test_nades_recipe.py`](../tests/test_nades_recipe.py)

> **Every mass, ratio and conversion in this document is computed by `nades_recipe.py` and
> checked by 48 automated tests, not typed by hand.** Where an earlier draft of this
> protocol was wrong, the error and the correction are called out in `⚠` boxes, because
> knowing *why* a number changed is what stops it drifting back.

---

## 0. Read this first — the three things that were causing the confusion

Your message contained three separate documents' worth of advice stitched together, and
they disagreed in small ways that are impossible to spot by eye. Here is the whole
confusion, resolved:

| # | The confusion | The resolution |
|---|---|---|
| 1 | "Is the recipe right?" | **Yes.** 25.34 g β-alanine + 59.78 g citric acid monohydrate + 14.88 g water = 100.00 g at exactly 20.00 wt % total water and 1.000:1 molar. Verified to three decimal places. |
| 2 | "Does 20 % water match the published study?" | **Not exactly — and that is fine, but say so.** The published β-Ala:CA:H₂O is **1:1:3 molar = 16.1 wt % water**. Your 20 wt % point is **1:1:3.9 molar**. Close cousins, not the same solvent. Both descriptors must be reported. |
| 3 | "What do I actually *do*?" | The earlier recipe was missing **the temperature (70 °C)** and **the time (≈2 h of stirring)** for making the solvent. Those two omissions are why a NADES "doesn't work" for most first-timers: they stir for 20 minutes at 40 °C, get a gritty paste, and conclude the recipe is wrong. |

Three further corrections, all of which matter for the result you get:

| What the earlier draft said | What this protocol does | Why |
|---|---|---|
| 20 mL solvent per 0.50 g leaf | **30 mL** per 0.50 g leaf | 20 mL gives 1:40 g/mL; the published extraction is **1:60**. 30 mL reproduces it exactly, for free. |
| one sample + one blank | **three samples + one blank** | One sample gives you a number with no error bar. A report cannot use it. Same solvent batch, four containers. |
| make a 100 g batch | make a **~240 g / 200 mL** batch | 100 g is only ≈83 mL — less than the 120 mL you need for 3 × 30 mL + 1 × 30 mL. You would run out halfway. |

Nothing here overrides your supervisor, your lab's risk assessment, or your HPLC
technician's method. Where this document and a person in the building disagree, the person
wins.

---

## 1. Where this work actually sits in your project (read even if you skip the rest)

This is the part no other answer can give you, because it needs your repo.

Your repository is **`extractlab` — an automated *water–oil* liquid–liquid separation rig**:
a Pi 5 + Camera Module 3 watches a 125 mL pear-shaped separatory funnel, finds the interface
by row-wise brightness gradient, checks turbidity by DCT, and (once P3/P4 are done) drives a
24 V peristaltic pump through an HW-039 motor driver to stop at a target volume
([`docs/PRD.md`](PRD.md), [`CLAUDE.md`](../CLAUDE.md)).

`grep -rn "nades\|mango\|hplc\|eutectic"` across the repo returns **nothing**. The mango-leaf
NADES work is not in your project's documentation at all. That is almost certainly the root
of the confusion: you have a **chemistry experiment** and a **computer-vision project**, and
nothing in either one says how they connect. So here is the honest map:

```
        ┌──────────────────────────────────────────────┐
        │  This document: make the NADES, extract,     │   ← chemistry bench work
        │  hand a clean sample to the HPLC lab         │      (weeks 1–3)
        └───────────────────┬──────────────────────────┘
                            │ gives you: mangiferin mg/g DW
                            │ and a viscous, coloured liquid
                            ▼
        ┌──────────────────────────────────────────────┐
        │  extractlab: interface detection + pumping   │   ← the repo (P1–P5)
        └──────────────────────────────────────────────┘
```

Two possible relationships, and **you must decide which one you are in before you spend
three weeks on this**:

1. **The NADES is the *sample*, the rig is the *machine*.** You extract mango leaves with
   NADES, then use the rig to separate/purify the extract (e.g. NADES from a water wash, or a
   two-phase system). In this case this protocol is upstream of the repo and the two are
   complementary.
2. **The NADES *replaces* water–oil as the liquid pair the rig detects.** In this case you
   are pointing a camera at a **2.35 Pa·s (2350 cP) light-brown liquid** instead of clear
   water and yellow oil. That is a genuinely harder imaging problem: higher viscosity slows
   settling, colour reduces the brightness gradient the detector keys on, and a dark extract
   can flatten `conf` below your gate. Your `boundary_detection.py` has never seen a liquid
   like this.

**Either way, the blank from this trial is valuable to the rig**, and this is a concrete,
immediate benefit you should note: *Solvent blank* is the NADES alone, run through the same
45 °C / 3 h / filter. It is exactly what you need to check whether the detector can hold an
interface in this solvent before any leaf material is in it. Log it as a frame series and
compare `conf` and the gradient profile against your `records/` water–oil runs.

If your supervisor's intent is option 2, say so in your progress report explicitly — it
changes the risk profile of the CV work, and it is a good, honest point to raise **before**
the 2026-11-27 progress-report deadline, not after.

### Why "ask another AI / compare another repo" does not help by itself

Three reasons, stated plainly because you asked:

- **No other repo has your chemistry.** A generic NADES repo gives you a ratio table and no
  batch arithmetic. Yours now has batch arithmetic that is *tested*.
- **The arithmetic is where the errors live.** This protocol's numbers were computed and
  asserted in `tests/test_nades_recipe.py`, and building it **caught two errors of mine** —
  a claimed "1:1:2.46 molar" that is really 1:1:3.9, and a claim that the monohydrate and
  anhydrous routes differ in water wt % when they do not (both are 16.1 wt %). Those are
  exactly the mistakes a fluent paragraph hides and a test does not.
- **What only you can supply** is: your supervisor's intent, the Design-Expert design you
  actually built, and your HPLC lab's method. This document is structured so you can slot
  those three in without rewriting anything.

---

## 2. Understand your own solvent in 90 seconds

A **NADES** (natural deep eutectic solvent) is a mixture whose melting point is far below
that of its parts, because the two solids hydrogen-bond to each other instead of to
themselves. Here:

- **β-alanine** — the hydrogen-bond **donor/acceptor amine + acid** (HBA in the paper's terms)
- **citric acid** — the hydrogen-bond **donor**, three COOH and one OH
- **water** — not a diluent. At 10–30 wt % it is a **third component** that breaks up the
  lattice and cuts viscosity by an order of magnitude. This is why your 20 wt % point still
  behaves as a eutectic and not as "citric acid dissolved in water".

**The one number to remember: citric acid monohydrate is 8.58 wt % water already.**
210.14 g/mol of solid contains 18.015 g/mol of water. So a "1:1:3 molar" recipe written in
terms of the *monohydrate* needs only **2 more moles** of pipetted water, not 3. Count it
twice and you get too-wet solvent; forget it and you get 24 wt % when you wanted 20 wt %.

### The two ways to describe this solvent, and the converter

| Description | β-alanine | Citric acid·H₂O | Added water | Total water |
|---|---:|---:|---:|---:|
| **Your recipe: 1:1 molar, 20 wt % water** | 25.34 g | 59.78 g | 14.88 g | 20.00 g = **20.0 wt %** = **1:1:3.90 molar** |
| **Published: Ojeda 2023 DES-2, 1:1:3 molar** | 1 mol (89.09 g) | 1 mol (210.14 g) | 2 mol (36.03 g) | 3 mol (54.05 g) = **16.1 wt %** = **1:1:3.00 molar** |

> **⚠ Correction to the earlier framing.** A previous draft implied these were more or less
> unrelated solvents ("the published study used a 1:1:3 formulation, not this exact trial").
> That undersells the connection and is numerically wrong in a way a reviewer would catch:
> 20 wt % water *is* 3.9 mol water per mol acid, so you are about **one mole of water more
> hydrating** than the published DES-2 — a small, defensible step, not a different recipe
> family. Say *that* in your report; it is both more accurate and a better story ("we moved
> modestly wetter than the literature point, which lowers viscosity and is why we expect it
> to behave in the rig").

Get the wt % → molar converter from the module rather than a spreadsheet that will drift:

```bash
python3 nades_recipe.py                    # the ladder + batch sizing, printed
python3 -c "import nades_recipe as n; r=n.for_total_mass(100,20); print(r.molar_ratio_text())"
```

### Water ladder — paste straight into Design-Expert

If 20 wt % is your **centre point**, your design's water factor almost certainly spans
10–30 wt %. These are the actual weighings for each level, 1:1 molar, 100 g total:

| Water (wt %) | β-alanine (g) | Citric acid·H₂O (g) | Added water (g) | Molar ratio | Note |
|---:|---:|---:|---:|---|---|
| 10 | 28.51 | 67.25 | 4.23 | 1:1:1.73 | very viscous; near the crystallisation edge |
| 15 | 26.93 | 63.52 | 9.55 | 1:1:2.75 | ≈ the published DES-2 point (16.1 wt %) |
| **20** | **25.34** | **59.78** | **14.88** | **1:1:3.90** | **your centre point / this trial** |
| 25 | 23.76 | 56.04 | 20.20 | 1:1:5.20 | lower viscosity, faster extraction |
| 30 | 22.18 | 52.31 | 25.52 | 1:1:6.69 | approaching "not really a eutectic" |

Two useful properties of this table: your 10–30 % range **brackets the 16.1 wt % literature
point**, which is a strong justification for the design; and the trend is monotonic in the
right direction (more water → less viscous → better mass transfer), so the design has a real
chance of showing a maximum rather than a flat line.

---

## 3. Part A — Make the solvent

### A0. Safety and setup (do not skip; your supervisor signs this)

- Goggles, nitrile gloves, lab coat. **Citric acid** is an eye/skin irritant, especially as
  fine dust and when warm. **β-alanine** is a non-protein amino acid — low toxicity, but
  weigh it gently; respirable dust is the only real nuisance. Neither is a controlled
  substance.
- **Glass only** for the hot vessel and the stirrer. Warm citric acid solution will attack
  aluminium and will stain/pit some stainless steels. No metal spatulas in the hot mixture.
- **Do not seal** the vessel. Vapour and thermal expansion; a screw cap on a hot jar is a
  small pressure bomb. Loose watch-glass or foil, or a vented cap.
- Water bath set to **70 °C**, thermometer in the bath (not just the dial).
- Balance readable to **0.01 g** is enough for a 240 g batch; 0.001 g is better and is what
  the published method used. Record the *actual* masses, not the targets.

### A1. How big a batch? — make 200 mL, not 100 g

Your four containers need 4 × 30 mL = **120 mL**, plus what stays on the vessel wall, in
the filter, and in the dead volume of whatever you use to dispense. A 100 g batch is only
≈83 mL at an assumed 1.2 g/mL — **short**. Make 200 mL of finished solvent ≈ **240 g**:

| Ingredient | Amount for **200 mL** (≈240 g total) |
|---|---:|
| β-alanine | **60.83 g** |
| Citric acid monohydrate | **143.47 g** |
| Purified water | **35.70 g** (≈35.7 mL) |
| *Total weighed* | *240.0 g* |
| *Water check* | *12.30 g from the hydrate + 35.70 g added = 48.00 g = **20.00 wt %*** |
| *Molar check* | *0.683 mol : 0.683 mol = **1.000*** |

Vessel: 400–600 mL beaker (the mixture foams and climbs the wall while it wets out), on a
**magnetic stirrer** if you have one. If your only option is a glass rod, plan on the long
end of the times below.

> If your supervisor wants a smaller trial, `python3 -c "import nades_recipe as n;
> print(n.for_volume(120).table())"` gives a 120 mL batch — but 200 mL is the sensible
> minimum for 3 + 1 containers.

### A2. Weigh the solids first, water last

1. Weigh **143.47 g citric acid monohydrate** into the beaker. It is fluffy; add it in
   portions, and do not pack it.
2. Add **60.83 g β-alanine** on top. **Record both actual masses.**
3. Mix the two dry powders briefly with a glass rod (this reduces clumping later).

### A3. Add the water in ~5 portions, mixing between

Add the **35.70 g water** in roughly five portions with a few minutes of stirring between
each. You will see the mixture go from wet powder → slush → lumpy paste → a clear,
honey-like liquid. The lumps are normal at this stage; they are undissolved/unmelted solid,
not a mistake. Do not add extra water to "loosen it" — that silently moves you off your
20 wt % design point, and the design is the whole experiment.

### A4. Heat at 70 °C and keep stirring — for up to 2 hours

> **⚠ The omission that wastes the most time.** "Warm it in a water bath and keep mixing
> until it is uniform" does not say *how hot* or *how long*. The published synthesis for
> exactly this solvent (DES-2) is **70 ± 2 °C, constant agitation, 120 min**. Expect
> **60–120 minutes**. If you stop at 20 minutes you will be looking at a gritty paste and
> will wrongly conclude the recipe failed.

- Bath at **70 °C**; keep the beaker in it, covered loosely, stirring continuously.
- Stir slowly enough that you do not whip air in (air bubbles look exactly like
  undissolved solid, and they make the "is it clear?" judgement impossible).
- **Do not exceed 80 °C.** Above that you are inviting citric acid decomposition
  (it starts losing water and forming aconitic acid well below its 175 °C decomposition
  point), which changes both the solvent composition and its UV background in the HPLC.
- Check clarity by drawing a little onto a watch glass and looking through it against a
  white background, not by peering into the beaker.

### A5. Decide: is it uniform? (binary gate, no judgement calls)

| Observation | Verdict |
|---|---|
| Clear, homogeneous, light brown/amber, flows as one liquid when the rod is lifted | **Pass** — go to A6 |
| Any **grittiness** felt on the rod, or visible crystals after cooling | **Stop.** Do not add leaves. Ask your supervisor (see §8, row 1). |
| Two layers, or a skin on the surface, or a solid lump at the bottom | **Stop.** Ask your supervisor. |
| Still lumpy after **2.5 h at 70–80 °C** | **Stop.** Do not "rescue" it with more water. Ask. |

Then cool to room temperature. Note the appearance and colour in your record sheet — you
will want it later to explain any colour in the chromatogram.

### A6. Measure the density — this is a measurement you owe the report

**100 g of solvent is not 100 mL**, and the density is not in the literature for your exact
composition. Measure it, because everything downstream (30 mL aliquots, the "how much did I
make?" question) depends on it:

1. Weigh a dry, stoppered 10 mL or 25 mL graduated cylinder empty. Record.
2. Fill to the mark with **cooled** solvent, carefully, avoiding bubbles. Wipe the outside.
3. Weigh again. `density = (m_filled − m_empty) / volume`. Do it twice.
4. **Record it.** Then update the constant at the top of `nades_recipe.py`
   (`ASSUMED_DENSITY_G_ML`, currently a placeholder 1.20) so the code stops guessing.

> **Practical consequence, and the single best lab tip in this document:** at ~2350 cP this
> liquid takes *minutes* to drain out of a pipette and leaves a film on the wall, so a
> "30 mL" pipetted aliquot can easily be 26 mL in reality. **Weigh the aliquots instead.**
> At an assumed 1.2 g/mL, 30 mL ≈ **36.0 g** — but use *your* measured density:
> `mass = 30 mL × your_density`. Weighing is faster, more accurate, and self-documenting.

---

## 4. Part B — The extraction: three samples + one blank

### B1. The blank, and why it earns its place

The **Solvent blank** is the NADES carried through the entire procedure — same container,
same 45 °C, same 3 h, same filtration — with **no leaf powder**. It does three jobs:

1. **Chromatographic:** tells the HPLC lab whether the solvent itself produces a peak near
   mangiferin's retention time.
2. **Optical:** it is a clean reference liquid for the rig (§1) — what an "interface" looks
   like in this solvent with nothing else in it.
3. **Honesty:** it is what lets you say "the mangiferin we report is from the leaf", which is
   the only claim that survives review.

Good news on job 1: **neither β-alanine nor citric acid absorbs strongly at 254–265 nm**
(no aromatic ring; citric acid's absorbance is below ~230 nm). So the blank *should* be
near-clean at the mangiferin wavelength. That makes it a sharp diagnostic: a large blank
peak at the mangiferin retention time means **carryover, contamination, or column
equilibration trouble**, not solvent interference. Say that in the report — it is a
specific, checkable prediction rather than a vague "the blank checks for interference".

### B2. Replication: three, not one

| Container | Label | Leaf powder | Solvent |
|---|---|---:|---:|
| 1 | `M1 20%W 45C 3h` | 0.50 g | 30 mL (weigh ≈36 g) |
| 2 | `M2 20%W 45C 3h` | 0.50 g | 30 mL (weigh ≈36 g) |
| 3 | `M3 20%W 45C 3h` | 0.50 g | 30 mL (weigh ≈36 g) |
| 4 | `BLANK 20%W 45C 3h` | **none** | 30 mL (weigh ≈36 g) |

Weigh each leaf portion **to 0.001 g if the balance allows**, and record the actual value —
the yield is divided by this number, so a 0.04 g error is an 8 % error on the final result.
Three samples from **one solvent batch** gives you a repeatability estimate; three solvent
batches would be better and is the next step, not this one.

For the first-ever trial you may run **one** sample + blank to shake out the procedure
(§6 has the decision point), but do not put a single-sample yield in the report. Run the
triplicate before the deadline.

### B3. Ratio — use 30 mL, not 20 mL

0.50 g in 30 mL = **1:60 g/mL**, exactly the published solid:liquid ratio. 0.50 g in 20 mL
= 1:40, a 50 % thicker slurry that is harder to wet out, harder to filter, and a different
extraction. You get the literature-matched condition for free by using 30 mL, and 30 mL is
the volume your 200 mL batch was sized for.

### B4. Loading and the 45 °C / 3 h / static step

1. Weigh the leaf powder directly into the container **first**, then add the solvent on top
   and stir briefly *with a glass rod* to wet it out. (Wetting-out matters at 2350 cP: dry
   powder dropped into thick solvent forms a crust that never wets.)
2. Weigh the solvent in — do not pipette (§A6).
3. Cover all four containers **identically** — same lid, same tightness. A loose lid lets
   water evaporate over 3 hours and quietly changes the water wt % of that container only;
   that is a source of between-sample scatter that looks like "extraction variability" and
   is not.
4. Place in the **45 °C** bath, **stationary: no shaking, no stirring, no sonication**, for
   **3 h** from the time the bath is back at temperature. Record start/end times.
5. Check the bath is actually 45 °C at the *end* too — baths drift when a cold beaker goes in.

> **⚠ Be aware of what you are choosing here.** 45 °C static for 3 h is *not* the published
> condition. Ojeda et al. used either **30 min at 25 °C with 800 rpm stirring** or **5 min of
> ultrasound (60 % amplitude)**. Static diffusion is much slower, which is presumably the
> point (you want no agitation), but it means two things: your yield will likely be **lower
> than the literature**, and **3 h may not be enough to reach equilibrium** — in which case
> your triplicate scatter will be driven by time, not by leaf.
>
> Do not change the plan now. Just write this in the report as a stated limitation, and
> treat **"is 3 h enough?"** as the first follow-up experiment: one run with a 6 h arm, or a
> duplicate set pulled at 1 h vs 3 h. That single comparison is more publishable than another
> water level.

### B5. Cool, then separate

1. Cool all four to room temperature before opening (warm extract + air = condensation, and
   a volume you cannot account for).
2. Use your lab's procedure — filtration or centrifugation, **identically for all four**.
   If centrifuging, use the published condition as a starting point: **20 000 × g, 30 min**.
   If filtering, note the filter material and pore size; a cellulose filter can adsorb
   phenolics, so record it.
3. **Keep the four separate** and label the filtrates with the container ID plus the date.
4. Store at **−20 °C**, in the dark if possible (mangiferin is reasonably stable but the
   phenolics are not). Record the storage time before HPLC — it belongs in the report.

---

## 5. Part C — What the HPLC lab needs from you, and what to ask for

You asked for the concrete version of "ask them to clean up the NADES sample appropriately".
Here it is, taken from the published method (Ojeda et al. §2.6) so you are asking for
something specific rather than a favour:

### C1. The cleanup they should do (cite this to them)

> **Dilute the extract 1:4 with distilled water, load onto a 1 g C18 SPE cartridge
> (pre-conditioned per the manufacturer), wash with 4 mL distilled water, then elute the
> retained phenolics with 3 mL methanol containing 0.1 % v/v formic acid.** Inject that
> eluate.

The wash step is the point: β-alanine (very polar, zwitterionic) and citric acid (very polar)
run straight through, while mangiferin — a xanthone C-glucoside — is retained on C18 and comes
off in the methanol. **Do not inject raw NADES**: at 2350 cP it will foul the column, the
citric acid will wreck the peak shape and the pH of the mobile phase front, and the
refractive-index disturbance alone can look like a peak.

Ask them three questions, and write the answers down:
1. *Will you run the SPE cleanup, or should I deliver pre-cleaned eluate?*
2. *What is your calibration range and LOQ for mangiferin, so I know how much to dilute?*
3. *Will you inject my **blank** at the same dilution?* (This is not optional — see B1.)

### C2. Chromatography that is known to work for mangiferin

| Parameter | Value | Source |
|---|---|---|
| Column | C18, e.g. 250 × 4.6 mm, 5 µm (Gemini/Lichrospher/Phenomenex class) | several, consistent |
| Detection | **254 nm** (also reported 258–265 nm) | 254 nm is the most common single choice |
| Mobile phase | MeOH or ACN + acidified water, e.g. MeOH/0.1–0.5 % acetic or formic acid 30:70, or KH₂PO₄ buffer pH 2.5–2.8 : ACN 85:15 | isocratic methods, all C18 |
| Flow / injection / T | 1.0 mL/min, 5–20 µL, 25–40 °C | typical |
| Mangiferin retention | e.g. 19.75 min on Gemini C18, MeOH/water gradient | one validated method |
| Mangiferin UV maxima | ~254–258, ~316, ~366 nm | a DAD spectrum confirms identity |

If their method differs, **use their method** — but insist they run the **reference standard
and the blank** through it so the retention time is anchored.

### C3. Sanity-check the number you get back (this is your real quality control)

You can predict the answer to within a factor of a few, which means you will *know* if the
HPLC result is believable. Mangiferin in mango leaves is **≈1–6 % of dry weight** (reported
0.96–3.00 g/100 g in one multi-variety study; 3.0–6.2 % in a Mekong Delta survey).

For 0.50 g leaf in 30 mL:

| If leaf is… | mangiferin in the leaf | at 100 % recovery, in your 30 mL | after 1:4 dilution (×5) |
|---|---:|---:|---:|
| 1 % DW | 5 mg | 167 µg/mL | 33 µg/mL |
| 2 % DW | 10 mg | 333 µg/mL | 67 µg/mL |
| 4 % DW | 20 mg | 667 µg/mL | 133 µg/mL |

With realistic NADES recovery (say 50–80 %) expect the **diluted** solution to land roughly
**20–110 µg/mL**. Comfortably inside a typical 15–1000 µg/mL calibration range.

**So: if the lab reports <5 µg/mL, suspect the dilution, the SPE recovery, or the extraction
— not the leaf. If they report >500 µg/mL undiluted, you are off the calibration curve and
the number is meaningless.** Expect **lower** than the literature because of B4, and say so
before you have the data, not after.

---

## 6. Part D — Turning the result into a number

### D1. The yield formula

Worked by `nades_recipe.mangiferin_mg_per_g_dw`:

```
yield (mg mangiferin / g dry leaf) = (C_sample − C_blank) × V_extract × DF / 1000 / (m_leaf × (1 − moisture))
```

- **C_sample, C_blank** — µg/mL from the calibration curve, at mangiferin's retention time
- **V_extract** — 30 mL (the volume the leaf was extracted into, not the eluate volume)
- **DF** — dilution factor applied before injection (5 for 1:4, ×2 more for a further 1:1)
- **m_leaf** — the mass you actually weighed
- **moisture** — residual water in the "dried" powder; measure it by drying a 1 g portion at
  105 °C to constant mass and report **per g DW**, as the literature does. Skipping this
  overstates the yield by the moisture percentage, which for a poorly dried powder can be
  10 % or more.

Example, all four containers, blank-subtracted: if C_sample = 70 µg/mL, C_blank = 2 µg/mL,
DF = 5, m = 0.500 g, moisture = 6 %:

```
yield = (70 − 2) × 30 × 5 / 1000 / (0.5 × 0.94) = 10.2 / 0.47 = 21.7 mg/g DW
```

```bash
python3 -c "import nades_recipe as n; print(n.mangiferin_mg_per_g_dw(70,30,5,0.5,6,2))"
```

A **negative** result (blank larger than sample) is not a bug to be clamped to zero — it
means the solvent interferes and the assay needs the SPE cleanup repeated. The function
deliberately returns the negative number so you notice.

### D2. If your lab uses SPE, be careful with DF

If the SPE eluate is what gets injected, then either (a) keep DF as the pre-SPE dilution and
use V_extract = 30 mL, which assumes 100 % SPE recovery — acceptable only if you say so; or
(b) compute the **total mass in the eluate** (`C_eluate × 3 mL`) and divide by the leaf mass,
which requires knowing SPE recovery. **Best practice:** spike one sample with a known amount
of mangiferin standard before SPE and report the recovery. One spike costs an hour and turns
an assumption into a measurement.

### D3. Report these numbers whether or not they look good

| Quantity | Where it comes from |
|---|---|
| mean ± SD mangiferin (mg/g DW), n = 3 | the three samples |
| blank value at mangiferin RT (µg/mL) | the blank — even if zero, say "no peak at RT" |
| solvent density (g/mL) at 25 °C | §A6 |
| actual masses weighed, per container | the record sheet |
| extraction yield as % of the literature value | for context, clearly labelled as a different matrix |

---

## 7. Part E — Record sheets (copy these into your notebook before you start)

**Solvent batch**

| Field | Value |
|---|---|
| Date / analyst / supervisor present | |
| β-alanine actual mass (g) | |
| Citric acid monohydrate actual mass (g) | |
| Water actual mass (g) | |
| Total (g) / water wt % / molar ratio | | ← compute from the *actual* masses, not the targets
| Bath temperature(s) during synthesis | |
| Stirring time to clarity (min) | |
| Appearance, colour, any crystals | |
| Density at 25 °C (g/mL), replicate 1 / 2 | |
| Volume of solvent obtained (mL) | |

**Each container** (one column per container: `M1`, `M2`, `M3`, `BLANK`)

| Field | M1 | M2 | M3 | BLANK |
|---|---|---|---|---|
| Leaf mass (g) | | | | — |
| Solvent mass (g) / volume (mL) | | | | |
| Start time / bath T | | | | |
| End time / bath T | | | | |
| Lid type | | | | |
| Separation (filter/centrifuge, conditions) | | | | |
| Filtrate volume (mL) | | | | |
| Appearance / colour | | | | |
| Storage (°C, until date) | | | | |

**HPLC handover** — sample IDs, dilution, who ran it, date, column, mobile phase, wavelength,
calibration range, blank result.

---

## 8. Troubleshooting — what will actually go wrong

| # | Symptom | Cause | Do this |
|---|---|---|---|
| 1 | Gritty, never clears | Not hot enough / not long enough / water added too fast | Back to 70–80 °C, stir up to 2.5 h total. If still gritty, **stop** — ask supervisor; do not add water |
| 2 | Crystals appear on cooling | Went below the eutectic's stability window (most likely at low water, e.g. 10 wt %) | Warm gently to re-melt and re-check; record it. For the 20 wt % point this should not happen — if it does, it is a real finding |
| 3 | Two layers after 3 h | Water separated out; or the mixture was never homogeneous | Do not proceed. The solvent was not a eutectic |
| 4 | Extract won't filter | 2350 cP + fine leaf powder | Centrifuge (20 000 × g, 30 min) instead; or dilute a *recorded* amount for filtration only, and correct for it |
| 5 | Aliquots come out short | Pipetting a viscous liquid | Weigh instead (§A6) |
| 6 | Colours differ between M1–M3 | Uneven wetting, or lids of different tightness (evaporation) | Note it; it is exactly what the SD is for. Use identical lids next time |
| 7 | Blank shows a big peak at mangiferin RT | Carryover from a previous injection, dirty SPE cartridge, or column equilibration | Have the lab re-run the blank last; check cartridge lot |
| 8 | Yield ≪ literature | Expected — static 45 °C is slower than 30 min stirred or 5 min ultrasound (§B4) | Report as a limitation; next experiment is time/agitation, not more water levels |
| 9 | HPLC says "cannot inject this" | Raw NADES, too viscous, too acidic | Send the SPE eluate (§C1) |

---

## 9. Design-Expert: one honest critique before you run anything

You are building a response-surface design with **water % as a factor and 20 % as the centre
level**, and the centre point is what this trial executes. Three things worth checking in
your plan before you commit bench time:

1. **How many factors, and do you have the runs?** A central composite or Box–Behnken design
   in 3–4 factors needs 15–30 runs, **plus centre-point replicates (typically 5)**. Centre
   points are not a formality — they are how RSM estimates pure error and tests curvature.
   Five centre runs at 30 mL each, plus the rest, is **well over a litre of solvent** and
   many hours of HPLC. Check you and your lab can actually deliver that by the **full-report
   deadline (2027-04-23)**; if not, cut a factor now rather than halfway through.
2. **Screen before you optimise.** If you have four candidate factors (water %, temperature,
   time, solid:liquid ratio), a **Plackett–Burman or fractional factorial screen** first, then
   a 3-factor RSM on the ones that mattered, is the defensible order — and it is a stronger
   report than a large design with missing runs. The fact that §B4 flags "3 h may be too
   short to reach equilibrium" is the reason **time** should be screened before it is
   optimised: optimising a factor that is still kinetically limited gives you a model of your
   own impatience.
3. **Fix the response definition first.** "Mangiferin mg/g DW" is a clean response. Do not
   switch to "peak area" or "TPC" between runs, and fix the dilution protocol so every run
   lands mid-calibration. A design is only as good as the consistency of its response.

Keep 20 wt % as the centre — it is bracketed by the literature (16.1 wt %) and it is the
viscosity sweet spot for a bench trial. That choice is sound; it is the *run count* and the
*response definition* that need checking.

---

## 10. What to write in the progress report (deadline 2026-11-27)

Suggested wording, honest and defensible:

> A β-alanine:citric acid:water NADES at 1:1 molar and 20 wt % total water
> (1:1:3.9 molar, counting the water of crystallisation in citric acid monohydrate) was
> prepared at 70 °C and used to extract dried mango-leaf powder at a 1:60 g/mL solid:liquid
> ratio, 45 °C, 3 h, without agitation, in triplicate alongside a solvent blank. Mangiferin
> was quantified by RP-HPLC after C18 solid-phase cleanup. The 20 wt % water level is the
> centre point of the response-surface design and lies modestly wetter than the published
> β-Ala:CA:H₂O formulation (1:1:3 molar, 16.1 wt %), which was applied to mango peel and
> seed, not leaf; the present work is therefore a proposed mango-leaf method under test, not
> an established one.

And two sentences that will earn you credit, both drawn from this document:

> The static 45 °C condition was chosen to exclude agitation as a variable; it is expected to
> give a lower yield than the published agitated (30 min, 800 rpm) and ultrasound (5 min)
> procedures, and the triplicate scatter will be reported as a check on whether 3 h is long
> enough to reach equilibrium.

---

## 11. What changed in the repo for this

| File | Change |
|---|---|
| `nades_recipe.py` | **New.** Stdlib-only batch arithmetic: mass/water-wt %/molar-ratio solving, volume and density conversion, water ladder, solid:liquid ratio, mangiferin yield. Not on the Pi's critical path; importable anywhere. |
| `tests/test_nades_recipe.py` | **New.** 48 tests: the documented 100 g weighing is asserted exactly, both invariants (1:1 molar, 20 wt %) are re-derived, the ratio/wt % confusion has a regression test, and the yield maths is checked against hand calculations. |
| `docs/MANGO_LEAF_TRIAL.md` | **New.** This protocol. |
| `README.md`, `CHANGELOG.md` | Linked/noted, so the chemistry work is no longer invisible in a water–oil repo. |

`python3 -m pytest -q` → 66 passed (48 new + 18 existing). The existing water–oil code was
not touched.

---

## 12. References

1. Ojeda GA, Vallejos MM, Sgroppo SC, Sánchez-Moreno C, de Ancos B. **Enhanced extraction of
   phenolic compounds from mango by-products using deep eutectic solvents.** *Heliyon*
   2023;9(6):e16912. doi:10.1016/j.heliyon.2023.e16912 · PMC10360955. — source of DES-2
   (β-Ala:CA:H₂O 1:1:3, clear light brown, 2350 ± 25 cP, 70 ± 2 °C, 120 min synthesis),
   the 1:60 g/mL ratio, agitation/ultrasound conditions, and the C18 SPE cleanup.
2. Mangiferin RP-HPLC, 254 nm, C18, phosphate buffer pH 2.5–2.8 : ACN 85:15 —
   *Development of new reversed-phase HPLC method for the determination of mangiferin in
   Mangifera indica*, Biosci Biotechnol Res Asia.
3. Mangiferin HPLC-DAD at 265 nm, Gemini C18 250 × 4.6 mm, 40 °C, RT 19.75 min, and leaf
   mangiferin content 3.0–6.2 % DW — *Mangiferin-Rich Mango Leaves from the Mekong Delta*
   (2026).
4. Leaf mangiferin 0.96–3.00 g/100 g DW across five North Indian varieties — Saxena et al.,
   cited therein.
5. Chem-SDI / `extractlab` background for §1: `docs/PRD.md` §1–2, `CLAUDE.md` hardware table.

---

*Not validated against your supervisor's instructions, your lab's SOP, or your HPLC
method. Treat it as a proposed method under test — which is exactly how §10 asks you to
describe it.*
