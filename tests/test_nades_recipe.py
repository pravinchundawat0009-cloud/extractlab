"""Tests for nades_recipe - the batch arithmetic behind docs/MANGO_LEAF_TRIAL.md.

The point of these tests is that the protocol document and any spreadsheet someone builds
later can be checked against one authority, and that the two common recipe mistakes are
caught rather than silently baked in:

  1. counting the monohydrate's water twice (or not at all)
  2. treating "20 wt% water" and "1:1:3 molar" as the same solvent

Stdlib only, so this runs on the Pi where pytest is an apt package.
"""

import math

import pytest

import nades_recipe as nr


# --- the documented recipe must not drift -----------------------------------

def test_100g_20wtpct_matches_the_documented_weighing():
    r = nr.for_total_mass(100.0, 20.0)
    assert round(r.beta_alanine_g, 2) == 25.34
    assert round(r.citric_acid_monohydrate_g, 2) == 59.78
    assert round(r.added_water_g, 2) == 14.88


def test_100g_20wtpct_really_is_1_to_1_molar_and_20_wtpct_water():
    r = nr.for_total_mass(100.0, 20.0)
    assert math.isclose(r.total_g, 100.0, abs_tol=1e-6)
    assert math.isclose(r.mol_ratio, 1.0, abs_tol=2e-3)
    assert math.isclose(r.water_wt_pct, 20.0, abs_tol=1e-6)


def test_water_of_crystallisation_is_counted_once():
    r = nr.for_total_mass(100.0, 20.0)
    assert math.isclose(r.water_from_monohydrate_g, 5.12, abs_tol=0.01)
    # total water = what came with the acid + what was pipetted in
    assert math.isclose(r.water_total_g, r.added_water_g + r.water_from_monohydrate_g)
    # and the pipetted part alone is less than 20 wt% - that is the whole subtlety
    assert r.added_water_g < 0.20 * r.total_g


# --- the ratio/wtpct confusion ---------------------------------------------

def test_one_to_one_to_three_molar_is_about_16_wtpct_water():
    """Ojeda et al. 2023, DES-2: beta-Ala:CA:H2O = 1:1:3 molar.

    Counted as TOTAL water (the monohydrate's crystal water included), that is 3 mol of
    water per mole of acid: 54.05 g in 335.26 g = 16.1 wt%. This is the number that makes
    "1:1:3" and "20 wt%" comparable at all - they are close cousins (3.9 vs 3.0 mol water),
    not the same solvent and not unrelated solvents either.

    Two corrections are baked into this test, both caught by running it:
      * an earlier draft said 15.3 wt% - that counted the crystal water twice;
      * the hydrate form is irrelevant to the wt%, only to how you weigh it out. Starting
        from anhydrous acid (192.12 g/mol + 3 mol water) gives the SAME 16.1 wt%.
    """
    m_b, m_cam, m_w = (
        nr.MOLAR_MASS["beta_alanine"],
        nr.MOLAR_MASS["citric_acid_monohydrate"],
        nr.MOLAR_MASS["water"],
    )
    # 1 mol acid already brings 1 mol water, so add 2 mol to reach 3 mol total
    r = nr.Recipe(beta_alanine_g=m_b, citric_acid_monohydrate_g=m_cam, added_water_g=2 * m_w)
    assert math.isclose(r.water_wt_pct, 16.12, abs_tol=0.05)

    # Same mixture built from the ANHYDROUS acid: weigh 192.12 g and pipette all 3 mol of
    # water instead of 2. Identical atoms in, identical wt% out - the hydrate is a
    # weighing convenience, not a different solvent.
    m_anhy = nr.MOLAR_MASS["citric_acid_anhydrous"]
    anhy_wtpct = 100.0 * (3 * m_w) / (m_b + m_anhy + 3 * m_w)
    assert math.isclose(anhy_wtpct, r.water_wt_pct, abs_tol=0.01)
    # the crystal water is the difference between the two weighings. Tolerance is 0.01 g
    # and not 1e-9 because the tabulated molar masses are themselves rounded: the handbook
    # figures give 210.14 - 192.12 = 18.02 g/mol for the water of crystallisation, against
    # 18.015 for water. Half a hundredth of a gram, not a chemistry problem.
    assert math.isclose(m_cam - m_anhy, m_w, abs_tol=0.01)


