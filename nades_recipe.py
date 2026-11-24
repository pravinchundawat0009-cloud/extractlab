"""nades_recipe - batch arithmetic for the beta-alanine / citric acid / water NADES.

The solvent is a 1:1 *molar* mixture of beta-alanine (HBA) and citric acid (HBD) with
water as a third component, counted as a *weight percent of the total batch*. Two ways of
writing "the same" recipe are easy to confuse, so this module keeps them separate:

  * molar ratio  -- beta-alanine : citric acid : water = 1 : 1 : n
  * water content -- grams of water / grams of total batch, x100 (wt%)

They are NOT interchangeable. A recipe that says "20 wt% water" and a recipe that says
"1:1:3 molar" are close but distinct points:

    1:1:3 molar  -> 16.1 wt% total water  (0.2845 mol acid, 1.110 mol water)
    20 wt% water -> 1:1:3.9 molar         (0.2844 mol acid, 1.110 mol water)

The hydrate form does NOT change the solvent, only the weighing: 1:1:3 starting from
anhydrous citric acid means pipetting 3 mol of water, while starting from the monohydrate
means pipetting only 2 mol (the third is already bound in the solid). Both end at the same
16.1 wt% mixture. What you must never do is count the crystal water twice, or forget it
entirely - forgetting it is how "20 wt%" silently becomes "20 wt% added, 24 wt% actual".

Every number in docs/MANGO_LEAF_TRIAL.md comes from this module, so the protocol and the
code cannot drift apart. Pure standard library, no numpy, so it imports on the Pi and in a
bare sandbox.

Worked example (the doc's headline numbers):

    >>> r = for_total_mass(100.0, 20.0)
    >>> round(r.beta_alanine_g, 2), round(r.citric_acid_monohydrate_g, 2), round(r.added_water_g, 2)
    (25.34, 59.78, 14.88)
    >>> round(r.water_wt_pct, 2), round(r.mol_ratio, 3)
    (20.0, 1.0)
    >>> r.molar_ratio_text()   # total water per mole of acid, see docstring above
    '1:1:1.00:3.90'
"""

from __future__ import annotations

from dataclasses import dataclass

# g/mol. Mangiferin is here only for the yield calculation, not the solvent.
MOLAR_MASS = {
    "beta_alanine": 89.09,          # C3H7NO2
    "citric_acid_monohydrate": 210.14,  # C6H8O7 . H2O
    "citric_acid_anhydrous": 192.12,    # C6H8O7
    "water": 18.015,
    "mangiferin": 422.34,
}

# Assumed density of the finished solvent, g/mL. MEASURE IT - do not trust this.
# Honey-like DESs of this family sit around 1.15-1.30 g/mL; the whole point of the trial
# is to replace this placeholder with a measured number.
ASSUMED_DENSITY_G_ML = 1.20


def water_in_monohydrate(citric_acid_monohydrate_g: float) -> float:
    """Mass of water of crystallisation already present in a mass of citric acid monohydrate."""
    if citric_acid_monohydrate_g < 0:
        raise ValueError("mass cannot be negative")
    return citric_acid_monohydrate_g * MOLAR_MASS["water"] / MOLAR_MASS["citric_acid_monohydrate"]


