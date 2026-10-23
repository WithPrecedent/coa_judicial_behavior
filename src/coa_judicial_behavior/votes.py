"""Turns coded appeals into the votes that the scores are computed from.

Each of the four scores in Yung's studies is computed from what he called the
"super-panel": the three judges of an appellate panel and the district judge
whose judgment they review. Each vote of an appellate judge has three
interactions with other judges (two with copanelists and one with the
district judge), and the scores turn on whether the judge agreed with each
of them, on the standard of review that the panel applied, and on the
parties of the presidents who appointed them.

courtpy finds most of what that needs: the judges of each panel and who
dissented or concurred (`code_judges` and its `judge_votes`), whether the
decision reversed (`code_outcome`), whether the case is criminal
(`code_case_type`), and four standards of review (the federal rules'
`standard_...` flags). The rulebook in "instructions/review.csv" adds the
rest: the district judge's name, whether the appeal came from a district
court, immigration review (which the studies left out), and two more
deferential standards. Three techniques, which are added to the `amos`
library as soon as coa_judicial_behavior is imported, then put it together:

* `code_review` (an `amos.Munger`) sorts each case by the standard of review
  that it applied ("deferential", "non_deferential", or "unclear") and marks
  the cases that the studies left out (immigration and habeas corpus).
* `code_district_judge` (an `amos.Munger`) finds the district judge in the
  roster of judges, and adds the party of the president who appointed the
  judge.
* `review_votes` (an `amos.Shaper`) makes the table of votes, with one row
  for each judge on each case (courtpy's `vote_table`), and adds what each
  vote's super-panel was: the parties of the judge's two copanelists and of
  the district judge (the "alignment", such as "RR-D").

Contents:
    CodeDistrictJudge: finds the district judge whose judgment each case
        reviews.
    CodeReview: sorts each case by its standard of review and marks the
        cases that the studies left out.
    DEFERENTIAL: the flags of the deferential standards of review.
    NON_DEFERENTIAL: the flags of the nondeferential standards of review.
    RULEBOOK: the path of the rulebook that finds what the scores need.
    ReviewVotes: makes the table of votes.
    STANDARDS: the categories of the standard of review.
    describe_panels: adds the super-panel of each vote to a table of votes.
    vote_table: returns the table of votes.

"""

from __future__ import annotations

import dataclasses
import pathlib
from collections.abc import Sequence
from typing import Any

import amos
import numpy as np
import pandas as pd
from courtpy import judges

DEFERENTIAL: tuple[str, ...] = (
    'standard_clear_error', 'standard_abuse_disc', 'standard_arb_cap',
    'standard_substantial_evidence', 'standard_plain_error')
NON_DEFERENTIAL: tuple[str, ...] = ('standard_de_novo',)
RULEBOOK: pathlib.Path = (
    pathlib.Path(__file__).parent / 'instructions' / 'review.csv')
STANDARDS: tuple[str, ...] = ('deferential', 'non_deferential', 'unclear')
# Habeas corpus and immigration cases were left out of the studies because
# their standards of review are unique (the deference of AEDPA, and the
# collateral review of the Board of Immigration Appeals).
_EXCLUDED: tuple[str, ...] = (
    'civil_habeas', 'civil_aedpa', 'civil_ina', 'civil_asylum',
    'review_immigration')
_DISTRICT_COURT: str = 'U.S. District Court'
_PARTY_LETTERS: dict[int, str] = {-1: 'D', 1: 'R'}


