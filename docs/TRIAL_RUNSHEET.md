# How I would run this trial

*My own run sheet, written 2026-11-24 after reading your repo. This is not a fourth version of the
protocol — [`MANGO_LEAF_TRIAL.md`](MANGO_LEAF_TRIAL.md) stays the reference. This is the order I would
do things in, the calls I would make at each point, and where I think it is most likely to go wrong.*

**Read time: 8 minutes. Bench time: 3 working days.**

---

## The two decisions that shape everything

Before the first weighing, I would settle two things — because they determine whether day 1 is 6 hours
or 6 minutes.

**Decision 1: I would not make the full batch first.** The protocol says make 200 mL. I would make a
**20 g scout batch** first: 5.07 g β-alanine + 11.96 g citric acid monohydrate + 2.98 g water. Same
recipe, same 20 wt %, 1/12th the material. Reason: the one thing I genuinely cannot predict is whether
this solvent forms cleanly at *your* 20 wt % point with *your* bottle of citric acid. If it crystallises
on cooling, I want to find that out for 20 g of material in 2 hours, not for 240 g after a full day.
Everything that usually goes wrong is scale-independent, so the scout buys almost all the information
for a twelfth of the cost.

**Decision 2: I would measure the leaf's moisture before I do anything else.** It is a 2-hour oven step
with zero attention, it runs while I am doing something else, and it is the divisor in the final yield.
Without it, "mg per g dry weight" is really "mg per g of something I have not defined" — and if the
powder is holding 10 % water, every yield is overstated by 11 %. Start it first, forget it, come back
to it.

---

## Before I touch anything (20 minutes)

| # | Check | Why I would not skip it | Fails → |
|---|---|---|---|
| 1 | **Citric acid is crystalline and free-flowing, not caked** | Caked acid has absorbed water. My whole 20 wt % calculation assumes 8.58 wt % water and no more, so a damp bottle silently moves me to a wetter solvent and my centre point is no longer the centre point | Use a fresh bottle, or dry-weight it and recalculate |
| 2 | **Balance: weigh the same object twice, then a second object** | Cheap balances drift; a 0.01 g error on 143 g is nothing, but 0.01 g on a 0.500 g leaf sample is 2 % of the answer | Borrow a better balance for the leaf |
| 3 | **Thermometer reads the bath, not the dial** | A dial reading "70" can be 62 or 78. At 62 the solvent takes 3× longer; above 80 I am decomposing citric acid | Use a thermometer in the water, not the knob |
| 4 | **Two litres of water for the baths, and which bath does what** | I need 70 °C for the solvent and 45 °C for the extraction, and the 45 °C bath must be free and stable for 3 uninterrupted hours | One bath, sequential — solvent first, then turn it down |
| 5 | **Four containers, identical lids, pre-labelled** | Different lids = different evaporation over 3 h = the "random" scatter in your triplicate | Same lid type, or nothing |
| 6 | **Supervisor has seen this sheet** | Every "stop and ask" below is a decision I am not making alone | — |

---

## Day 1, morning — start the moisture test, then the scout

**t = 0 (5 min).** Weigh ~1.0 g of leaf powder into a pre-weighed, labelled dish. Record the exact
mass. Put it in the oven at **105 °C**. Write the time on the dish. Walk away.

**t = 10 min — build the scout batch.**

Weigh into a 100 mL beaker, in this order: **11.96 g citric acid monohydrate**, then **5.07 g
β-alanine**, then mix the dry powders briefly with a rod. Add the **2.98 g water** in four small
portions, stirring between each.

What I expect to see, and what I am watching for:

| Elapsed | What it looks like | What I am actually watching |
|---|---|---|
| 0 min | Wet sand, then a stiff slush | Is there free liquid? If yes I added water too fast — slow down |
| 15–30 min | Lumpy paste, smells faintly sour | Lumps are normal. Grit under the rod is **not** normal |
| 45–75 min | It suddenly goes glossy and flows | This is the eutectic forming. It is usually abrupt, not gradual |
| 90–120 min | Clear, amber, honey-like, holds a thread off the rod | Done. Stop heating — more time buys nothing |

