"""Scores the ideology, activism, partisanship, and independence of judges.

The four scores follow the methods of Corey Rayburn Yung's studies of the
judges of the federal courts of appeals:

* **Ideology**: *Judged by the Company You Keep: An Empirical Study of the
  Ideologies of Judges on the United States Courts of Appeals*, 51 B.C. L.
  Rev. 1133 (2010).
* **Activism**: *Flexing Judicial Muscle: An Empirical Study of Judicial
  Activism in the Federal Courts*, 105 Nw. U. L. Rev. 1 (2011).
* **Partisanship and independence**: *Beyond Ideology: An Empirical Study of
  Partisanship and Independence in the Federal Courts*, 80 Geo. Wash. L.
  Rev. 505 (2012).
* **All four, revised together**: *A Typology of Judging Styles*, 107 Nw. U.
  L. Rev. 1757 (2013).

Each score is computed from a table of votes, with one row for each judge on
each case (see `coa_judicial_behavior.votes`), in three steps: a raw score
from rates of agreement and reversal, adjustments for what the judge could
not choose (the mix of criminal and civil cases, the parties of the other
judges of the "super-panel", and the circuit), and a common scale.

**Ideology** is an "agnostic" measure: judges who think alike vote together.
Every judge is first given the party of the president who appointed the
judge (-1 for a Democrat and 1 for a Republican), and the judge being scored
is a blank slate. The Panel Score is the judge's rate of agreement with
copanelists appointed by Republicans less the rate with those appointed by
Democrats, and the District Score is the same for the district judges whose
judgments the judge affirmed (an affirmance is an agreement and a reversal a
disagreement). The District Score weights each standard of review by how
rarely judgments are reversed under it, since affirming under a deferential
standard says less about a judge than reversing under one:

    Panel Score = sum over case types t of
        share(t) * (RateAgree(Rep, t) - RateAgree(Dem, t))
    District Score = sum over t of share(t) * sum over standards s of
        w(t, s) * (RateAffirm(Rep, t, s) - RateAffirm(Dem, t, s))

where `share(t)` is the average judge's share of criminal or civil cases and
`w(t, s)` is proportional to the judge's votes under each standard times the
inverse of the rate of reversal under it (normalized to sum to one within
each case type, which keeps the District Score on the scale of the Panel
Score, as the 2010 article sought by halving its sum).

**Activism** is the difference between how often a judge reversed under
deferential standards of review and under de novo review. The de novo rate
is the baseline that removes reversals for ideological or other reasons, so
what is left is how often the judge failed to defer when the formal model of
law says that the judge should have:

    Activism Differential = sum over t of share(t) *
        (ReversalRate(deferential, t) - ReversalRate(de novo, t))

**Partisanship** is whether a judge applied the same neutral rule (the
standard of review) differently to district judges appointed by the two
parties. It is signed by the judge's own party, so that a Democratic
appointee who favored Republican district judges is not partisan:

    Partisanship = sum over t of share(t) *
        ((DeferentialReversal(other party, t) - DeferentialReversal(own party, t))
         - (NondeferentialReversal(other party, t) - NondeferentialReversal(own party, t)))

**Independence** is how often a judge provoked disagreements (dissents and
separate concurrences, by the judge or by a copanelist against the judge's
opinion) beyond what ideological differences predict. The expected rates are
the fitted values of a linear regression, across the judges scored, of the
rates on how far each judge's ideology is from the mean of the judge's
circuit:

    Independence = DissentRate + ConcurrenceRate
        - ExpectedDissentRate - ExpectedConcurrenceRate

A concurrence in part and dissent in part counts as a dissent only.

The adjustments:

* **Case mix.** Every rate is computed separately for criminal and civil
  cases and weighted by the average judge's shares (`share(t)`). When a
  judge has too few votes in a cell (fewer than `cell_minimum`), the
  judge's rate in both kinds of cases is used, and else the rate of all
  judges, which is how the studies "interpolated" thin cells.
* **Super-panel effects.** The parties of a judge's copanelists and of the
  district judge change how the judge votes. Each vote's super-panel is one
  of six alignments ("RR-R", "RR-D", "DR-R", "DR-D", "DD-R", and "DD-D").
  The score that a blank-slate judge would have from the alignments that
  the judge happened to sit in (computed with the rates of all judges in
  each alignment, so that offsetting alignments cancel) is subtracted.
* **Circuit.** Judges who sat in more than one circuit are assumed to keep
  their traits, so how their scores differ from circuit to circuit measures
  the circuits. For each circuit, the traveling judges' votes there are
  scored together, as one hypothetical judge, and compared with their
  overall scores weighted by their votes there. The difference is the
  circuit's differential, which is subtracted from the judges of the
  circuit: divided by twice the number of judges of the circuit ("per
  judge", as the 2010 and 2011 articles did) or by the number of traveling
  votes in the circuit and multiplied by the judge's votes there ("per
  vote", as the 2012 and 2013 articles did). "full" subtracts the whole
  differential, weighted by the judge's votes in each circuit, which is not
  in the articles.
* **Scale.** The judges with at least `minimum` interactions with other
  judges (two copanelists and a district judge on each vote; the studies
  required 200) define the scale. Activism, partisanship, and independence
  run from 0 to 100, and ideology from -100 (liberal) to 100
  (conservative). Independence is placed on a logarithmic scale first.

The 2013 article revised the earlier methods. `method = "typology"` (the
default) follows it, and `method = "original"` follows each score's first
article:

| Choice | "original" | "typology" |
| --- | --- | --- |
| Panel and District Scores | Added (2010). | Weighted by the rate of disagreement at each level. |
| Zero of the Ideology Score | The judge whose rank is the number of Democratic appointees (2010). | Equal agreement with both parties (no shift). |
| Super-panel effects | Ideology and partisanship. | Ideology, activism, and partisanship. |
| Circuit adjustment | Per judge for ideology and activism (2010, 2011), per vote for partisanship (2012). | Per vote for all three. |
| Independence's expected rates | From the scaled Ideology Score (2012). | From the adjusted raw Ideology Score. |

Independence has no circuit adjustment in either, because judges seldom
write separately when they travel.

Contents:
    METHODS: the versions of the methods.
    SCORES: the names of the four scores.
    score_judges: returns the four scores of every judge in a table of
        votes.

"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
import pandas as pd

METHODS: tuple[str, ...] = ('typology', 'original')
SCORES: tuple[str, ...] = (
    'ideology', 'activism', 'partisanship', 'independence')
_CASE_TYPES: tuple[bool, ...] = (False, True)
_CIRCUIT_METHODS: tuple[str, ...] = ('per_judge', 'per_vote', 'full', 'none')
_PARTIES: tuple[float, ...] = (-1.0, 1.0)
_PROVOKED: tuple[str, ...] = ('author', 'panel')
_REVIEWED: tuple[str, ...] = ('deferential', 'non_deferential')
_STANDARDS: tuple[str, ...] = ('deferential', 'non_deferential', 'unclear')
# The circuit adjustment of each score under each method.
_CIRCUIT: dict[str, dict[str, str]] = {
    'original': {
        'ideology': 'per_judge', 'activism': 'per_judge',
        'partisanship': 'per_vote'},
    'typology': {
        'ideology': 'per_vote', 'activism': 'per_vote',
        'partisanship': 'per_vote'}}
# The pooled votes of the traveling judges in a circuit are scored as one
# hypothetical judge with this number.
_TRAVELER: int = -1

Scorer = Callable[[pd.DataFrame, pd.DataFrame], pd.Series]


@dataclasses.dataclass
class _Context:
    """What every judge's scores are compared with.

    Args:
        votes: every vote, as `_prepare` returns it.
        pairs: every pair of a vote and a copanelist, as `_prepare` returns
            it.
        shares: the average judge's share of civil (`False`) and criminal
            (`True`) cases.
        weights: the weight of each standard of review in the District Score,
            by case type and standard: the inverse of the rate of reversal
            under it, normalized within each case type.
        panel_disagreement: the rate at which copanelists disagreed.
        district_disagreement: the rate at which district judges were
            reversed.
        minimum: fewest votes in a cell for a judge's own rate to be used.

    """

    votes: pd.DataFrame
    pairs: pd.DataFrame
    shares: dict[bool, float]
    weights: pd.Series
    panel_disagreement: float
    district_disagreement: float
    minimum: int

    @classmethod
    def create(
        cls,
        votes: pd.DataFrame,
        pairs: pd.DataFrame,
        minimum: int) -> _Context:
        """Returns the context of a table of votes.

        Args:
            votes: every vote, as `_prepare` returns it.
            pairs: every pair, as `_prepare` returns it.
            minimum: fewest votes in a cell for a judge's own rate to be
                used.

        Returns:
            The context.

        """
        per_judge = votes.groupby('unit')['criminal'].mean()
        criminal = float(per_judge.mean()) if len(per_judge) else 0.0
        shares = {False: 1 - criminal, True: criminal}
        district = votes[votes['district_party'].notna()]
        rates = district.groupby(['criminal', 'standard'])['reversed'].mean()
        index = pd.MultiIndex.from_product(
            [_CASE_TYPES, _STANDARDS], names = ['criminal', 'standard'])
        overall = district['reversed'].mean()
        rates = rates.reindex(index).fillna(
            overall if pd.notna(overall) else 0.5)
        inverse = 1 / rates.clip(lower = 1e-6)
        weights = inverse / inverse.groupby(level = 'criminal').transform(
            'sum')
        agreement = pairs['agree'].mean()
        return cls(
            votes = votes,
            pairs = pairs,
            shares = shares,
            weights = weights,
            panel_disagreement = (
                0.0 if pd.isna(agreement) else 1 - float(agreement)),
            district_disagreement = (
                0.0 if pd.isna(overall) else float(overall)),
            minimum = minimum)


def score_judges(
    votes: pd.DataFrame,
    *,
    method: str = 'typology',
    minimum: int = 200,
    cell_minimum: int = 5,
    provoked: str = 'author',
    circuit: str | None = None,
    log_offset: float = 0.01,
    by: str | None = None) -> pd.DataFrame:
    """Returns the four scores of every judge in a table of votes.

    Args:
        votes: a table of votes, with one row for each judge on each case,
            as `review_votes` makes it. It needs "case_id", "judge_nid",
            "judge_party", "court_num", "type_criminal", "review_standard",
            "vote_reversal", "judge_dissented", "judge_concurred",
            "judge_author", "district_party", and "alignment". "judge" and
            "judge_designated" are used if they are there.
        method: "typology" (the 2013 article's methods) or "original" (each
            score's first article). Defaults to "typology".
        minimum: fewest interactions with other judges for a judge to define
            the scales. Defaults to 200, as in the studies.
        cell_minimum: fewest votes in a cell (such as criminal cases under a
            deferential standard) for the judge's own rate in it to be used.
            Defaults to 5.
        provoked: whose separate opinions count toward a judge's
            independence besides the judge's own: "author" (those against
            the opinion that the judge wrote, as the 2012 article describes)
            or "panel" (those against any majority that the judge joined).
            Defaults to "author".
        circuit: the circuit adjustment of ideology, activism, and
            partisanship: "per_judge", "per_vote", "full", or "none".
            Defaults to `None`, in which case each score's adjustment under
            `method` is used.
        log_offset: what is added to the shifted raw Independence Scores
            before their logarithm is taken, so that the lowest is not zero.
            Defaults to 0.01 (one percentage point).
        by: name of a column (such as "year") whose values are scored
            separately, as the studies scored one year. Defaults to `None`,
            in which case every vote is scored together.

    Raises:
        ValueError: if `method`, `provoked`, or `circuit` is not one of its
            choices.
        KeyError: if `votes` lacks a column that is needed.

    Returns:
        A table with a row for each judge (and value of `by`), sorted from
            the most liberal Ideology Score. Its columns are described in the
            documentation of the project.

    """
    _check(method, METHODS, 'method')
    _check(provoked, _PROVOKED, 'provoked')
    if circuit is not None:
        _check(circuit, _CIRCUIT_METHODS, 'circuit')

    def score(frame: pd.DataFrame) -> pd.DataFrame:
        return _score(
            frame, method = method, minimum = int(minimum),
            cell_minimum = int(cell_minimum), provoked = provoked,
            circuit = circuit, log_offset = float(log_offset))

    if by is None:
        return score(votes)
    tables = []
    for value, group in votes.groupby(by, sort = True):
        table = score(group)
        table.insert(1, by, value)
        tables.append(table)
    return pd.concat(tables, ignore_index = True)


""" Scores """


def _score(
    votes: pd.DataFrame,
    *,
    method: str,
    minimum: int,
    cell_minimum: int,
    provoked: str,
    circuit: str | None,
    log_offset: float) -> pd.DataFrame:
    """Returns the four scores of every judge in one table of votes.

    Args:
        votes: the votes.
        method: "typology" or "original".
        minimum: fewest interactions for a judge to define the scales.
        cell_minimum: fewest votes in a cell for a judge's own rate.
        provoked: "author" or "panel".
        circuit: the circuit adjustment, or `None` for each score's own.
        log_offset: what is added before the logarithm of independence.

    Returns:
        The table of scores.

    """
    prepared, pairs = _prepare(votes, provoked)
    context = _Context.create(prepared, pairs, cell_minimum)
    table = _judges(prepared, pairs, minimum)
    qualified = table['qualified']
    adjustments = {
        score: circuit or _CIRCUIT[method][score]
        for score in ('ideology', 'activism', 'partisanship')}

    def ideology(v: pd.DataFrame, p: pd.DataFrame) -> pd.Series:
        observed = _ideology(v, p, context, method)['raw']
        expected = _ideology(v, p, context, method, expected = True)['raw']
        return observed - expected

    parts = _ideology(prepared, pairs, context, method)
    expected = _ideology(prepared, pairs, context, method, expected = True)
    table['ideology_panel'] = _by_judge(table, parts['panel'])
    table['ideology_district'] = _by_judge(table, parts['district'])
    table['ideology_raw'] = _by_judge(table, parts['raw'])
    table['ideology_super_panel'] = _by_judge(table, expected['raw'])
    _adjust(
        table, 'ideology', ideology, votes = prepared, pairs = pairs,
        adjustments = adjustments)
    table['ideology'] = _scale_signed(
        table['ideology_adjusted'], qualified, table['judge_party'],
        center = method == 'original')
    table['ideological'] = table['ideology'].abs()

    super_panel = method == 'typology'

    def activism(v: pd.DataFrame, _pairs: pd.DataFrame) -> pd.Series:
        observed = _activism(v, context)
        if not super_panel:
            return observed
        return observed - _activism(v, context, expected = True)

    table['activism_raw'] = _by_judge(table, _activism(prepared, context))
    table['activism_super_panel'] = (
        _by_judge(table, _activism(prepared, context, expected = True))
        if super_panel else 0.0)
    _adjust(
        table, 'activism', activism, votes = prepared, pairs = pairs,
        adjustments = adjustments)
    table['activism'] = _scale_unit(table['activism_adjusted'], qualified)

    def partisanship(v: pd.DataFrame, _pairs: pd.DataFrame) -> pd.Series:
        return (
            _partisanship(v, context)
            - _partisanship(v, context, expected = True))

    table['partisanship_raw'] = _by_judge(
        table, _partisanship(prepared, context))
    table['partisanship_super_panel'] = _by_judge(
        table, _partisanship(prepared, context, expected = True))
    _adjust(
        table, 'partisanship', partisanship, votes = prepared,
        pairs = pairs, adjustments = adjustments)
    table['partisanship'] = _scale_unit(
        table['partisanship_adjusted'], qualified)

    measure = (
        table['ideology_adjusted'] if method == 'typology'
        else table['ideology'])
    _independence(table, prepared, context, measure, log_offset)
    return table.sort_values('ideology').reset_index(drop = True)


def _activism(
    votes: pd.DataFrame,
    context: _Context,
    *,
    expected: bool = False) -> pd.Series:
    """Returns each judge's raw Activism Differential.

    Args:
        votes: the votes to score, with "unit".
        context: what the judges are compared with.
        expected: whether to score the reversals that a blank-slate judge
            would make in each vote's super-panel instead of the judge's.
            Defaults to `False`.

    Returns:
        The differential of each judge (or "unit").

    """
    value = 'expected_reversed' if expected else 'reversed'
    reviewed = votes[
        votes['standard'].isin(_REVIEWED) & votes['reversed'].notna()]
    reference = context.votes[
        context.votes['standard'].isin(_REVIEWED)
        & context.votes['reversed'].notna()]
    rates, _ = _cell_rates(
        reviewed, reference, value, ['criminal', 'standard'],
        [list(_CASE_TYPES), list(_REVIEWED)], minimum = context.minimum)
    score = pd.Series(0.0, index = votes['unit'].unique())
    for kind in _CASE_TYPES:
        difference = (
            _cell(rates, criminal = kind, standard = 'deferential')
            - _cell(rates, criminal = kind, standard = 'non_deferential'))
        score = score.add(context.shares[kind] * difference, fill_value = 0)
    return score


def _ideology(
    votes: pd.DataFrame,
    pairs: pd.DataFrame,
    context: _Context,
    method: str,
    *,
    expected: bool = False) -> pd.DataFrame:
    """Returns each judge's Panel, District, and raw Ideology Scores.

    Args:
        votes: the votes to score, with "unit".
        pairs: the pairs of votes and copanelists.
        context: what the judges are compared with.
        method: "typology" or "original".
        expected: whether to score the agreements that a blank-slate judge
            would have in each vote's super-panel instead of the judge's.
            Defaults to `False`.

    Returns:
        A table with a row for each judge (or "unit") and the columns
            "panel", "district", and "raw".

    """
    units = pd.Index(votes['unit'].unique())
    together = _paired(pairs, votes)
    value = 'expected_agree' if expected else 'agree'
    rates, _ = _cell_rates(
        together, context.pairs, value, ['criminal', 'colleague_party'],
        [list(_CASE_TYPES), list(_PARTIES)], minimum = context.minimum)
    panel = pd.Series(0.0, index = units)
    for kind in _CASE_TYPES:
        difference = (
            _cell(rates, criminal = kind, colleague_party = 1.0)
            - _cell(rates, criminal = kind, colleague_party = -1.0))
        panel = panel.add(context.shares[kind] * difference, fill_value = 0)
    reviewed = votes[
        votes['district_party'].notna() & votes['affirmed'].notna()]
    reference = context.votes[
        context.votes['district_party'].notna()
        & context.votes['affirmed'].notna()]
    value = 'expected_affirmed' if expected else 'affirmed'
    district = pd.Series(0.0, index = units)
    if len(reviewed):
        rates, counts = _cell_rates(
            reviewed, reference, value,
            ['criminal', 'standard', 'district_party'],
            [list(_CASE_TYPES), list(_STANDARDS), list(_PARTIES)],
            minimum = context.minimum)
        numbers = counts.groupby(
            level = ['unit', 'criminal', 'standard']).sum()
        overall = reference.groupby(['criminal', 'standard']).size()
        for kind in _CASE_TYPES:
            total = pd.Series(0.0, index = rates.index.unique('unit'))
            weight = pd.Series(0.0, index = total.index)
            fallback_total = pd.Series(0.0, index = total.index)
            fallback_weight = 0.0
            for standard in _STANDARDS:
                difference = (
                    _cell(rates, criminal = kind, standard = standard,
                          district_party = 1.0)
                    - _cell(rates, criminal = kind, standard = standard,
                            district_party = -1.0))
                w = float(context.weights[(kind, standard)])
                n = _cell(numbers, criminal = kind, standard = standard)
                total = total.add(w * n * difference, fill_value = 0)
                weight = weight.add(w * n, fill_value = 0)
                n_all = float(overall.get((kind, standard), 0))
                fallback_total = fallback_total.add(
                    w * n_all * difference, fill_value = 0)
                fallback_weight += w * n_all
            within = (total / weight).where(weight > 0)
            if fallback_weight > 0:
                within = within.fillna(fallback_total / fallback_weight)
            district = district.add(
                context.shares[kind] * within.fillna(0), fill_value = 0)
    if method == 'typology':
        levels = context.panel_disagreement + context.district_disagreement
        raw = (
            (context.panel_disagreement * panel
             + context.district_disagreement * district) / levels
            if levels > 0 else panel + district)
    else:
        raw = panel + district
    return pd.DataFrame({'panel': panel, 'district': district, 'raw': raw})


def _independence(
    table: pd.DataFrame,
    votes: pd.DataFrame,
    context: _Context,
    ideology: pd.Series,
    log_offset: float) -> None:
    """Adds each judge's Independence Score to the table of scores.

    Args:
        table: the table of scores, with "judge_nid", "circuit", and
            "qualified". It is changed in place.
        votes: every vote, with "unit".
        context: what the judges are compared with.
        ideology: the measure of each judge's ideology (in the order of
            `table`) whose distance from the circuit's mean predicts the
            judge's separate opinions.
        log_offset: what is added before the logarithm is taken.

    """
    units = table['judge_nid']
    qualified = table['qualified'].to_numpy()
    measure = pd.Series(ideology.to_numpy(), index = units)
    circuits = pd.Series(table['circuit'].to_numpy(), index = units)
    means = measure[qualified].groupby(circuits[qualified]).mean()
    deviation = (measure - circuits.map(means)).abs()
    deviation = deviation.fillna(deviation[qualified].mean())
    raw = pd.Series(0.0, index = units)
    for column, kind in (
        ('dissent_events', 'dissent'), ('concurrence_events', 'concurrence')):
        rates, _ = _cell_rates(
            votes, context.votes, column, ['criminal'],
            [list(_CASE_TYPES)], minimum = context.minimum)
        observed = pd.Series(0.0, index = units)
        predicted = pd.Series(0.0, index = units)
        for case_type in _CASE_TYPES:
            rate = _cell(rates, criminal = case_type).reindex(units)
            fitted = _fit(deviation, rate, qualified)
            observed += context.shares[case_type] * rate.fillna(0)
            predicted += context.shares[case_type] * fitted
        table[f'{kind}_rate'] = observed.to_numpy()
        table[f'expected_{kind}_rate'] = predicted.to_numpy()
        raw += observed - predicted
    table['independence_raw'] = raw.to_numpy()
    lowest = raw[qualified].min() if qualified.any() else raw.min()
    shifted = (raw - lowest + log_offset).clip(lower = log_offset / 10)
    table['independence_log'] = np.log(shifted.to_numpy(dtype = 'float64'))
    table['independence'] = _scale_unit(
        table['independence_log'], table['qualified'])


def _partisanship(
    votes: pd.DataFrame,
    context: _Context,
    *,
    expected: bool = False) -> pd.Series:
    """Returns each judge's raw Partisanship Score.

    Args:
        votes: the votes to score, with "unit".
        context: what the judges are compared with.
        expected: whether to score the reversals that a blank-slate judge
            would make in each vote's super-panel instead of the judge's.
            Defaults to `False`.

    Returns:
        The score of each judge (or "unit").

    """
    value = 'expected_reversed' if expected else 'reversed'

    def usable(frame: pd.DataFrame) -> pd.DataFrame:
        return frame[
            frame['standard'].isin(_REVIEWED) & frame['reversed'].notna()
            & frame['copartisan'].notna()].astype({'copartisan': bool})

    rates, _ = _cell_rates(
        usable(votes), usable(context.votes), value,
        ['criminal', 'standard', 'copartisan'],
        [list(_CASE_TYPES), list(_REVIEWED), [False, True]],
        minimum = context.minimum)
    score = pd.Series(0.0, index = votes['unit'].unique())
    for kind in _CASE_TYPES:
        cells = {
            (standard, same): _cell(
                rates, criminal = kind, standard = standard,
                copartisan = same)
            for standard in _REVIEWED for same in (False, True)}
        difference = (
            (cells['deferential', False] - cells['deferential', True])
            - (cells['non_deferential', False]
               - cells['non_deferential', True]))
        score = score.add(context.shares[kind] * difference, fill_value = 0)
    return score


""" Adjustments """


def _adjust(
    table: pd.DataFrame,
    score: str,
    scorer: Scorer,
    *,
    votes: pd.DataFrame,
    pairs: pd.DataFrame,
    adjustments: dict[str, str]) -> None:
    """Adds a score's circuit adjustment and adjusted value to the table.

    Args:
        table: the table of scores, with "{score}_raw" and
            "{score}_super_panel". It is changed in place.
        score: the name of the score.
        scorer: returns the super-panel-adjusted score of each "unit" of
            votes.
        votes: every vote.
        pairs: every pair of a vote and a copanelist.
        adjustments: the circuit adjustment of each score.

    """
    units = table['judge_nid']
    before = pd.Series(
        (table[f'{score}_raw'] - table[f'{score}_super_panel']).to_numpy(),
        index = units)
    circuit = _circuit_adjustment(
        votes, pairs, scorer, scores = before, table = table,
        method = adjustments[score])
    table[f'{score}_circuit'] = circuit.reindex(units).fillna(0).to_numpy()
    table[f'{score}_adjusted'] = (
        before.to_numpy() - table[f'{score}_circuit'].to_numpy())


def _circuit_adjustment(
    votes: pd.DataFrame,
    pairs: pd.DataFrame,
    scorer: Scorer,
    *,
    scores: pd.Series,
    table: pd.DataFrame,
    method: str) -> pd.Series:
    """Returns the circuit adjustment of each judge's score.

    Args:
        votes: every vote, with "unit" and "court_num".
        pairs: every pair of a vote and a copanelist.
        scorer: returns the score of each "unit" of votes.
        scores: each judge's score before the adjustment.
        table: the table of scores, with "judge_nid", "circuit", and
            "qualified".
        method: "per_judge", "per_vote", "full", or "none".

    Returns:
        The amount to subtract from each judge's score.

    """
    if method == 'none':
        return pd.Series(0.0, index = scores.index)
    circuits = votes.groupby('unit')['court_num'].nunique()
    travelers = circuits.index[circuits > 1]
    traveling = votes[votes['unit'].isin(travelers)]
    differentials: dict[int, float] = {}
    traveling_votes: dict[int, int] = {}
    for court, group in traveling.groupby('court_num'):
        numbers = group.groupby('unit').size()
        known = scores.reindex(numbers.index)
        if known.isna().all():
            continue
        expected = float(
            (numbers * known).sum() / numbers[known.notna()].sum())
        pooled = group.assign(unit = _TRAVELER)
        actual = scorer(pooled, pairs).get(_TRAVELER, np.nan)
        if pd.isna(actual):
            continue
        differentials[int(court)] = float(actual) - expected
        traveling_votes[int(court)] = len(group)
    if not differentials:
        return pd.Series(0.0, index = scores.index)
    if method == 'per_judge':
        home = pd.Series(table['circuit'].to_numpy(), index = table['judge_nid'])
        counted = table[table['qualified']] if table['qualified'].any() else (
            table)
        judges = counted.groupby('circuit').size()
        return home.map(lambda c: (
            differentials.get(c, 0.0) / (2 * judges.get(c, 1))
            if pd.notna(c) else 0.0)).astype('float64')
    cells = votes.groupby(['unit', 'court_num']).size().rename(
        'votes').reset_index()
    totals = votes.groupby('unit').size()
    adjustment = pd.Series(0.0, index = scores.index)
    for unit, court, count in cells.itertuples(index = False, name = None):
        difference = differentials.get(int(court))
        if difference is None or unit not in adjustment.index:
            continue
        if method == 'per_vote':
            share = count / traveling_votes[int(court)]
        else:
            share = count / totals[unit]
        adjustment[unit] += difference * share
    return adjustment


def _scale_signed(
    values: pd.Series,
    qualified: pd.Series,
    party: pd.Series,
    *,
    center: bool) -> pd.Series:
    """Returns scores on a scale from -100 to 100.

    Args:
        values: the adjusted scores.
        qualified: whether each judge defines the scale.
        party: the party of the president who appointed each judge.
        center: whether to make the judge whose rank (from the most liberal)
            is the number of Democratic appointees the zero, as the 2010
            article did.

    Returns:
        The scores, multiplied so that the judge farthest from zero is at
            -100 or 100.

    """
    defining = values[qualified.to_numpy()].dropna()
    if defining.empty:
        defining = values.dropna()
    if center and len(defining) > 1:
        ranked = np.sort(defining.to_numpy())
        democrats = int((party[qualified.to_numpy()] == -1).sum())
        place = min(max(democrats, 1), len(ranked) - 1)
        zero = (ranked[place - 1] + ranked[place]) / 2
        values = values - zero
        defining = defining - zero
    farthest = defining.abs().max() if len(defining) else 0
    if not farthest:
        return values * 0
    return 100 * values / farthest


def _scale_unit(values: pd.Series, qualified: pd.Series) -> pd.Series:
    """Returns scores on a scale from 0 to 100.

    Args:
        values: the adjusted scores.
        qualified: whether each judge defines the scale.

    Returns:
        The scores, shifted so that the lowest of the judges who define the
            scale is 0 and multiplied so that the highest is 100.

    """
    defining = values[qualified.to_numpy()].dropna()
    if defining.empty:
        defining = values.dropna()
    lowest, highest = defining.min(), defining.max()
    if not highest > lowest:
        return values * 0 + 50
    scaled: pd.Series = 100 * (values - lowest) / (highest - lowest)
    return scaled


""" Preparation """


def _judges(
    votes: pd.DataFrame,
    pairs: pd.DataFrame,
    minimum: int) -> pd.DataFrame:
    """Returns the table of judges that the scores are added to.

    Args:
        votes: every vote, as `_prepare` returns it.
        pairs: every pair, as `_prepare` returns it.
        minimum: fewest interactions for a judge to define the scales.

    Returns:
        A table with a row for each judge and the columns "judge_nid",
            "judge", "judge_party", "circuit" (the circuit where the judge
            cast most votes without sitting by designation), "votes",
            "panel_interactions" (copanelists of known party),
            "district_interactions" (district judges of known party),
            "interactions", "traveling_votes" (votes outside "circuit"), and
            "qualified".

    """
    grouped = votes.groupby('unit')
    home_votes = votes[~votes['designated']]
    home = home_votes.groupby('unit')['court_num'].agg(_mode)
    fallback = grouped['court_num'].agg(_mode)
    table = pd.DataFrame({
        'judge': grouped['judge'].first(),
        'judge_party': grouped['party'].first(),
        'circuit': home.reindex(fallback.index).fillna(fallback),
        'votes': grouped.size(),
        'panel_interactions': _paired(pairs, votes).groupby('unit').size(),
        'district_interactions': votes[votes['district_party'].notna()]
        .groupby('unit').size()})
    table = table.fillna({'panel_interactions': 0, 'district_interactions': 0})
    table['interactions'] = (
        table['panel_interactions'] + table['district_interactions'])
    away = votes['court_num'] != votes['unit'].map(table['circuit'])
    table['traveling_votes'] = away.groupby(votes['unit']).sum()
    table['qualified'] = table['interactions'] >= minimum
    table.index.name = 'judge_nid'
    return table.reset_index().astype({
        'panel_interactions': 'int64', 'district_interactions': 'int64',
        'interactions': 'int64', 'traveling_votes': 'int64'})


def _prepare(
    votes: pd.DataFrame,
    provoked: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns the votes and the pairs of votes and copanelists to score.

    Args:
        votes: a table of votes.
        provoked: "author" or "panel" (see `score_judges`).

    Raises:
        KeyError: if `votes` lacks a column that is needed.

    Returns:
        The votes, with plain columns and what a blank-slate judge would do
            in each super-panel, and a table with a row for each pair of a
            vote and a copanelist of known party.

    """
    needed = [
        'case_id', 'judge_nid', 'judge_party', 'court_num', 'type_criminal',
        'review_standard', 'vote_reversal', 'judge_dissented',
        'judge_concurred', 'judge_author', 'district_party', 'alignment']
    missing = [c for c in needed if c not in votes.columns]
    if missing:
        message = f'the scores need the columns {missing} of the votes'
        raise KeyError(message)
    votes = votes[votes['judge_nid'].notna()]
    dissented = _flags(votes['judge_dissented'])
    party = pd.to_numeric(votes['judge_party'], errors = 'coerce')
    district = pd.to_numeric(votes['district_party'], errors = 'coerce')
    reversed_ = _numbers(votes['vote_reversal'])
    prepared = pd.DataFrame({
        'unit': pd.to_numeric(votes['judge_nid']).astype('int64'),
        'case_id': votes['case_id'].astype(str),
        'judge': (
            votes['judge'].astype(object) if 'judge' in votes.columns
            else None),
        'party': party,
        'court_num': pd.to_numeric(votes['court_num'], errors = 'coerce'),
        'criminal': _flags(votes['type_criminal']),
        'standard': votes['review_standard'].astype(object).where(
            votes['review_standard'].isin(_STANDARDS), 'unclear'),
        'district_party': district.where(district.isin(_PARTIES)),
        'alignment': votes['alignment'].astype(object),
        'reversed': reversed_,
        'affirmed': 1 - reversed_,
        'dissented': dissented,
        'concurred': _flags(votes['judge_concurred']) & ~dissented,
        'author': _flags(votes['judge_author']),
        'designated': (
            _flags(votes['judge_designated'])
            if 'judge_designated' in votes.columns
            else pd.Series(False, index = votes.index))},
        index = votes.index)
    prepared['copartisan'] = (district == party).astype(object).where(
        district.isin(_PARTIES) & party.isin(_PARTIES))
    cases = prepared['case_id']
    for kind, column in (
        ('dissented', 'dissent_events'), ('concurred', 'concurrence_events')):
        own = prepared[kind].astype(int)
        others = own.groupby(cases).transform('sum') - own
        provoking = (
            prepared['author'] if provoked == 'author'
            else ~prepared['dissented'])
        prepared[column] = own + others * provoking.astype(int)
    expected = prepared.groupby(
        ['alignment', 'criminal', 'standard'])['reversed'].transform('mean')
    fallback = prepared.groupby(
        ['criminal', 'standard'])['reversed'].transform('mean')
    prepared['expected_reversed'] = expected.fillna(fallback)
    prepared['expected_affirmed'] = 1 - prepared['expected_reversed']
    pairs = _pairs(prepared)
    return prepared, pairs