def test_the_20wtpct_recipe_is_about_1_to_1_to_3_9_molar_not_1_to_1_to_2_46():
    """Regression: an earlier draft of the doc claimed 1:1:2.46. That is wrong.

    20 wt% total water per 1 mol of acid is 1.11 mol water / 0.2845 mol acid = 3.90.
    Counting only the water that was pipetted in gives 2.90 - which is exactly the
    confusion the doc warns about, since ignoring the crystal water hides a whole mole.
    """
    r = nr.for_total_mass(100.0, 20.0)
    n_water_total = r.water_total_g / nr.MOLAR_MASS["water"]
    n_water_added = r.added_water_g / nr.MOLAR_MASS["water"]
    n_solids = r.beta_alanine_g / nr.MOLAR_MASS["beta_alanine"]

    assert math.isclose(n_water_total / n_solids, 3.90, abs_tol=0.03)
    assert math.isclose(n_water_added / n_solids, 2.90, abs_tol=0.03)
    # and neither of them is 2.46
    assert not math.isclose(n_water_total / n_solids, 2.46, abs_tol=0.1)


def test_the_20wtpct_batch_is_wetter_than_the_published_one_to_one_to_three():
    published = nr.Recipe(
        beta_alanine_g=nr.MOLAR_MASS["beta_alanine"],
        citric_acid_monohydrate_g=nr.MOLAR_MASS["citric_acid_monohydrate"],
        added_water_g=2 * nr.MOLAR_MASS["water"],
    )
    trial = nr.for_total_mass(100.0, 20.0)
    assert trial.water_wt_pct > published.water_wt_pct
    assert trial.water_wt_pct - published.water_wt_pct < 5.0  # close, a few wt% apart


# --- scaling and volume ----------------------------------------------------

@pytest.mark.parametrize("total_g", [20.0, 48.0, 100.0, 250.0])
@pytest.mark.parametrize("w", [10.0, 15.0, 20.0, 25.0, 30.0])
def test_scaling_preserves_both_invariants(total_g, w):
    r = nr.for_total_mass(total_g, w)
    assert math.isclose(r.total_g, total_g, abs_tol=1e-6)
    assert math.isclose(r.water_wt_pct, w, abs_tol=1e-6)
    assert math.isclose(r.mol_ratio, 1.0, abs_tol=2e-3)
    assert r.added_water_g > 0


def test_volume_batch_scales_with_density_in_the_right_direction():
    """A fixed volume needs MORE mass when the solvent is denser - not less."""
    r = nr.for_volume(40.0)
    assert math.isclose(r.volume_ml(), 40.0, abs_tol=1e-6)
    heavy = nr.for_volume(40.0, density_g_ml=1.30)
    light = nr.for_volume(40.0, density_g_ml=1.15)
    assert heavy.total_g > light.total_g
    assert math.isclose(heavy.total_g, 52.0, abs_tol=1e-6)
    assert math.isclose(light.total_g, 46.0, abs_tol=1e-6)
    # same volume, same recipe invariants
    for rec in (heavy, light):
        assert math.isclose(rec.mol_ratio, 1.0, abs_tol=2e-3)
        assert math.isclose(rec.water_wt_pct, 20.0, abs_tol=1e-6)


def test_fixing_a_weighed_solid_keeps_the_ratio_and_the_water():
    r = nr.for_solids(beta_alanine_g=25.31, water_wt_pct=20.0)
    assert math.isclose(r.beta_alanine_g, 25.31)
    assert math.isclose(r.mol_ratio, 1.0, abs_tol=1e-9)
    assert math.isclose(r.water_wt_pct, 20.0, abs_tol=1e-6)


def test_fixing_the_acid_gives_the_same_answer_as_fixing_the_alanine():
    a = nr.for_solids(beta_alanine_g=25.34, water_wt_pct=20.0)
    b = nr.for_solids(citric_acid_monohydrate_g=a.citric_acid_monohydrate_g, water_wt_pct=20.0)
    assert math.isclose(a.added_water_g, b.added_water_g, abs_tol=1e-9)