**My stop rule: 2.5 hours at 70–80 °C, then I stop regardless.** If it is still gritty, the batch
failed, and that is a *result* — I record it, keep the beaker, and take it to my supervisor rather
than "fixing" it with extra water. Adding water to force clarity would silently move me off the design
point, and the design point is the entire experiment.

Stir bar note: start at low speed. A stir bar in a stiff paste will stall and then throw the beaker.
As the mixture clears it thins, so I would raise the speed only after it starts flowing.

**t = ~2.5 h.** Cool it in the fume hood, uncovered, to room temperature. Then split it:
cover half and check it **1 hour later** and again **the next morning**. Crystals at 20 wt % on cooling
is the single most likely surprise, and it is worth knowing before I commit the full batch.

**t = ~3 h. Measure the density of whatever I made.** Dry, stoppered 10 mL cylinder: weigh empty,
fill to the mark, weigh full, subtract, divide. Twice. This number replaces the placeholder `1.20` in
`nades_recipe.py`, and it is the only new physical constant the whole trial produces.

**t = ~3.5 h.** Take the moisture dish out, cool in a desiccator, weigh, and put it back for another
hour. Repeat until two consecutive weights agree within 0.002 g. That is constant mass.

---

## The gate between day 1 and day 2

| Observation | My call |
|---|---|
| Clear solvent, no crystals after 24 h, density 1.10–1.35 g/mL | **Proceed** to the full batch |
| Clear but crystals appeared overnight | **Stop and tell my supervisor.** This is a real finding about the 20 wt % point, not a mistake. The fallback is 25 wt %, which requires a design change I would rather discuss than make quietly |
| Gritty after 2.5 h | **Stop.** Report, keep the beaker, do not add water |
| Density outside 1.10–1.35 | Something is wrong with the composition or the measurement. Re-measure before scaling |

I would write the density and the colour on the beaker in marker, because on day 2 I will not remember.

---

## Day 2 — the full batch, then the extraction

**Full batch (240 g, ~200 mL).** Same procedure, bigger vessel: **143.47 g citric acid monohydrate +
60.83 g β-alanine + 35.70 g water**. 400–600 mL beaker, because it foams and climbs the wall while it
wets out. Same 70 °C, same stirring, same 2.5 h stop rule. Expect it to take slightly *longer* than the
scout, not shorter — more mass, more heat-up time, less uniform mixing.

**While that runs, weigh out the leaf.** Three portions of **0.500 g**, to the nearest milligram if the
balance allows. This is the number the final result is divided by, so I would not rush it: a 0.04 g
error is an 8 % error on my yield.

**Now the aliquots — and this is where I would ignore the protocol's own first instinct.**

The protocol says 30 mL. At 1.2 g/mL that is 36.0 g. But **I would weigh it, not pipette it**, and I
would use *my* measured density from day 1:

```
mass per container = 30 mL × (my measured density)
```

At 1.2 g/mL that is 36.0 g per container, 144 g for four. At 2350 cP this liquid takes minutes to
drain out of a pipette and leaves a film behind, so a "30 mL" pipetted aliquot can easily be 26 mL. On
a design factor, that is a silent change to the solid:liquid ratio — the kind of error that shows up
later as unexplainable scatter.

**Assembly, in the order I would do it:**

1. Leaf into the three sample containers first (weighed, recorded), nothing in the fourth.
2. Solvent on top, then stir each briefly with its own glass rod to break up the crust. Dry powder
   dropped into 2350 cP solvent forms a skin that never wets.
3. Weigh each container before and after adding solvent, so the actual mass in every container is
   recorded rather than assumed.
4. Same lid, same tightness, on all four.

**45 °C for 3 hours, static.** Bath pre-equilibrated *before* the containers go in. All four in at
once. Write t = 0 on the sheet. Then check the bath temperature at 30, 60, 120 and 180 minutes — a
cold beaker drags it down and it may not recover. And then **leave them alone**. No shaking, no
stirring, no ultrasound. That is the whole point of this arm.

While they sit: photograph each container at t = 0 and t = 3 h. Colour change is data, it costs
nothing, and it is what lets me say later whether the blank and the samples behaved alike.

---

