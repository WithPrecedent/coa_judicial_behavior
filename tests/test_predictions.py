"""Tests the predictors and the studies' tests of the scores."""

from __future__ import annotations

import amos
import numpy as np
import pandas as pd
import pytest
from conftest import Simulation

from coa_judicial_behavior import predictions, scores


@pytest.fixture(scope = 'module')
def scored(simulation: Simulation) -> pd.DataFrame:
    """Returns the scores of the fictional judges."""
    table = scores.score_judges(simulation.votes)
    return table.assign(style = 'Collegial')


def test_add_predictors(simulation: Simulation, scored: pd.DataFrame) -> None:
    votes = simulation.votes
    added = predictions.add_predictors(votes, scored)
    assert added.index.equals(votes.index)
    assert set(predictions.PREDICTORS) - {'holdout'} <= set(added.columns)
    first = added[added['case_id'] == 'c0']
    ideology = first['judge_ideology'].to_numpy()
    # Each judge's colleagues are the other two judges of the case.
    for place in range(3):
        others = np.delete(ideology, place).mean()
        assert first['colleagues_ideology'].iloc[place] == pytest.approx(others)
    assert first['panel_ideology_median'].iloc[0] == pytest.approx(
        np.median(ideology))
    assert first['panel_ideology_net'].iloc[0] == pytest.approx(ideology.sum())
    assert (added['judge_style'] == 'Collegial').all()
    assert added['judge_scored'].all()
    # The pressures have the signs that the studies predicted.
    opposed = added['district_opposed'].astype(bool)
    partisan = added['judge_partisanship'] > 50
    assert (added.loc[opposed & partisan, 'partisan_pressure'] > 0).all()
    assert (added.loc[~opposed & partisan, 'partisan_pressure'] < 0).all()
    deferential = added['review_standard'] == 'deferential'
    assert (added.loc[~deferential, 'activist_pressure'] == 0).all()
    assert added['expected_reversal'].between(0, 1).all()
    assert (added['concurred_only'] & added['judge_dissented']).sum() == 0


def test_score_judges_technique(simulation: Simulation) -> None:
    dataset = amos.Dataset(
        simulation.votes.copy(), label = 'vote_reversal',
        groups = ['case_id'])
    technique = predictions.ScoreJudges(parameters = {
        'train': 'year == 2008', 'clusters': 4, 'minimum': 100})
    technique.apply(dataset)
    assert {'score_judges', 'typology', 'typology_differences'} <= set(
        dataset.tables)
    table = dataset.tables['score_judges']
    assert table['style'].notna().all()
    assert len(dataset.tables['typology']) == 4
    data = dataset.data
    assert data['holdout'].tolist() == (data['year'] != 2008).tolist()
    entry = dataset.history[-1]
    assert entry['technique'] == 'score_judges'
    assert entry['scored_votes'] == int((data['year'] == 2008).sum())
    assert 'judge_activism' in entry['created']
    with pytest.raises(ValueError, match = 'must select rows'):
        predictions.ScoreJudges(parameters = {'train': 'year + 1'}).apply(
            amos.Dataset(simulation.votes.copy()))


def test_validate(simulation: Simulation, scored: pd.DataFrame) -> None:
    added = predictions.add_predictors(simulation.votes, scored)
    added['holdout'] = added['year'] == 2009
    table = predictions.validate(added)
    assert set(table['test']) == {
        'dissent', 'concurrence', 'partisan_reversal', 'activist_reversal'}
    rows = table.set_index(['test', 'measure'])
    # Independence predicts dissents and concurrences, and ideology does
    # not, as Beyond Ideology found.
    for test in ('dissent', 'concurrence'):
        assert rows.loc[(test, 'judge_independence'), 'p_value'] < 0.01
        assert rows.loc[(test, 'judge_independence'), 'coefficient'] > 0
        assert (
            rows.loc[(test, 'judge_independence'), 'pseudo_r2']
            > rows.loc[(test, 'judge_ideological'), 'pseudo_r2'])
    assert rows.loc[('dissent', 'judge_independence'), 'observations'] == (
        int(added['holdout'].sum()))
    # The Judicial Common Space score is not in the fictional votes.
    assert np.isnan(rows.loc[('dissent', 'abs_jcs'), 'coefficient'])
    only = predictions.validate(added, tests = ['dissent'])
    assert set(only['test']) == {'dissent'}