@dataclasses.dataclass
class CodeReview(amos.Munger):
    """Sorts each case by its standard of review.

    Standards of review are the formal rules that tell an appellate court
    how much to defer to the court below, and the activism, partisanship,
    and ideology scores all compare what judges do under deferential and
    nondeferential standards. A case is "deferential" if the opinion names
    only deferential standards (clear error, abuse of discretion, arbitrary
    and capricious, substantial evidence, or plain error), "non_deferential"
    if it names only de novo review, and "unclear" if it names both or
    neither, which is how the studies sorted them. Adds:

    | Column | Meaning |
    | --- | --- |
    | `review_standard` | "deferential", "non_deferential", or "unclear". |
    | `review_deferential`, `review_de_novo` | Whether the standard is deferential, or de novo. |
    | `review_has_standard` | Whether the opinion names any standard of review (or uses words that announce one), as every case in the studies did. |
    | `review_excluded` | Whether the case is one that the studies left out: habeas corpus or immigration. |
    | `review_of_district` | Whether the case reviews a district court: the appeal came from one (or its judge was found), and it is not a petition to review an agency. |

    Needs the `standard_...` flags. Uses the columns that
    "instructions/review.csv" makes, and the habeas and immigration flags of
    courtpy's civil rules, if they exist.

    """

    def munge(
        self,
        data: pd.DataFrame,
        deferential: Sequence[str] | str | None = None,
        non_deferential: Sequence[str] | str | None = None,
        excluded: Sequence[str] | str | None = None,
        **kwargs: Any) -> pd.DataFrame:
        """Sorts each case by its standard of review.

        Args:
            data: the parsed cases.
            deferential: names of the flags of deferential standards.
                Defaults to `None`, in which case they are `DEFERENTIAL`.
            non_deferential: names of the flags of nondeferential standards.
                Defaults to `None`, in which case they are `NON_DEFERENTIAL`.
            excluded: names of the flags of the cases to leave out. Defaults
                to `None`, in which case they are habeas corpus and
                immigration.
            **kwargs: not used.

        Raises:
            KeyError: if the cases have none of the flags of either kind of
                standard.

        Returns:
            The cases, with the new columns.

        """
        deferring = _any(data, _listify(deferential) or DEFERENTIAL)
        novo = _any(data, _listify(non_deferential) or NON_DEFERENTIAL)
        if deferring is None or novo is None:
            message = (
                f'{self.name!r} needs the flags of the standards of review '
                f'(such as "standard_de_novo"), which the federal rules of '
                f'courtpy make'
            )
            raise KeyError(message)
        standard = np.select(
            [deferring & ~novo, novo & ~deferring],
            ['deferential', 'non_deferential'], default = 'unclear')
        data['review_standard'] = pd.Series(
            standard, index = data.index, dtype = object)
        data['review_deferential'] = data['review_standard'] == 'deferential'
        data['review_de_novo'] = data['review_standard'] == 'non_deferential'
        named = _any(data, ['standard_named'])
        data['review_has_standard'] = (
            deferring | novo | (False if named is None else named))
        left_out = _any(data, _listify(excluded) or _EXCLUDED)
        data['review_excluded'] = (
            pd.Series(False, index = data.index) if left_out is None
            else left_out)
        district = _any(data, ['review_district'])
        agency = _any(data, ['review_agency'])
        found = (
            data['district_judge_nid'].notna()
            if 'district_judge_nid' in data.columns else False)
        data['review_of_district'] = (
            (pd.Series(False, index = data.index) if district is None
             else district) | found) & ~(
                False if agency is None else agency)
        return data


@dataclasses.dataclass
class CodeDistrictJudge(amos.Munger):
    """Finds the district judge whose judgment each case reviews.

    Each name in "district_judges" (which "instructions/review.csv" finds in
    the lines about the court appealed from) is matched to a judge in a
    roster (see `courtpy.judges.Roster`), among the district judges of the
    case's circuit who were serving in its year. The first name that fits
    one judge is the district judge. A judge who also sat on the panel (as
    a district judge sitting by designation does) is not taken for the
    district judge. Adds:

    | Column | Meaning |
    | --- | --- |
    | `district_judge` | The district judge's name, as the roster reports it. |
    | `district_judge_nid` | The Federal Judicial Center's number for the judge. |
    | `district_party` | The party of the president who appointed the judge: -1 for a Democrat and 1 for a Republican. |
    | `district_{attribute}` | Each other attribute named in `attributes` (such as `district_jcs`, the judge's Judicial Common Space score). |

    Needs "district_judges", "court_num", and "year".

    """

    def munge(
        self,
        data: pd.DataFrame,
        roster: judges.Roster | pd.DataFrame | pathlib.Path | str | None = (
            None),
        column: str = 'district_judges',
        attributes: Sequence[str] | str | None = None,
        **kwargs: Any) -> pd.DataFrame:
        """Adds the district judge of each case.

        Args:
            data: the parsed cases.
            roster: a roster, the table of one, or the path of a saved one.
                Defaults to `None`, in which case the roster saved in
                "judges" in courtpy's data folder is used.
            column: name of the column with the names of the district judge.
                Defaults to "district_judges".
            attributes: names of the roster's columns to add, other than
                "party". Defaults to `None`, in which case "jcs" is added if
                the roster has it.
            **kwargs: not used.

        Raises:
            KeyError: if the cases lack a column that is needed.

        Returns:
            The cases, with the new columns.

        """
        missing = [
            c for c in (column, 'court_num', 'year') if c not in data.columns]
        if missing:
            message = f'{self.name!r} needs the columns {missing}'
            raise KeyError(message)
        found = judges.Roster.create(roster)
        table = found.data
        if attributes is None:
            attributes = ['jcs'] if 'jcs' in table.columns else []
        wanted = ['party', *[
            a for a in _listify(attributes) if a in table.columns]]
        district = table[table['court_type'] == _DISTRICT_COURT]
        circuits = {
            int(float(str(number))): judges.Roster(rows, grace = found.grace)
            for number, rows in district.groupby('circuit_num')}
        panels = _panel_nids(data)
        rows: list[dict[str, Any]] = []
        for names, court, year, panel in zip(
            data[column], data['court_num'], data['year'], panels,
            strict = True):
            rows.append(_district_judge(
                _names(names), circuits.get(_whole(court) or -1),
                _whole(year), panel, wanted))
        added = pd.DataFrame(rows, index = data.index)
        data['district_judge'] = added['district_judge'].astype(object)
        data['district_judge_nid'] = added['district_judge_nid'].astype(
            'Int64')
        for name in wanted:
            data[f'district_{name}'] = added[name].astype('float64')
        return data