def _pairs(votes: pd.DataFrame) -> pd.DataFrame:
    """Returns a row for each pair of a vote and a copanelist.

    Args:
        votes: every vote, as `_prepare` makes it.

    Returns:
        A table with the columns "vote" (the label of the vote), "criminal",
            "colleague_party", "agree" (whether the two judges both dissented
            or both did not), and "expected_agree" (the rate at which judges
            agreed with copanelists of that party in the vote's alignment
            and case type), for each copanelist of known party.

    """
    left = pd.DataFrame({
        'vote': votes.index, 'case_id': votes['case_id'].to_numpy(),
        'unit': votes['unit'].to_numpy(),
        'criminal': votes['criminal'].to_numpy(),
        'alignment': votes['alignment'].to_numpy(),
        'dissented': votes['dissented'].to_numpy()})
    right = pd.DataFrame({
        'case_id': votes['case_id'].to_numpy(),
        'colleague': votes['unit'].to_numpy(),
        'colleague_party': votes['party'].to_numpy(),
        'colleague_dissented': votes['dissented'].to_numpy()})
    pairs = left.merge(right, on = 'case_id')
    pairs = pairs[
        (pairs['unit'] != pairs['colleague'])
        & pairs['colleague_party'].isin(_PARTIES)].copy()
    pairs['agree'] = (
        pairs['dissented'] == pairs['colleague_dissented']).astype('float64')
    expected = pairs.groupby(
        ['alignment', 'criminal', 'colleague_party'])['agree'].transform(
            'mean')
    fallback = pairs.groupby(['criminal', 'colleague_party'])[
        'agree'].transform('mean')
    pairs['expected_agree'] = expected.fillna(fallback)
    return pairs[[
        'vote', 'criminal', 'colleague_party', 'agree',
        'expected_agree']].reset_index(drop = True)