def test_scaled_recipe_is_proportional():
    base = nr.for_total_mass(100.0, 20.0)
    big = base.scaled(2.5)
    assert math.isclose(big.total_g, 250.0)
    assert math.isclose(big.water_wt_pct, base.water_wt_pct, abs_tol=1e-9)


# --- the trial design numbers ---------------------------------------------

def test_fifty_ml_batch_covers_the_recommended_trial_with_margin():
    """3 samples x 30 mL + 1 blank x 30 mL = 120 mL needed; a ~200 mL batch covers it."""
    per_container_ml = 30.0
    needed = 4 * per_container_ml
    r = nr.for_volume(200.0)
    assert r.volume_ml() >= needed
    assert r.total_g > 200.0  # mass > volume for a solvent denser than water


def test_thirty_ml_reproduces_the_papers_solid_liquid_ratio():
    assert math.isclose(nr.solid_liquid_ratio(0.5, 30.0), 60.0, abs_tol=1e-9)


def test_twenty_ml_is_a_diluter_extraction_than_the_paper():
    assert nr.solid_liquid_ratio(0.5, 20.0) == pytest.approx(40.0)
    assert nr.solid_liquid_ratio(0.5, 20.0) < 60.0


# --- results arithmetic ---------------------------------------------------

def test_mangiferin_yield_conversion():
    # 0.50 g leaf, 30 mL extract, 1:4 water dilution (factor 5), 80 ug/mL on the HPLC
    y = nr.mangiferin_mg_per_g_dw(80.0, 30.0, 5.0, 0.50)
    assert math.isclose(y, 24.0, abs_tol=1e-9)  # 80*30*5 = 12000 ug = 12 mg / 0.5 g


def test_blank_is_subtracted_and_moisture_is_excluded():
    clean = nr.mangiferin_mg_per_g_dw(80.0, 30.0, 5.0, 0.50)
    blanked = nr.mangiferin_mg_per_g_dw(80.0, 30.0, 5.0, 0.50, blank_conc_ug_per_ml=10.0)
    wet = nr.mangiferin_mg_per_g_dw(80.0, 30.0, 5.0, 0.50, moisture_wt_pct=10.0)
    assert blanked < clean
    assert math.isclose(blanked, 21.0, abs_tol=1e-9)
    assert wet > clean  # same measured amount, less dry mass -> higher yield per g DW
    assert math.isclose(wet, clean / 0.9, abs_tol=1e-9)


def test_a_blank_larger_than_the_sample_reads_negative_not_zero():
    """A negative result is information: it means the solvent interferes. Do not clamp it."""
    assert nr.mangiferin_mg_per_g_dw(5.0, 30.0, 5.0, 0.50, blank_conc_ug_per_ml=9.0) < 0


# --- input validation -----------------------------------------------------

@pytest.mark.parametrize(
    "call",
    [
        lambda: nr.for_total_mass(0.0, 20.0),
        lambda: nr.for_total_mass(-5.0, 20.0),
        lambda: nr.for_total_mass(100.0, 0.0),
        lambda: nr.for_total_mass(100.0, 100.0),
        lambda: nr.for_volume(-1.0),
        lambda: nr.for_solids(beta_alanine_g=25.0, citric_acid_monohydrate_g=59.0),
        lambda: nr.for_solids(),
        lambda: nr.solid_liquid_ratio(0.0, 20.0),
        lambda: nr.mangiferin_mg_per_g_dw(10.0, 30.0, 1.0, 0.0),
        lambda: nr.mangiferin_mg_per_g_dw(10.0, 30.0, 0.0, 0.5),
    ],
)
def test_bad_input_raises(call):
    with pytest.raises(ValueError):
        call()


def test_water_below_what_the_monohydrate_supplies_is_rejected():
    """At 1:1 molar the monohydrate alone is already ~8.6 wt% water."""
    with pytest.raises(ValueError):
        nr.for_total_mass(100.0, 5.0)


def test_zero_density_rejected():
    with pytest.raises(ValueError):
        nr.for_total_mass(100.0, 20.0).volume_ml(0.0)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