@dataclasses.dataclass
class ReviewVotes(amos.Shaper):
    """Makes the table of votes, with one row for each judge on each case.

    The table is courtpy's table of votes (see `courtpy.judges.vote_table`)
    with the super-panel of each vote added (see `describe_panels`). It
    replaces the table of cases, so it comes after the techniques that code
    the cases and, like every shaper, before the data is split. Its
    "case_id" column should be the "groups" of a study, which keeps the
    judges of a case together.

    """

    def shape(
        self,
        data: pd.DataFrame,
        roster: judges.Roster | pd.DataFrame | pathlib.Path | str | None = (
            None),
        outcomes: Sequence[str] | str | None = None,
        **kwargs: Any) -> pd.DataFrame:
        """Returns a table with one row for each judge on each case.

        Args:
            data: the coded cases.
            roster: a roster, the table of one, or the path of a saved one.
                Defaults to `None`, in which case the roster saved in
                "judges" in courtpy's data folder is used.
            outcomes: names of the columns with the outcomes of the cases.
                Defaults to `None`, in which case they are the columns whose
                names start with "outcome_".
            **kwargs: not used.

        Returns:
            The table of votes.

        """
        return vote_table(
            data, roster, outcomes = _listify(outcomes) or None)


def describe_panels(votes: pd.DataFrame) -> pd.DataFrame:
    """Adds the super-panel of each vote to a table of votes.

    Adds:

    | Column | Meaning |
    | --- | --- |
    | `colleagues_republican`, `colleagues_democratic` | How many of the judge's copanelists were appointed by Republican and Democratic presidents. |
    | `copanel` | The parties of the judge's two copanelists: "RR", "DR", or "DD" (missing unless there are two, both of known party). |
    | `alignment` | The copanelists and the district judge, as the studies wrote them: "RR-R", "RR-D", "DR-R", "DR-D", "DD-R", or "DD-D". Missing if any of them is unknown. |
    | `district_opposed` | Whether the district judge was appointed by a president of the other party than the judge's. Missing if either is unknown. |
    | `panel_unanimous` | Whether no judge of the case dissented. |

    Args:
        votes: a table of votes, with "case_id", "judge_party",
            "judge_dissented", and "district_party".

    Returns:
        The table, with the new columns.

    """
    party = pd.to_numeric(votes['judge_party'], errors = 'coerce')
    cases = votes['case_id']
    republican = (party == 1).groupby(cases).transform('sum') - (party == 1)
    democratic = (party == -1).groupby(cases).transform('sum') - (party == -1)
    known = republican + democratic
    votes['colleagues_republican'] = republican.astype('int64')
    votes['colleagues_democratic'] = democratic.astype('int64')
    copanel = pd.Series(
        np.select(
            [republican == 2, (republican == 1) & (democratic == 1),
             democratic == 2],
            ['RR', 'DR', 'DD'], default = ''),
        index = votes.index)
    copanel = copanel.where(known == 2).replace('', pd.NA)
    votes['copanel'] = copanel.astype(object)
    district = pd.to_numeric(votes['district_party'], errors = 'coerce')
    letters = district.map(_PARTY_LETTERS)
    votes['alignment'] = (copanel + '-' + letters).where(
        copanel.notna() & letters.notna()).astype(object)
    votes['district_opposed'] = (district != party).astype('boolean').where(
        district.notna() & party.notna())
    dissents = votes['judge_dissented'].astype(bool).groupby(cases).transform(
        'sum')
    votes['panel_unanimous'] = dissents == 0
    return votes