""" Private Functions """


def _by_judge(table: pd.DataFrame, values: pd.Series) -> np.ndarray:
    """Returns values labeled by judge in the order of the table of scores.

    Args:
        table: the table of scores, with "judge_nid".
        values: values labeled by the judges' numbers.

    Returns:
        The value of each row of `table`.

    """
    return values.reindex(table['judge_nid']).to_numpy(dtype = 'float64')


def _cell(rates: pd.Series, **values: Any) -> pd.Series:
    """Returns the rates of one cell, by judge.

    Args:
        rates: rates labeled by "unit" and the keys of the cells.
        **values: the value of each key of the cell.

    Returns:
        The rate of each judge (or "unit") in the cell.

    """
    mask = np.ones(len(rates), dtype = bool)
    for key, value in values.items():
        mask &= rates.index.get_level_values(key) == value
    picked = rates[mask]
    picked.index = picked.index.get_level_values('unit')
    return picked


def _cell_rates(
    frame: pd.DataFrame,
    reference: pd.DataFrame,
    value: str,
    keys: Sequence[str],
    levels: Sequence[Sequence[Any]],
    *,
    minimum: int) -> tuple[pd.Series, pd.Series]:
    """Returns each judge's mean of a column in each cell, with fallbacks.

    A judge's own mean in a cell is used if the judge has at least
    `minimum` votes in it. Otherwise, the judge's mean in the cell's
    criminal and civil cases together is used (with the same minimum), and
    else the mean of all judges in the cell.

    Args:
        frame: the rows to average, with "unit" and `keys`.
        reference: every row, for the means of all judges.
        value: name of the column to average.
        keys: names of the columns that define the cells.
        levels: the values of each key.
        minimum: fewest rows for a judge's own mean to be used.

    Returns:
        The means and the numbers of rows, labeled by "unit" and `keys`.

    """
    units = pd.Index(frame['unit'].unique(), name = 'unit')
    index = pd.MultiIndex.from_product(
        [units, *levels], names = ['unit', *keys])
    own = frame.groupby(['unit', *keys])[value].agg(['mean', 'count'])
    own = own.reindex(index)
    counts = own['count'].fillna(0)
    rates = own['mean'].where(counts >= minimum)
    others = [k for k in keys if k != 'criminal']
    if len(others) < len(keys):
        grouped = frame.groupby(['unit', *others])[value].agg(
            ['mean', 'count'])
        pooled = grouped['mean'].where(grouped['count'] >= minimum)
        aligned = pooled.reindex(index.droplevel('criminal'))
        rates = rates.fillna(pd.Series(aligned.to_numpy(), index = index))
    overall = reference.groupby(list(keys))[value].mean()
    aligned = overall.reindex(index.droplevel('unit'))
    rates = rates.fillna(pd.Series(aligned.to_numpy(), index = index))
    mean = reference[value].mean()
    return rates.fillna(0.0 if pd.isna(mean) else mean), counts