@dataclass(frozen=True)
class Recipe:
    """A weighed-out batch. All masses in grams."""

    beta_alanine_g: float
    citric_acid_monohydrate_g: float
    added_water_g: float

    # --- derived quantities -------------------------------------------------
    @property
    def water_from_monohydrate_g(self) -> float:
        return water_in_monohydrate(self.citric_acid_monohydrate_g)

    @property
    def water_total_g(self) -> float:
        return self.added_water_g + self.water_from_monohydrate_g

    @property
    def total_g(self) -> float:
        return self.beta_alanine_g + self.citric_acid_monohydrate_g + self.added_water_g

    @property
    def water_wt_pct(self) -> float:
        return 100.0 * self.water_total_g / self.total_g

    @property
    def mol_ratio(self) -> float:
        """beta-alanine : citric acid molar ratio (1.000 is the target)."""
        return (self.beta_alanine_g / MOLAR_MASS["beta_alanine"]) / (
            self.citric_acid_monohydrate_g / MOLAR_MASS["citric_acid_monohydrate"]
        )

    @property
    def water_per_mol_acid(self) -> float:
        """Moles of TOTAL water per mole of citric acid (crystal water included)."""
        n_acid = self.citric_acid_monohydrate_g / MOLAR_MASS["citric_acid_monohydrate"]
        return (self.water_total_g / MOLAR_MASS["water"]) / n_acid

    def molar_ratio_text(self) -> str:
        """The '1:1:n' form a paper would print. Report this, not just the wt%.

        Both descriptors are honest; printing only one of them is what lets a reader
        think a 20 wt% batch is the same solvent as a 1:1:3 batch.
        """
        return f"1:{self.mol_ratio:.2f}:{self.water_per_mol_acid:.2f}"

    # --- conversions --------------------------------------------------------
    def volume_ml(self, density_g_ml: float = ASSUMED_DENSITY_G_ML) -> float:
        if density_g_ml <= 0:
            raise ValueError("density must be positive")
        return self.total_g / density_g_ml

    def scaled(self, factor: float) -> "Recipe":
        if factor <= 0:
            raise ValueError("scale factor must be positive")
        return Recipe(
            self.beta_alanine_g * factor,
            self.citric_acid_monohydrate_g * factor,
            self.added_water_g * factor,
        )

    def as_dict(self) -> dict:
        return {
            "beta_alanine_g": self.beta_alanine_g,
            "citric_acid_monohydrate_g": self.citric_acid_monohydrate_g,
            "added_water_g": self.added_water_g,
            "water_from_monohydrate_g": self.water_from_monohydrate_g,
            "water_total_g": self.water_total_g,
            "total_g": self.total_g,
            "water_wt_pct": self.water_wt_pct,
            "mol_ratio": self.mol_ratio,
        }

    def table(self, density_g_ml: float = ASSUMED_DENSITY_G_ML) -> str:
        """Markdown table ready to paste into the protocol or a lab notebook."""
        return (
            "| Ingredient | Amount |\n|---|---:|\n"
            f"| beta-alanine | **{self.beta_alanine_g:.2f} g** |\n"
            f"| citric acid monohydrate | **{self.citric_acid_monohydrate_g:.2f} g** |\n"
            f"| Purified water (added) | **{self.added_water_g:.2f} g** (approx. {self.added_water_g:.2f} mL) |\n"
            f"| *Total weighed* | *{self.total_g:.2f} g* |\n\n"
            f"Water of crystallisation in the citric acid: {self.water_from_monohydrate_g:.2f} g. "
            f"Total water in the batch: {self.water_total_g:.2f} g = **{self.water_wt_pct:.2f} wt%**. "
            f"Molar ratio beta-alanine:citric acid = **{self.mol_ratio:.3f}** "
            f"(so the mixture is {self.molar_ratio_text()} molar). "
            f"Volume at an assumed {density_g_ml:.2f} g/mL: **{self.volume_ml(density_g_ml):.1f} mL** "
            f"(measured volume may differ - see the density step)."
        )


def for_total_mass(total_g: float = 100.0, water_wt_pct: float = 20.0) -> Recipe:
    """Recipe that weighs out exactly `total_g` with `water_wt_pct` total water, 1:1 molar solids.

    Solving the mass and water balances simultaneously gives

        n_solids = total_g * (1 - w) / (M_bAla + M_CAM - M_water)

    where the M_water is subtracted because the monohydrate's water is part of the batch
    already and must not be weighed twice.
    """
    if total_g <= 0:
        raise ValueError("total_g must be positive")
    if not 0 < water_wt_pct < 100:
        raise ValueError("water_wt_pct must be between 0 and 100")

    w = water_wt_pct / 100.0
    n = total_g * (1.0 - w) / (
        MOLAR_MASS["beta_alanine"] + MOLAR_MASS["citric_acid_monohydrate"] - MOLAR_MASS["water"]
    )
    cam_g = MOLAR_MASS["citric_acid_monohydrate"] * n
    added_water_g = w * total_g - water_in_monohydrate(cam_g)
    if added_water_g < 0:
        raise ValueError(
            f"{water_wt_pct} wt% water is below what the monohydrate already supplies; "
            "use anhydrous citric acid or raise the water content"
        )
    return Recipe(MOLAR_MASS["beta_alanine"] * n, cam_g, added_water_g)


def for_volume(
    volume_ml: float,
    water_wt_pct: float = 20.0,
    density_g_ml: float = ASSUMED_DENSITY_G_ML,
) -> Recipe:
    """Recipe yielding about `volume_ml` of finished solvent at the given density."""
    if volume_ml <= 0:
        raise ValueError("volume_ml must be positive")
    return for_total_mass(volume_ml * density_g_ml, water_wt_pct)


