"""Tests the judging styles."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from coa_judicial_behavior import typology


def judges_like(styles: list[str], each: int = 12, seed: int = 3) -> pd.DataFrame:
    """Returns judges whose scores lie around the profiles of `styles`."""
    random = np.random.default_rng(seed)
    rows = []
    for style in styles:
        profile = typology.PROTOTYPES.loc[style]
        for _ in range(each):
            scores = 50 + 15 * profile + random.normal(0, 2, size = 4)
            rows.append({
                'style_true': style,
                # Half of the judges are on the left of zero, which the
                # absolute Ideology Score treats like the right.
                'ideology': scores['ideological'] * random.choice([-1, 1]),
                'activism': scores['activism'],
                'partisanship': scores['partisanship'],
                'independence': scores['independence'],
                'qualified': True})
    return pd.DataFrame(rows)


def test_classify_finds_styles() -> None:
    judges = judges_like(list(typology.STYLES))
    found = typology.classify(judges)
    assigned = found.assignments.join(judges['style_true'])
    # Every judge is given the style whose profile the judge was drawn
    # around.
    assert (assigned['style'] == assigned['style_true']).all()
    assert found.profiles['judges'].tolist() == [12] * 9
    assert set(found.profiles['style']) == set(typology.STYLES)
    assert found.distinct
    assert found.differences.shape == (9, 9)
    assert (np.diag(found.differences) == 0).all()


def test_classify_other_numbers() -> None:
    judges = judges_like(['Stalwart', 'Collegial', 'Minimalist'])
    found = typology.classify(judges, 3)
    assert set(found.profiles['style']) == {'Cluster 1', 'Cluster 2', 'Cluster 3'}
    assert found.profiles['distance'].isna().all()
    named = typology.classify(
        judges, 3, names = ['Stalwart', 'Collegial', 'Minimalist'])
    assigned = named.assignments.join(judges['style_true'])
    assert (assigned['style'] == assigned['style_true']).all()


def test_classify_leaves_out_judges() -> None:
    judges = judges_like(['Stalwart', 'Collegial'], each = 5)
    judges.loc[0, 'qualified'] = False
    judges.loc[1, 'activism'] = np.nan
    found = typology.classify(judges, 2)
    assert len(found.assignments) == 8
    assert {0, 1}.isdisjoint(found.assignments.index)
    with pytest.raises(ValueError, match = 'cannot be sorted'):
        typology.classify(judges.head(3), 9)