def _check(value: str, choices: Sequence[str], name: str) -> None:
    """Raises an error if a setting is not one of its choices.

    Args:
        value: the setting.
        choices: its choices.
        name: its name.

    Raises:
        ValueError: if `value` is not in `choices`.

    """
    if value not in choices:
        message = f'{name} must be one of {list(choices)}, not {value!r}'
        raise ValueError(message)


def _fit(
    deviation: pd.Series,
    rate: pd.Series,
    qualified: np.ndarray) -> pd.Series:
    """Returns the rates that a linear regression on deviation predicts.

    Args:
        deviation: each judge's distance from the circuit's mean ideology.
        rate: each judge's rate.
        qualified: whether each judge is fitted.

    Returns:
        The fitted rate of every judge. If fewer than three judges can be
            fitted, it is their mean rate.

    """
    usable = qualified & deviation.notna().to_numpy() & rate.notna().to_numpy()
    if usable.sum() < 3 or np.ptp(deviation[usable]) == 0:
        mean = rate[usable].mean() if usable.any() else rate.mean()
        return pd.Series(0.0 if pd.isna(mean) else mean, index = rate.index)
    slope, intercept = np.polyfit(
        deviation[usable].to_numpy(float), rate[usable].to_numpy(float), 1)
    fitted: pd.Series = intercept + slope * deviation
    return fitted