def vote_table(
    data: pd.DataFrame,
    roster: judges.Roster | pd.DataFrame | pathlib.Path | str | None = None,
    *,
    outcomes: Sequence[str] | None = None) -> pd.DataFrame:
    """Returns the table of votes, with each vote's super-panel.

    Args:
        data: the coded cases, which need what `courtpy.judges.vote_table`
            needs and "district_party" (from `code_district_judge`).
        roster: a roster, the table of one, or the path of a saved one.
            Defaults to `None`, in which case the roster saved in "judges"
            in courtpy's data folder is used.
        outcomes: names of the columns with the outcomes of the cases.
            Defaults to `None`, in which case they are the columns whose
            names start with "outcome_".

    Returns:
        The table, labeled by "vote_id".

    """
    if 'district_party' not in data.columns:
        data = data.assign(district_party = np.nan)
    votes = judges.vote_table(data, roster, outcomes = outcomes)
    return describe_panels(votes)


""" Private Functions """


def _any(data: pd.DataFrame, columns: Sequence[str]) -> pd.Series | None:
    """Returns whether any of the flags that the cases have is true.

    Args:
        data: the cases.
        columns: names of flags.

    Returns:
        Whether any of `columns` that `data` has is true in each case, or
            `None` if it has none of them.

    """
    present = [c for c in columns if c in data.columns]
    if not present:
        return None
    flags = data[present].fillna(False).astype(bool)
    return flags.any(axis = 1)


def _district_judge(
    names: list[str],
    roster: judges.Roster | None,
    year: int | None,
    panel: set[int],
    attributes: Sequence[str]) -> dict[str, Any]:
    """Returns the district judge that the names of a case refer to.

    Args:
        names: the names, as the opinion writes them.
        roster: the district judges of the case's circuit, or `None` if
            there are none.
        year: the year of the case, or `None`.
        panel: the numbers of the judges of the case's panel.
        attributes: the roster's columns to return.

    Returns:
        The judge's name ("district_judge"), number ("district_judge_nid"),
            and `attributes`, all missing if no judge is found.

    """
    empty: dict[str, Any] = {
        'district_judge': None, 'district_judge_nid': pd.NA,
        **dict.fromkeys(attributes, np.nan)}
    if roster is None:
        return empty
    for name in names:
        row = roster.match(name, None, year)
        if row is None:
            continue
        nid = roster.nids([row])[0]
        if nid in panel:
            continue
        values = roster.data.iloc[row]
        return {
            'district_judge': roster.names([row])[0],
            'district_judge_nid': nid,
            **{a: pd.to_numeric(values[a], errors = 'coerce')
               for a in attributes}}
    return empty


def _listify(value: Sequence[str] | str | None) -> list[str]:
    """Returns a setting as a list of names.

    Args:
        value: a name, names separated by commas, a sequence of names, or
            `None`.

    Returns:
        The names, which is empty if `value` is `None` or blank.

    """
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(',') if v.strip()]
    return [str(v) for v in value]


def _names(value: Any) -> list[str]:
    """Returns a cell of a table of cases as a list of names.

    Args:
        value: a list of names, the names joined by semicolons (as courtpy
            saves lists in a CSV file), or a missing value.

    Returns:
        The names.

    """
    if isinstance(value, (list, tuple, np.ndarray)):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        return [v.strip() for v in value.split(';') if v.strip()]
    return []


def _panel_nids(data: pd.DataFrame) -> list[set[int]]:
    """Returns the numbers of the judges of each case's panel.

    Args:
        data: the cases, with the "judge1_nid", "judge2_nid", ... columns
            that `code_judges` makes, if it was applied.

    Returns:
        The numbers of each case's judges who were found, which are empty
            for every case if `code_judges` was not applied.

    """
    columns = [
        c for c in data.columns
        if str(c).startswith('judge') and str(c).endswith('_nid')]
    if not columns:
        return [set() for _ in range(len(data))]
    numbers = data[columns].apply(pd.to_numeric, errors = 'coerce')
    return [
        {int(v) for v in row if not np.isnan(v)}
        for row in numbers.to_numpy(dtype = 'float64')]


def _whole(value: Any) -> int | None:
    """Returns a value as a whole number, or `None` if it is missing.

    Args:
        value: a number, or text of one.

    Returns:
        The number, or `None`.

    """
    number = pd.to_numeric(value, errors = 'coerce')
    return None if pd.isna(number) else int(number)
