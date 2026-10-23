"""Tests the rules and techniques that make the votes."""

from __future__ import annotations

import courtpy
import numpy as np
import pandas as pd
import pytest

from coa_judicial_behavior import votes

OPENINGS: dict[str, tuple[str, list[str]]] = {
    'fourth': (
        'Appeal from the United States District Court for the District of '
        'Maryland, at Baltimore. Catherine C. Blake, District Judge. '
        '(1:17-cr-00123-CCB)', ['CATHERINE C BLAKE']),
    'second': (
        'Appeal from a judgment of the United States District Court for the '
        'Southern District of New York (Hon. Lewis A. Kaplan, Judge).',
        ['LEWIS A KAPLAN']),
    'ninth': (
        'Appeal from the United States District Court for the Central '
        'District of California Dean D. Pregerson, District Judge, '
        'Presiding', ['DEAN D PREGERSON']),
    'third': (
        'On Appeal from the United States District Court for the District '
        'of New Jersey (D.C. No. 3-07-cr-00123) District Judge: Honorable '
        'Joel A. Pisano', ['JOEL A PISANO']),
    'seventh': (
        'Appeal from the United States District Court for the Northern '
        'District of Illinois, Eastern Division. No. 1:19-cv-01234 '
        + chr(0x2014) + ' John Z. Lee, Judge.', ['JOHN Z LEE']),
    'designated': (
        'Before SMITH and JONES, Circuit Judges, and Mary Doe, District '
        'Judge, sitting by designation. Appeal from the United States '
        'District Court for the District of Maine [Hon. John A. Woodcock, '
        'Jr., U.S. District Judge]', ['JOHN A WOODCOCK', 'JR']),
    'starred': (
        'Before SMITH and JONES, Circuit Judges, and DOE,* District Judge. '
        'Appeal from the United States District Court for the Eastern '
        'District of Michigan at Detroit. No. 2:18-cr-20012' + chr(0x2014)
        + 'Judith E. Levy, District Judge.', ['JUDITH E LEVY'])}


@pytest.fixture(scope = 'module')
def rulebook() -> courtpy.Rulebook:
    """Returns the project's rules."""
    return courtpy.Rulebook.load(votes.RULEBOOK)


@pytest.mark.parametrize('circuit', sorted(OPENINGS))
def test_rules_find_district_judge(
    rulebook: courtpy.Rulebook,
    circuit: str) -> None:
    text, names = OPENINGS[circuit]
    found = rulebook.apply({'opening_lines': text, 'opinion': ''})
    assert found['district_judges'] == names
    assert found['review_district']
    assert not found['review_agency']


def test_rules_find_review(rulebook: courtpy.Rulebook) -> None:
    found = rulebook.apply({
        'opening_lines': (
            'On Petition for Review of an Order of the Board of Immigration '
            'Appeals'),
        'opinion': 'We review for substantial evidence and for plain error.'})
    assert found['review_agency']
    assert found['review_immigration']
    assert not found['review_district']
    assert found['district_judges'] == []
    assert found['standard_substantial_evidence']
    assert found['standard_plain_error']
    assert found['standard_named']


def test_code_review() -> None:
    cases = pd.DataFrame({
        'standard_de_novo': [True, False, True, False, False],
        'standard_abuse_disc': [False, True, True, False, False],
        'standard_named': [False, False, False, True, False],
        'civil_habeas': [False, False, False, False, True],
        'review_district': [True, True, False, True, True],
        'review_agency': [False, False, True, False, False]})
    coded = votes.CodeReview().munge(cases.copy())
    assert coded['review_standard'].tolist() == [
        'non_deferential', 'deferential', 'unclear', 'unclear', 'unclear']
    assert coded['review_has_standard'].tolist() == [
        True, True, True, True, False]
    assert coded['review_excluded'].tolist() == [
        False, False, False, False, True]
    assert coded['review_of_district'].tolist() == [
        True, True, False, True, True]
    assert coded['review_deferential'].sum() == 1
    with pytest.raises(KeyError, match = 'standards of review'):
        votes.CodeReview().munge(pd.DataFrame({'x': [1]}))


def test_code_district_judge(roster: courtpy.judges.Roster) -> None:
    cases = pd.DataFrame({
        'district_judges': [
            ['DANA P WOODS'], ['THOMAS E LYNCH'], 'ANA L ORTIZ',
            ['NOBODY HERE'], [], ['DANA P WOODS']],
        'court_num': [1, 1, 9, 1, 1, 9],
        'year': [2015] * 6,
        'judge1_nid': [101, 101, 201, 101, 101, 201]})
    coded = votes.CodeDistrictJudge().munge(cases.copy(), roster = roster)
    # Judge Lynch of the district court is found, although a judge of the
    # court of appeals has the same last name, and a district judge of
    # another circuit is not.
    assert coded['district_judge_nid'].tolist()[:3] == [301, 304, 401]
    assert coded['district_judge_nid'].isna().tolist()[3:] == [True] * 3
    assert coded['district_party'].tolist()[:3] == [-1.0, 1.0, -1.0]
    assert coded['district_jcs'].tolist()[:3] == [-0.3, 0.4, -0.4]
    assert coded['district_judge'][0].startswith('Woods')
    # A judge who sat on the panel is not the district judge.
    sat = cases.iloc[[0]].assign(judge2_nid = 301)
    assert votes.CodeDistrictJudge().munge(
        sat, roster = roster)['district_judge_nid'].isna().all()


def test_describe_panels() -> None:
    table = pd.DataFrame({
        'case_id': ['a', 'a', 'a', 'b', 'b', 'b'],
        'judge_party': [1.0, 1.0, -1.0, -1.0, np.nan, 1.0],
        'judge_dissented': [False, False, True, False, False, False],
        'district_party': [-1.0, -1.0, -1.0, 1.0, 1.0, 1.0]})
    described = votes.describe_panels(table)
    assert described['copanel'].tolist()[:3] == ['DR', 'DR', 'RR']
    assert described['alignment'].tolist()[:3] == ['DR-D', 'DR-D', 'RR-D']
    # A copanelist of unknown party leaves the alignment unknown, but the
    # judge of unknown party has two copanelists who are known.
    assert described['alignment'][[3, 5]].isna().all()
    assert described['alignment'][4] == 'DR-R'
    assert described['district_opposed'].tolist()[:3] == [True, True, False]
    assert pd.isna(described['district_opposed'][4])
    assert described['panel_unanimous'].tolist() == [False] * 3 + [True] * 3