def _flags(column: pd.Series) -> pd.Series:
    """Returns a column of flags as plain booleans.

    Args:
        column: flags, which may be missing.

    Returns:
        The flags, with missing values false.

    """
    return column.astype('boolean').fillna(False).astype(bool)


def _mode(values: pd.Series) -> float:
    """Returns the most common value, or a missing value if there is none.

    Args:
        values: the values.

    Returns:
        The most common value (the smallest, if several are as common).

    """
    counts = values.dropna().value_counts()
    if counts.empty:
        return np.nan
    return float(counts[counts == counts.max()].index.min())


def _numbers(column: pd.Series) -> pd.Series:
    """Returns a column of flags as numbers.

    Args:
        column: flags, which may be missing.

    Returns:
        1.0 for true, 0.0 for false, and NaN for missing values.

    """
    return pd.Series(
        column.astype('boolean').astype('Float64').to_numpy(
            dtype = 'float64', na_value = np.nan),
        index = column.index)


def _paired(pairs: pd.DataFrame, votes: pd.DataFrame) -> pd.DataFrame:
    """Returns the pairs of some votes, with the "unit" of each vote.

    Args:
        pairs: every pair of a vote and a copanelist.
        votes: the votes whose pairs to return, with "unit".

    Returns:
        The pairs, with "unit".

    """
    kept = pairs[pairs['vote'].isin(votes.index)]
    return kept.assign(unit = kept['vote'].map(votes['unit']).to_numpy())