## Day 3 — separate, record, hand over

**Cool to room temperature before opening.** Warm extract plus room air equals condensation, and a
volume I cannot account for.

**Centrifuge 20 000 × g for 30 min** — the published condition — with all four treated identically. If
I filter instead, I record the membrane material, because cellulose adsorbs phenolics and would quietly
cost me recovery.

Then, for each of the four: record the **volume I actually recovered**. This is not the same as 30 mL,
and it matters for the HPLC dilution even though the yield calculation uses the 30 mL extraction
volume.

**Store at −20 °C, in the dark, and write the date.** Record how long it sat before HPLC; it belongs
in the report.

**The handover package.** I would give the HPLC lab five things, not four:

1. The three samples + the blank, labelled with ID, solvent, temperature, time.
2. The **blank explicitly flagged** as "must be injected at the same dilution" — not optional.
3. My predicted concentration range, so they can bracket the calibration: for 0.5 g leaf in 30 mL and
   1–4 % mangiferin in the leaf, the diluted (1:4) solution should land roughly **20–110 µg/mL**.
4. The cleanup I am asking for, in writing: 1:4 water dilution, 1 g C18 SPE, 4 mL water wash, elute
   with 3 mL methanol + 0.1 % formic acid.
5. The question I need answered in advance: *what is your LOQ, so I know how much to dilute?*

If they hand back a number under 5 µg/mL, my first suspicion is the dilution or the SPE recovery, not
the leaf. If they hand back something off the top of the curve, the number is meaningless and I would
ask for a re-injection rather than report it.

---

## What I would deliberately not do

- **Not make 100 g.** It is only ~83 mL and I need 120 mL for four containers. I would rather make one
  batch too big than two batches that differ.
- **Not pipette the aliquots.** Weighed, per measured density.
- **Not skip the blank.** It is the only thing that lets me claim the mangiferin came from the leaf.
- **Not inject raw NADES.** It would foul the column and the citric acid would wreck the peak shape.
- **Not add water to rescue a gritty batch.** That moves the design point.
- **Not run five water levels first.** I do not yet know that 3 hours reaches equilibrium, so a
  water-level study right now would be mapping a moving target.

---

## Where I think this actually goes wrong (top 4, ranked)

**1. The 3 h static step does not reach equilibrium.** This is my real doubt about the whole plan. The
published work used 30 min at 800 rpm, or 5 min of ultrasound. Static diffusion through a 2350 cP
liquid is far slower, and if 3 hours is not enough, my triplicates will disagree for a reason that has
nothing to do with the leaf. *Mitigation:* read the triplicate SD as the diagnostic. If it is above
~30 % of the mean, I would run a time arm (1 h vs 3 h vs 6 h) before touching another factor.

**2. Crystals in the 20 wt % solvent.** *Mitigation:* the scout batch finds this for 20 g, and the
24-hour check catches it before the full batch.

**3. The liquid is too viscous to handle reproducibly.** *Mitigation:* weigh everything, never measure
volume; expect slower filtering and reach for the centrifuge early.

**4. Evaporation through imperfectly sealed lids over 3 h.** *Mitigation:* identical lids, and record
every container's mass before and after the bath. If a sample loses more than ~1 % of its mass, I know
the lid leaked and I can flag that container rather than wonder about the leaf.

---

## The honest summary of the plan

The recipe is not the risk. The maths is checked, the ratio is right, and the numbers in the protocol
are reproducible to 0.01 g. **The risk is that I have chosen a slow, unagitated extraction and I do not
yet know whether 3 hours is long enough** — and I have no way to find that out except by running it and
looking at how well the triplicates agree.

So I would spend day 1 on a 20 g scout and a moisture test, and treat the triplicate's spread on day 3
as the actual result of this trial — more informative than the yield itself. If the three samples agree
tightly, 3 hours is enough and the design can move to the next water level. If they do not, the trial
has still told me something useful, and it told me before I spent a week on an optimist's schedule.

---

<!-- Build note (not printed): regenerate this PDF with
     python3 tools/typeset_protocol.py --src docs/TRIAL_RUNSHEET.md --out docs/TRIAL_RUNSHEET.pdf -->
