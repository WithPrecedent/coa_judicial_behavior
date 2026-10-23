"""Runs the study on fictional appeals."""

from __future__ import annotations

import pathlib

import chrisjen
import courtpy
from conftest import write_cases

import coa_judicial_behavior

STUDIES = pathlib.Path(__file__).parents[1] / 'studies'


def test_judicial_behavior_study(
    roster: courtpy.judges.Roster,
    tmp_path: pathlib.Path) -> None:
    # Judge Kay of the First Circuit reverses as often under deferential
    # standards as under de novo review.
    write_cases(tmp_path / 'data' / 'court_listener', 600, activist = 'Kay')
    idea = chrisjen.Idea.create(STUDIES / 'judicial_behavior.toml')
    loader = idea['load_court_listener_parameters']
    loader['download'] = 'none'
    loader['workers'] = 1
    loader['rulebooks'] = (
        f'federal, {coa_judicial_behavior.RULEBOOK.as_posix()}')
    idea['score_judges_parameters']['train'] = 'year <= 2015'
    idea['score_judges_parameters']['minimum'] = 100
    idea['score_judges_parameters']['clusters'] = 3
    idea['random_forest_parameters']['n_estimators'] = 20
    # Eleven fictional judges cannot tell apart as many attributes of
    # judges as the study uses, which would make the probit model singular,
    # so only a few are kept.
    idea['keep_columns_parameters']['columns'] = [
        'judge_ideology', 'judge_activism', 'judge_partisanship',
        'judge_independence', 'colleagues_ideology', 'partisan_pressure',
        'activist_pressure', 'ideological_pressure', 'expected_reversal',
        'type_criminal', 'review_deferential', 'review_de_novo',
        'district_party', 'court_num', 'year']
    idea['group_k_fold_parameters']['n_splits'] = 3
    project = coa_judicial_behavior.Project.create(idea, clerk = tmp_path)
    result = project.result
    assert result.label == 'vote_reversal'
    techniques = [entry['technique'] for entry in result.history]
    assert techniques[:8] == [
        'load_court_listener', 'code_parties', 'code_case_type',
        'code_outcome', 'code_judges', 'code_politics',
        'code_district_judge', 'code_review']
    assert {'review_votes', 'score_judges', 'validate_scores'} <= set(
        techniques)
    assert (tmp_path / 'data' / 'appeals.parquet').is_file()
    # Every fictional appeal has three judges in the roster, so each has
    # three votes.
    assert len(result.data) == 1800
    tables = result.tables
    scored = tables['score_judges'].set_index('judge')
    assert len(scored) == 11
    assert scored['qualified'].all()
    # Every district judge was found, so every vote has its super-panel.
    assert scored['district_interactions'].sum() == scored['votes'].sum()
    # The judge who does not defer is the most activist of the First
    # Circuit.
    first = scored[scored['circuit'] == 1]
    assert first['activism'].idxmax().startswith('Kay')
    # Republican appointees reverse Democratic district judges, so they are
    # conservative.
    assert (
        scored.loc[scored['judge_party'] == 1, 'ideology'].mean()
        > scored.loc[scored['judge_party'] == -1, 'ideology'].mean())
    assert len(tables['typology']) == 3
    tests = tables['validate_scores']
    assert {'dissent', 'partisan_reversal', 'civil_rights'} <= set(
        tests['test'])
    assert {
        'summarize', 'fixest_coefficients', 'analyst_comparison',
        'scorecard', 'permutation_importance'} <= set(tables)
    assert 'judge_activism' in tables['fixest_coefficients'].index
    assert 'roc_curve' in result.figures
    assert 0 <= result.metrics['roc_auc'] <= 1
    folder = project.export()
    assert (folder / 'tables' / 'score_judges.csv').is_file()
