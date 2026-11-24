"""The protocol document and the arithmetic must not drift apart.

docs/MANGO_LEAF_TRIAL.md quotes a lot of numbers. Numbers in prose rot: someone edits the
doc, or the module, and the two disagree for months. These tests read the actual markdown
and assert every batch figure in it against nades_recipe, so a drift is a red test rather
than a wrong weighing at the bench.

If you intentionally change a recipe, change the module first, run the tests, and let them
tell you exactly which table rows in the document to update.
"""

import re
from pathlib import Path

import pytest

import nades_recipe as nr

DOC = Path(__file__).resolve().parent.parent / "docs" / "MANGO_LEAF_TRIAL.md"


@pytest.fixture(scope="module")
def doc_text():
    if not DOC.exists():  # pragma: no cover - doc is part of the deliverable
        pytest.skip(f"{DOC} not found")
    return DOC.read_text(encoding="utf-8")


def _ladder_rows(text: str):
    """Pull the '| 20 | 25.34 | 59.78 | 14.88 | 1:1:3.90 |' rows out of the water ladder."""
    rows = {}
    for line in text.splitlines():
        # the centre row is bolded in the doc, so drop the emphasis markers before parsing
        m = re.match(
            r"^\|\s*(\d{1,2})\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*"
            r"\|\s*([\d.]+)\s*\|\s*([\d:.]+)\s*\|",
            line.replace("*", ""),
        )
        if m:
            w = int(m.group(1))
            if w in (10, 15, 20, 25, 30):
                rows[w] = (float(m.group(2)), float(m.group(3)), float(m.group(4)), m.group(5))
    return rows


def test_the_water_ladder_in_the_doc_is_what_the_module_computes(doc_text):
    rows = _ladder_rows(doc_text)
    assert set(rows) == {10, 15, 20, 25, 30}, f"ladder rows found: {sorted(rows)}"
    for w, (b_ala, cam, added, ratio) in rows.items():
        r = nr.for_total_mass(100.0, float(w))
        assert round(r.beta_alanine_g, 2) == pytest.approx(b_ala, abs=0.01), f"{w} wt% beta-alanine"
        assert round(r.citric_acid_monohydrate_g, 2) == pytest.approx(cam, abs=0.01), f"{w} wt% acid"
        assert round(r.added_water_g, 2) == pytest.approx(added, abs=0.01), f"{w} wt% water"
        assert ratio == r.molar_ratio_text().replace("1:1.00:", "1:1:"), (
            f"{w} wt% molar ratio: doc says {ratio}, module says {r.molar_ratio_text()}"
        )


def test_the_headline_100g_weighing_is_in_the_doc(doc_text):
    r = nr.for_total_mass(100.0, 20.0)
    for value in (r.beta_alanine_g, r.citric_acid_monohydrate_g, r.added_water_g):
        assert f"{value:.2f}" in doc_text, f"{value:.2f} g missing from the protocol"


def test_the_200ml_batch_weighing_is_in_the_doc_and_is_consistent(doc_text):
    r = nr.for_volume(200.0)
    assert f"{r.beta_alanine_g:.2f}" in doc_text
    assert f"{r.citric_acid_monohydrate_g:.2f}" in doc_text
    assert f"{r.added_water_g:.2f}" in doc_text
    # the total it states
    assert f"{round(r.total_g, 1)} g" in doc_text or f"{r.total_g:.1f} g" in doc_text


def test_the_docs_claim_that_20wtpct_is_a_200ml_batch_for_four_containers_holds(doc_text):
    """The doc's core sizing argument: 4 x 30 mL must fit in the batch it recommends."""
    assert "4 × 30 mL" in doc_text or "4 × 30" in doc_text
    assert nr.for_volume(200.0).volume_ml() >= 4 * 30.0


def test_the_published_16_wtpct_figure_is_stated(doc_text):
    published = nr.Recipe(
        beta_alanine_g=nr.MOLAR_MASS["beta_alanine"],
        citric_acid_monohydrate_g=nr.MOLAR_MASS["citric_acid_monohydrate"],
        added_water_g=2 * nr.MOLAR_MASS["water"],
    )
    assert f"{published.water_wt_pct:.1f} wt %" in doc_text


def test_the_yield_worked_example_in_the_doc_is_right(doc_text):
    """The doc's arithmetic example: 70 ug/mL, 30 mL, DF 5, 0.5 g, 6 % moisture, blank 2."""
    expected = nr.mangiferin_mg_per_g_dw(70, 30, 5, 0.5, 6, 2)
    assert expected == pytest.approx(21.7, abs=0.05)
    assert "21.7 mg/g DW" in doc_text


def test_no_molar_descriptor_in_the_doc_uses_the_wrong_2_46_figure():
    """An earlier draft claimed 20 wt% = 1:1:2.46 molar. It is 1:1:3.90. Nothing may revive it.

    This scans every '1:1:n' descriptor, but exempts occurrences on a line that explicitly
    retracts the figure: the correction note has to quote 2.46 for the reader to understand
    what was fixed. Everything else - every table row, every method description - must be a
    number the module actually produces.
    """
    text = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
    lines = text.splitlines()
    checked = 0
    for i, line in enumerate(lines):
        if "retract" in line.lower() or "really 1:1:3.9" in line or "earlier draft" in line.lower():
            continue
        for value in re.findall(r"1:1(?:\.\d+)?:(\d+\.\d+)", line):
            checked += 1
            assert float(value) != pytest.approx(2.46, abs=0.01), (
                f"line {i + 1} quotes 1:1:2.46, which is wrong for a 20 wt% batch: {line.strip()}"
            )
    assert checked > 0, "no molar descriptors were checked - the regex has stopped matching"


def test_every_molar_descriptor_in_the_ladder_is_one_the_module_can_produce(doc_text):
    """The only molar ratios allowed in the ladder are 1:1:1.73, 2.75, 3.90, 5.20, 6.69."""
    allowed = {nr.for_total_mass(100.0, float(w)).molar_ratio_text().replace("1:1.00:", "1:1:")
               for w in (10, 15, 20, 25, 30)}
    for w, (_, _, _, ratio) in _ladder_rows(doc_text).items():
        assert ratio in allowed, f"{w} wt% quotes {ratio}; module produces {sorted(allowed)}"


def test_the_doc_names_the_temperature_and_time_it_was_missing():
    """The earlier recipe's real defect: no 70 °C, no 120 min. Both must be present."""
    text = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
    assert "70" in text and "120 min" in text
    assert "70 °C" in text