def for_solids(
    beta_alanine_g: float | None = None,
    citric_acid_monohydrate_g: float | None = None,
    water_wt_pct: float = 20.0,
) -> Recipe:
    """Scale up from a mass you have already weighed, keeping 1:1 and the target water wt%.

    Useful when the balance gives you e.g. 25.31 g of beta-alanine instead of 25.34 g: fix
    the solid you actually weighed, and let the other two components follow.
    """
    if (beta_alanine_g is None) == (citric_acid_monohydrate_g is None):
        raise ValueError("give exactly one of beta_alanine_g / citric_acid_monohydrate_g")
    if water_wt_pct <= 0 or water_wt_pct >= 100:
        raise ValueError("water_wt_pct must be between 0 and 100")
    w = water_wt_pct / 100.0

    if beta_alanine_g is not None:
        n = beta_alanine_g / MOLAR_MASS["beta_alanine"]
    else:
        n = citric_acid_monohydrate_g / MOLAR_MASS["citric_acid_monohydrate"]

    b_g = MOLAR_MASS["beta_alanine"] * n
    cam_g = MOLAR_MASS["citric_acid_monohydrate"] * n
    # total water = n*Mw_water + added ; total mass = b + cam + added
    # solve added:  (n*Mw + a) / (b + cam + a) = w
    num = w * (b_g + cam_g) - n * MOLAR_MASS["water"]
    added = num / (1.0 - w)
    if added < 0:
        raise ValueError("that much solid cannot reach this water content; check the target")
    return Recipe(b_g, cam_g, added)


def solid_liquid_ratio(sample_g: float, solvent_ml: float) -> float:
    """g of leaf powder per mL of solvent, expressed as the '1:X' the literature uses."""
    if sample_g <= 0 or solvent_ml <= 0:
        raise ValueError("sample and solvent must be positive")
    return solvent_ml / sample_g


def mangiferin_mg_per_g_dw(
    conc_ug_per_ml: float,
    extract_volume_ml: float,
    dilution_factor: float,
    leaf_g: float,
    moisture_wt_pct: float = 0.0,
    blank_conc_ug_per_ml: float = 0.0,
) -> float:
    """Convert an HPLC result into mg mangiferin per g of dry leaf powder.

    conc_ug_per_ml        -- from the calibration curve, in the injected (diluted) solution
    dilution_factor       -- e.g. 5 for a 1:4 extract:water dilution, then any further step
    blank_conc_ug_per_ml  -- the solvent blank at the same retention time; subtracted
    moisture_wt_pct       -- residual moisture in the "dried" powder, measured by drying

    Results are reported per gram of DRY weight (DW), which is why the moisture term exists;
    skipping it overstates the yield by the moisture percentage.
    """
    if leaf_g <= 0:
        raise ValueError("leaf_g must be positive")
    if dilution_factor <= 0:
        raise ValueError("dilution_factor must be positive")
    if not 0 <= moisture_wt_pct < 100:
        raise ValueError("moisture_wt_pct must be in [0, 100)")

    total_ug = (conc_ug_per_ml - blank_conc_ug_per_ml) * extract_volume_ml * dilution_factor
    dry_g = leaf_g * (1.0 - moisture_wt_pct / 100.0)
    return total_ug / 1000.0 / dry_g


if __name__ == "__main__":  # pragma: no cover - manual inspection helper
    print("== trial batch: 100 g at 20 wt% water ==")
    r = for_total_mass(100.0, 20.0)
    print(r.table())
    print()
    print("== water ladder at 1:1 molar, 100 g total ==")
    print("| water wt% | beta-alanine g | citric acid mono g | added water g |")
    print("|---:|---:|---:|---:|")
    for w in (10, 15, 20, 25, 30):
        rr = for_total_mass(100.0, w)
        print(f"| {w} | {rr.beta_alanine_g:.2f} | {rr.citric_acid_monohydrate_g:.2f} | {rr.added_water_g:.2f} |")
    print()
    print("== how big a batch do I need? ==")
    for ml in (40, 50, 70, 80):
        rr = for_volume(ml)
        print(f"  {ml} mL solvent -> weigh {rr.total_g:.1f} g  "
              f"({rr.beta_alanine_g:.2f} g bAla + {rr.citric_acid_monohydrate_g:.2f} g CAM + {rr.added_water_g:.2f} g water)")
    print()
    print(f"== 0.50 g leaf in 20 mL solvent = 1:{solid_liquid_ratio(0.5, 20.0):.0f} g/mL; "
          f"in 30 mL = 1:{solid_liquid_ratio(0.5, 30.0):.0f} g/mL (paper used 1:60) ==")
