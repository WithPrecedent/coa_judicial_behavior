"""Adds the scores to the votes as variables for control and prediction.

The studies used the scores in two ways: to describe judges, and to predict
what panels and judges do. The 2010 article predicted whether civil rights
plaintiffs won from the panel's net and median Ideology Scores, the 2012
article predicted dissents and separate concurrences from the Independence
Scores and partisan reversals from the Partisanship Scores, and each
compared the scores with the measures they were meant to improve on (the
party of the appointing president and the Judicial Common Space score).
Each kept the votes that it predicted out of the scores, so that the scores
would not predict the data they came from.

`add_predictors` adds each judge's scores, and those of the judge's panel,
to every vote, with the variables that the studies controlled for or
predicted with. Two techniques, which are added to the `amos` library as
soon as coa_judicial_behavior is imported, use it:

* `score_judges` (an `amos.Operation`) scores the judges from the votes that
  its "train" query selects (all of them, unless one is set), sorts them
  into judging styles, adds the tables of scores and styles to the dataset,
  and adds the predictors to every vote. "holdout" marks the votes that the
  scores were not computed from, which a study can then predict (with the
  "time_split" or "group_split" of amos, or by filtering).
* `validate_scores` (an `amos.Describer`) repeats the studies' tests: probit
  regressions of each outcome on each measure, among the held-out votes.

Contents:
    PREDICTORS: the variables that `add_predictors` adds, with what each
        means.
    ScoreJudges: scores the judges and adds the predictors to the votes.
    ValidateScores: repeats the studies' tests of the scores.
    add_predictors: adds the judges' scores and the variables made from
        them to a table of votes.
    validate: returns the studies' tests of the scores.

"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from typing import Any

import amos
import numpy as np
import pandas as pd

from . import scores as scoring
from . import typology

PREDICTORS: dict[str, str] = {
    'judge_ideology': "The judge's Ideology Score (-100 liberal to 100 conservative).",
    'judge_ideological': 'The absolute value of the Ideology Score.',
    'judge_activism': "The judge's Activism Score (0 to 100).",
    'judge_partisanship': "The judge's Partisanship Score (0 to 100).",
    'judge_independence': "The judge's Independence Score (0 to 100).",
    'judge_style': "The judge's judging style.",
    'judge_scored': 'Whether the judge had enough interactions to define the scales.',
    'colleagues_ideology': "The mean Ideology Score of the judge's copanelists (and so on for each score).",
    'panel_ideology_median': "The median Ideology Score of the panel (the 2010 article's panel measure).",
    'panel_ideology_net': 'The sum of the Ideology Scores of the panel.',
    'panel_activism_mean': 'The mean Activism Score of the panel (and so on for partisanship and independence).',
    'panel_independence_max': 'The highest Independence Score on the panel.',
    'ideological_distance': "How far the judge's Ideology Score is from the copanelists' mean.",
    'circuit_ideology': "The mean Ideology Score of the scored judges of the judge's circuit.",
    'circuit_deviation': "How far the judge's Ideology Score is from the circuit's mean, which predicts separate opinions.",
    'ideological_pressure': 'The Ideology Score (as -1 to 1) times the side of the district judge: positive when a conservative judge reviews a Democratic appointee or a liberal judge a Republican one.',
    'partisan_pressure': 'The centered Partisanship Score (-1 to 1) times 1 if the district judge was appointed by the other party and -1 if by the same.',
    'activist_pressure': 'The centered Activism Score (-1 to 1) under a deferential standard, and 0 otherwise.',
    'expected_reversal': "The rate of reversal of all judges in the vote's super-panel alignment, case type, and standard of review.",
    'concurred_only': 'Whether the judge concurred without dissenting.',
    'holdout': 'Whether the vote was left out of the scores (set by `score_judges`).',
}
_SCORES: tuple[str, ...] = (
    'ideology', 'ideological', 'activism', 'partisanship', 'independence')
_CIVIL_RIGHTS: tuple[str, ...] = (
    'civil_titlevii', 'civil_sec1983', 'civil_ada')


@dataclasses.dataclass
class ScoreJudges(amos.Operation):
    """Scores the judges and adds the predictors to the votes.

    Adds three tables to the dataset: "score_judges" (a row for each judge;
    see `coa_judicial_behavior.scores.score_judges`), "typology" (a row for
    each judging style; see `coa_judicial_behavior.typology.classify`), and
    "typology_differences". The votes get the variables of `PREDICTORS`.

    | Parameter | Meaning |
    | --- | --- |
    | `train` | A query that selects the votes to score the judges from (such as "year <= 2019"), as `pandas.DataFrame.eval` reads it. The others are marked "holdout". Without it, every vote is used. |
    | `method` | "typology" (the 2013 article's methods, the default) or "original" (each score's first article). |
    | `minimum` | Fewest interactions with other judges for a judge to define the scales. It is 200 unless set. |
    | `cell_minimum`, `provoked`, `circuit`, `log_offset`, `by` | See `score_judges`. |
    | `clusters` | The number of judging styles. It is 9 unless set. `styles = false` skips them. |
    | `merge` | Whether to add the predictors to the votes. It is true unless set. |

    """

    def apply(
        self,
        item: amos.Dataset,
        *,
        train: str | None = None,
        method: str = 'typology',
        minimum: int = 200,
        cell_minimum: int = 5,
        provoked: str = 'author',
        circuit: str | None = None,
        log_offset: float = 0.01,
        by: str | None = None,
        clusters: int = 9,
        styles: bool = True,
        merge: bool = True,
        **kwargs: Any) -> amos.Dataset:
        """Scores the judges of the votes in `item`.

        Args:
            item: the dataset of votes (as `review_votes` makes it).
            train: a query that selects the votes to score from. Defaults to
                `None`, in which case every vote is used.
            method: "typology" or "original". Defaults to "typology".
            minimum: fewest interactions for a judge to define the scales.
                Defaults to 200.
            cell_minimum: fewest votes in a cell for a judge's own rate.
                Defaults to 5.
            provoked: "author" or "panel". Defaults to "author".
            circuit: the circuit adjustment, or `None` for each score's own
                under `method`. Defaults to `None`.
            log_offset: what is added before the logarithm of the raw
                Independence Scores. Defaults to 0.01.
            by: name of a column whose values are scored separately.
                Defaults to `None`.
            clusters: the number of judging styles. Defaults to 9.
            styles: whether to sort the judges into styles. Defaults to
                `True`.
            merge: whether to add the predictors to the votes. Defaults to
                `True`.
            **kwargs: not used.

        Returns:
            The dataset, with the tables of scores and styles and, with
                `merge`, the predictors.

        """
        data = item.data
        mask = _selected(data, train)
        table = scoring.score_judges(
            data[mask], method = method, minimum = int(minimum),
            cell_minimum = int(cell_minimum), provoked = provoked,
            circuit = circuit, log_offset = float(log_offset), by = by)
        made = [self.name]
        if _flag(styles):
            table = _classify(table, int(clusters), by, item, made)
        item.tables[self.name] = table
        created: list[str] = []
        if _flag(merge):
            added = add_predictors(data, table, by = by, train = mask)
            added['holdout'] = ~mask.to_numpy()
            created = [c for c in added.columns if c not in data.columns]
            item.replace(added)
        item.record(
            self.name, tables = made, created = created,
            judges = len(table),
            qualified = int(table['qualified'].sum()),
            scored_votes = int(mask.sum()))
        return item


@dataclasses.dataclass
class ValidateScores(amos.Describer):
    """Repeats the studies' tests of the scores.

    Each test is a probit regression of an outcome on one measure at a time,
    with standard errors clustered by case, among the votes left out of the
    scores (see `score_judges`). The table has a row for each test and
    measure (see `validate`). A measure that a study's score was meant to
    improve on (the party of the appointing president, the Judicial Common
    Space score) is tested beside it, so their pseudo-R-squared values can be
    compared, as the studies compared them.

    """

    def describe(
        self,
        item: amos.Dataset,
        *,
        holdout_only: bool = True,
        tests: Sequence[str] | str | None = None,
        **kwargs: Any) -> pd.DataFrame:
        """Returns the tests of the scores.

        Args:
            item: the dataset of votes, with the predictors.
            holdout_only: whether to test only the votes left out of the
                scores (if "holdout" is a column). Defaults to `True`.
            tests: names of the tests to run (see `validate`). Defaults to
                `None`, in which case every test whose columns exist is run.
            **kwargs: not used.

        Returns:
            The table of tests.

        """
        return validate(
            item.data, holdout_only = holdout_only,
            tests = _listify(tests) or None)


def add_predictors(
    votes: pd.DataFrame,
    scores: pd.DataFrame,
    *,
    by: str | None = None,
    train: pd.Series | None = None) -> pd.DataFrame:
    """Adds the judges' scores and the variables made from them to the votes.

    Args:
        votes: a table of votes (see `review_votes`).
        scores: the table of scores (see `score_judges`), with "style" if the
            judges were sorted into styles.
        by: name of the column that the judges were scored separately by, if
            they were. Defaults to `None`.
        train: whether each vote was one that the scores were computed from,
            for "expected_reversal". Defaults to `None`, in which case every
            vote was.

    Returns:
        The votes, with the variables of `PREDICTORS` (except "holdout").

    """
    keys = ['judge_nid', *([by] if by else [])]
    columns = {
        score: f'judge_{score}' for score in _SCORES if score in scores}
    if 'style' in scores.columns:
        columns['style'] = 'judge_style'
    columns['qualified'] = 'judge_scored'
    judged = scores[[*keys, 'circuit', *columns]].rename(columns = columns)
    circuit = (
        judged[judged['judge_scored']]
        .groupby([*([by] if by else []), 'circuit'])['judge_ideology'].mean()
        .rename('circuit_ideology').reset_index())
    judged = judged.merge(circuit, on = [*([by] if by else []), 'circuit'],
                          how = 'left').drop(columns = 'circuit')
    table = votes.drop(
        columns = [c for c in judged.columns if c in votes.columns
                   and c not in keys] + [
            c for c in PREDICTORS if c in votes.columns and c != 'holdout'])
    numbers = pd.to_numeric(table['judge_nid'], errors = 'coerce')
    left = table.assign(judge_nid = numbers.astype('Int64'))
    judged = judged.assign(
        judge_nid = pd.to_numeric(judged['judge_nid']).astype('Int64'))
    merged = left.reset_index().merge(judged, on = keys, how = 'left')
    merged = merged.set_index(votes.index.name or 'index')
    merged.index.name = votes.index.name
    merged['judge_nid'] = votes['judge_nid'].to_numpy()
    merged['judge_scored'] = merged['judge_scored'].fillna(False).astype(bool)
    cases = merged['case_id']
    for score in _SCORES:
        column = f'judge_{score}'
        if column not in merged.columns:
            continue
        values = merged[column].astype('float64')
        total = values.groupby(cases).transform('sum')
        count = values.groupby(cases).transform('count')
        others = count - values.notna()
        merged[f'colleagues_{score}'] = (
            (total - values.fillna(0)) / others).where(others > 0)
    ideology = merged['judge_ideology'].astype('float64')
    merged['panel_ideology_median'] = ideology.groupby(cases).transform(
        'median')
    merged['panel_ideology_net'] = ideology.groupby(cases).transform(
        lambda v: v.sum(min_count = 1))
    for score in ('activism', 'partisanship', 'independence'):
        merged[f'panel_{score}_mean'] = merged[f'judge_{score}'].astype(
            'float64').groupby(cases).transform('mean')
    merged['panel_independence_max'] = merged['judge_independence'].astype(
        'float64').groupby(cases).transform('max')
    merged['ideological_distance'] = (
        ideology - merged['colleagues_ideology']).abs()
    merged['circuit_deviation'] = (ideology - merged['circuit_ideology']).abs()
    district = (
        pd.to_numeric(merged['district_party'], errors = 'coerce')
        if 'district_party' in merged.columns
        else pd.Series(np.nan, index = merged.index))
    merged['ideological_pressure'] = ideology / 100 * -district
    opposed = merged.get('district_opposed')
    side = (
        pd.Series(np.nan, index = merged.index) if opposed is None
        else pd.Series(np.where(
            opposed.astype('boolean').fillna(False), 1.0, -1.0),
            index = merged.index).where(opposed.notna()))
    merged['partisan_pressure'] = (
        (merged['judge_partisanship'] - 50) / 50 * side)
    deferential = (
        merged['review_deferential'].astype('boolean').fillna(False)
        if 'review_deferential' in merged.columns
        else merged['review_standard'] == 'deferential')
    merged['activist_pressure'] = (
        (merged['judge_activism'] - 50) / 50 * deferential.astype(float))
    merged['expected_reversal'] = _expected_reversal(merged, train)
    merged['concurred_only'] = (
        merged['judge_concurred'].astype('boolean').fillna(False)
        & ~merged['judge_dissented'].astype('boolean').fillna(False)).astype(
            bool)
    return merged


def validate(
    votes: pd.DataFrame,
    *,
    holdout_only: bool = True,
    tests: Sequence[str] | None = None) -> pd.DataFrame:
    """Returns the studies' tests of the scores.

    | Test | Rows | Outcome | Measures |
    | --- | --- | --- | --- |
    | `civil_rights` | Cases under Title VII, section 1983, or the ADA whose plaintiff won or lost (2010) | `outcome_civil_plaintiff_won` | The panel's median and net Ideology Scores, its median Judicial Common Space score, and the mean party of its appointing presidents. |
    | `dissent` | Every vote (2012) | `judge_dissented` | The Independence Score, the absolute Ideology Score, and the absolute Judicial Common Space score. |
    | `concurrence` | Every vote (2012) | `concurred_only` | The same. |
    | `partisan_reversal` | Votes under a deferential standard with a district judge of known party (2012) | `vote_reversal` | `partisan_pressure`, `ideological_pressure`, and whether the district judge is of the other party. |
    | `activist_reversal` | Votes under a deferential standard (2011) | `vote_reversal` | The Activism Score. |

    Args:
        votes: the votes, with the predictors (see `add_predictors`).
        holdout_only: whether to test only the votes left out of the scores
            (if "holdout" is a column). Defaults to `True`.
        tests: names of the tests to run. Defaults to `None`, in which case
            every test whose columns exist is run.

    Returns:
        A table with a row for each test and measure: "test", "measure",
            "coefficient", "std_error", "z", "p_value", "pseudo_r2"
            (McFadden's), and "observations". A measure that could not be
            fitted (too few rows or no variation) has missing values.

    """
    data = votes
    if holdout_only and 'holdout' in data.columns and data['holdout'].any():
        data = data[data['holdout'].astype(bool)]
    deferential = (
        data['review_standard'] == 'deferential'
        if 'review_standard' in data.columns
        else pd.Series(False, index = data.index))
    data = data.assign(
        abs_jcs = pd.to_numeric(data['judge_jcs'], errors = 'coerce').abs()
        if 'judge_jcs' in data.columns else np.nan,
        district_other_party = pd.to_numeric(
            data['district_opposed'].astype('Float64'), errors = 'coerce')
        if 'district_opposed' in data.columns else np.nan)
    plans: dict[str, tuple[pd.DataFrame, str, list[str]]] = {}
    present = [c for c in _CIVIL_RIGHTS if c in data.columns]
    if present and 'outcome_civil_plaintiff_won' in data.columns:
        civil = data[data[present].fillna(False).astype(bool).any(axis = 1)]
        if 'judge_jcs' in civil.columns:
            civil = civil.assign(panel_jcs_median = pd.to_numeric(
                civil['judge_jcs'], errors = 'coerce').groupby(
                    civil['case_id']).transform('median'))
        civil = civil.drop_duplicates('case_id')
        plans['civil_rights'] = (
            civil, 'outcome_civil_plaintiff_won',
            ['panel_ideology_median', 'panel_ideology_net',
             'panel_jcs_median', 'panel_party'])
    plans['dissent'] = (
        data, 'judge_dissented',
        ['judge_independence', 'judge_ideological', 'abs_jcs'])
    plans['concurrence'] = (
        data, 'concurred_only',
        ['judge_independence', 'judge_ideological', 'abs_jcs'])
    plans['partisan_reversal'] = (
        data[deferential & data['district_other_party'].notna()],
        'vote_reversal',
        ['partisan_pressure', 'ideological_pressure', 'district_other_party'])
    plans['activist_reversal'] = (
        data[deferential], 'vote_reversal', ['judge_activism'])
    rows = []
    for test, (rows_of, outcome, measures) in plans.items():
        if tests is not None and test not in tests:
            continue
        if outcome not in rows_of.columns:
            continue
        for measure in measures:
            if measure not in rows_of.columns:
                continue
            rows.append({
                'test': test, 'measure': measure,
                **_probit(rows_of, outcome, measure)})
    return pd.DataFrame(rows, columns = [
        'test', 'measure', 'coefficient', 'std_error', 'z', 'p_value',
        'pseudo_r2', 'observations'])


""" Private Functions """


def _classify(
    table: pd.DataFrame,
    clusters: int,
    by: str | None,
    item: amos.Dataset,
    made: list[str]) -> pd.DataFrame:
    """Adds the judging style of each judge to the table of scores.

    Args:
        table: the table of scores.
        clusters: the number of styles.
        by: the column that the judges were scored separately by, if any.
        item: the dataset, to which the tables of styles are added.
        made: the names of the tables added, which is changed in place.

    Returns:
        The table of scores, with "cluster" and "style" for the judges who
            were classified.

    """
    groups = table.groupby(by) if by else [(None, table)]
    found = []
    for value, group in groups:
        try:
            styled = typology.classify(group, clusters)
        except ValueError:
            continue
        suffix = '' if value is None else f'_{value!s}'
        item.tables[f'typology{suffix}'] = styled.profiles
        item.tables[f'typology_differences{suffix}'] = styled.differences
        made.extend([f'typology{suffix}', f'typology_differences{suffix}'])
        found.append(styled.assignments)
    if not found:
        return table
    return table.join(pd.concat(found))


def _expected_reversal(
    votes: pd.DataFrame,
    train: pd.Series | None) -> pd.Series:
    """Returns the rate of reversal of all judges in each vote's situation.

    Args:
        votes: the votes, with "alignment", "type_criminal",
            "review_standard", and "vote_reversal".
        train: whether each vote was one that the scores were computed from,
            or `None` if every vote was.

    Returns:
        The rate of reversal among the training votes of the same alignment,
            case type, and standard of review (or else the same case type and
            standard).

    """
    needed = ('alignment', 'type_criminal', 'review_standard', 'vote_reversal')
    if any(c not in votes.columns for c in needed):
        return pd.Series(np.nan, index = votes.index)
    keys = pd.DataFrame({
        'alignment': votes['alignment'].astype(object),
        'criminal': votes['type_criminal'].astype('boolean').fillna(False),
        'standard': votes['review_standard'].astype(object)},
        index = votes.index)
    reversed_ = pd.Series(
        votes['vote_reversal'].astype('boolean').astype('Float64').to_numpy(
            dtype = 'float64', na_value = np.nan), index = votes.index)
    used = (
        np.ones(len(votes), dtype = bool) if train is None
        else train.to_numpy(dtype = bool))
    known = keys[used].assign(reversed = reversed_[used])
    fine = known.groupby(['alignment', 'criminal', 'standard'])[
        'reversed'].mean()
    coarse = known.groupby(['criminal', 'standard'])['reversed'].mean()
    first = pd.Series(
        fine.reindex(pd.MultiIndex.from_frame(keys)).to_numpy(),
        index = votes.index)
    second = pd.Series(
        coarse.reindex(pd.MultiIndex.from_frame(
            keys[['criminal', 'standard']])).to_numpy(), index = votes.index)
    return first.fillna(second)


def _flag(value: Any) -> bool:
    """Returns a setting as a boolean.

    Args:
        value: a boolean, or text such as "true" or "no".

    Returns:
        Whether the setting is on.

    """
    if isinstance(value, str):
        return value.strip().lower() in {'true', 'yes', 'y', '1', 'on'}
    return bool(value)


def _listify(value: Sequence[str] | str | None) -> list[str]:
    """Returns a setting as a list of names.

    Args:
        value: a name, names separated by commas, a sequence of names, or
            `None`.

    Returns:
        The names.

    """
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(',') if v.strip()]
    return [str(v) for v in value]


def _probit(data: pd.DataFrame, outcome: str, measure: str) -> dict[str, Any]:
    """Returns a probit regression of an outcome on one measure.

    Args:
        data: the rows, with `outcome`, `measure`, and "case_id".
        outcome: name of the outcome, a flag.
        measure: name of the measure.

    Returns:
        The coefficient of the measure, its standard error (clustered by
            case), z statistic, and p-value, McFadden's pseudo-R-squared, and
            the number of observations.

    """
    from statsmodels.discrete.discrete_model import Probit  # noqa: PLC0415

    y = pd.to_numeric(
        data[outcome].astype('boolean').astype('Float64'), errors = 'coerce')
    x = pd.to_numeric(data[measure], errors = 'coerce')
    usable = y.notna() & x.notna()
    empty = {
        'coefficient': np.nan, 'std_error': np.nan, 'z': np.nan,
        'p_value': np.nan, 'pseudo_r2': np.nan,
        'observations': int(usable.sum())}
    if usable.sum() < 30 or x[usable].nunique() < 2 or y[usable].nunique() < 2:
        return empty
    design = np.column_stack([
        np.ones(int(usable.sum())), x[usable].to_numpy(dtype = 'float64')])
    groups = pd.factorize(data.loc[usable, 'case_id'])[0]
    try:
        fitted = Probit(y[usable].to_numpy(dtype = 'float64'), design).fit(
            disp = False, cov_type = 'cluster', cov_kwds = {'groups': groups})
    except (np.linalg.LinAlgError, ValueError):
        return empty
    return {
        'coefficient': float(fitted.params[1]),
        'std_error': float(fitted.bse[1]),
        'z': float(fitted.tvalues[1]),
        'p_value': float(fitted.pvalues[1]),
        'pseudo_r2': float(fitted.prsquared),
        'observations': int(usable.sum())}


def _selected(data: pd.DataFrame, query: str | None) -> pd.Series:
    """Returns which rows a query selects.

    Args:
        data: the rows.
        query: the query, as `pandas.DataFrame.eval` reads it, or `None`.

    Raises:
        ValueError: if the query does not return a flag for each row.

    Returns:
        Whether each row is selected (every row, without a query).

    """
    if not query:
        return pd.Series(True, index = data.index)
    selected = data.eval(query)
    if (
        not isinstance(selected, pd.Series)
        or len(selected) != len(data)
        or not pd.api.types.is_bool_dtype(selected.dtype)):
        message = f'the query {query!r} must select rows of the votes'
        raise ValueError(message)
    return selected.astype('boolean').fillna(False).astype(bool)
