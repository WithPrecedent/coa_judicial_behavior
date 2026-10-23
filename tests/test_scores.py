"""Tests the four scores."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from conftest import Simulation

from coa_judicial_behavior import scores


def votes_of(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Returns a small table of votes from the rows that differ."""
    defaults = {
        'judge': 'Judge', 'judge_party': -1.0, 'court_num': 1,
        'type_criminal': False, 'review_standard': 'deferential',
        'vote_reversal': False, 'judge_dissented': False,
        'judge_concurred': False, 'judge_author': True,
        'district_party': np.nan, 'alignment': np.nan}
    table = pd.DataFrame([
        {**defaults, 'case_id': f'c{i}', 'judge_nid': 1, **row}
        for i, row in enumerate(rows)])
    table.index = pd.Index([f'v{i}' for i in range(len(table))])
    return table


def cast(standard: str, total: int, reversals: int, **row: object) -> list[dict[str, object]]:
    """Returns the votes of one judge in one cell."""
    return [
        {'review_standard': standard, 'vote_reversal': i < reversals, **row}
        for i in range(total)]


def test_activism_formula() -> None:
    # Judge Wood's example in Flexing Judicial Muscle: 4 reversals of 53 under
    # deferential standards and 13 of 49 under de novo review.
    table = votes_of(
        cast('deferential', 53, 4) + cast('non_deferential', 49, 13))
    scored = scores.score_judges(
        table, method = 'original', minimum = 0, cell_minimum = 1,
        circuit = 'none')
    assert scored['activism_raw'][0] == pytest.approx(4 / 53 - 13 / 49)
    assert scored['activism_super_panel'][0] == 0
    assert scored['activism_adjusted'][0] == pytest.approx(4 / 53 - 13 / 49)


def test_partisanship_formula() -> None:
    # A Democratic appointee who defers more to Democratic district judges
    # under deferential standards is partisan, and a Republican appointee
    # who does the same is not.
    rows = (
        cast('deferential', 4, 0, district_party = -1.0)
        + cast('deferential', 4, 2, district_party = 1.0)
        + cast('non_deferential', 4, 1, district_party = -1.0)
        + cast('non_deferential', 4, 1, district_party = 1.0))
    democrat = scores.score_judges(
        votes_of(rows), minimum = 0, cell_minimum = 1, circuit = 'none')
    assert democrat['partisanship_raw'][0] == pytest.approx(0.5)
    # The rates of all judges are the same for both parties, so the
    # super-panel takes nothing away.
    assert democrat['partisanship_super_panel'][0] == pytest.approx(0)
    republican = scores.score_judges(
        votes_of([{**row, 'judge_party': 1.0} for row in rows]),
        minimum = 0, cell_minimum = 1, circuit = 'none')
    assert republican['partisanship_raw'][0] == pytest.approx(-0.5)


def test_district_score_formula() -> None:
    # A judge who affirms Republican appointees more often has a positive
    # (conservative) District Score.
    rows = (
        cast('deferential', 10, 1, district_party = 1.0)
        + cast('deferential', 10, 5, district_party = -1.0))
    scored = scores.score_judges(
        votes_of(rows), method = 'original', minimum = 0, cell_minimum = 1,
        circuit = 'none')
    # Only deferential review of civil cases, so the weight is one.
    assert scored['ideology_district'][0] == pytest.approx(0.9 - 0.5)
    assert scored['ideology_panel'][0] == 0
    assert scored['ideology_raw'][0] == pytest.approx(0.4)


def test_scores_find_traits(simulation: Simulation) -> None:
    table = scores.score_judges(simulation.votes)
    merged = table.set_index('judge_nid').join(
        simulation.traits, rsuffix = '_true')
    assert merged['qualified'].all()
    expected = {
        'ideology': 0.6, 'activism': 0.45, 'partisanship': 0.3,
        'independence': 0.7}
    for score, least in expected.items():
        correlation = merged[score].corr(
            merged[f'{score}_true'], method = 'spearman')
        assert correlation > least, score


def test_scales(simulation: Simulation) -> None:
    table = scores.score_judges(simulation.votes)
    for score in ('activism', 'partisanship', 'independence'):
        assert table[score].min() == pytest.approx(0)
        assert table[score].max() == pytest.approx(100)
    assert table['ideology'].abs().max() == pytest.approx(100)
    # The table is sorted from the most liberal judge, and liberal judges
    # are mostly Democratic appointees.
    assert table['ideology'].is_monotonic_increasing
    liberal = table['ideology'] < 0
    assert (table.loc[liberal, 'judge_party'] == -1).mean() > 0.7
    assert {'circuit', 'votes', 'interactions', 'traveling_votes'} <= set(
        table.columns)
    assert table['traveling_votes'].sum() > 0


def test_methods(simulation: Simulation) -> None:
    typology = scores.score_judges(simulation.votes)
    original = scores.score_judges(simulation.votes, method = 'original')
    # The original Ideology Score puts its zero at the judge whose rank is
    # the number of Democratic appointees.
    democrats = int((original['judge_party'] == -1).sum())
    ranked = np.sort(original['ideology'].to_numpy())
    assert ranked[democrats - 1] <= 0 <= ranked[democrats]
    assert (original['activism_super_panel'] == 0).all()
    assert (typology['activism_super_panel'] != 0).any()
    # The per-judge circuit adjustment is the same for every judge of a
    # circuit.
    per_judge = original.groupby('circuit')['ideology_circuit'].nunique()
    assert (per_judge == 1).all()
    none = scores.score_judges(simulation.votes, circuit = 'none')
    assert (none['ideology_circuit'] == 0).all()
    full = scores.score_judges(simulation.votes, circuit = 'full')
    assert (full['ideology_circuit'] != 0).any()


def test_by_year(simulation: Simulation) -> None:
    table = scores.score_judges(simulation.votes, by = 'year', minimum = 100)
    assert set(table['year']) == {2008, 2009}
    assert table.columns[1] == 'year'
    assert len(table) == 2 * simulation.traits.shape[0]


def test_provoked(simulation: Simulation) -> None:
    author = scores.score_judges(simulation.votes, provoked = 'author')
    panel = scores.score_judges(simulation.votes, provoked = 'panel')
    assert (panel['dissent_rate'] >= author['dissent_rate'] - 1e-12).mean() > 0.5
    assert panel['dissent_rate'].mean() > author['dissent_rate'].mean()


def test_errors(simulation: Simulation) -> None:
    with pytest.raises(ValueError, match = 'method'):
        scores.score_judges(simulation.votes, method = 'newest')
    with pytest.raises(ValueError, match = 'circuit'):
        scores.score_judges(simulation.votes, circuit = 'some')
    with pytest.raises(ValueError, match = 'provoked'):
        scores.score_judges(simulation.votes, provoked = 'nobody')
    with pytest.raises(KeyError, match = 'review_standard'):
        scores.score_judges(simulation.votes.drop(columns = 'review_standard'))
