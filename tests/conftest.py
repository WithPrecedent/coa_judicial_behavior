"""Fictional judges and appeals for the tests.

`simulate` makes a table of votes like the one that `review_votes` makes,
from judges whose traits are known, so the tests can check that the scores
find them. Each judge has an ideology (-1 to 1), an activism (how much more
often the judge reverses under deferential standards than the baseline), a
partisanship (how much more often the judge reverses district judges of the
other party under deferential standards), and an independence (how often
the judge writes separately). A few senior judges sit in other circuits.

`roster` and `write_cases` make fictional judges and fictional CourtListener
cases, which courtpy parses as it parses real ones, for the tests of the
rules and of the whole study.

"""

from __future__ import annotations

import copy
import dataclasses
import pathlib
import random
from collections.abc import Iterator
from typing import Any

import chrisjen
import courtpy
import numpy as np
import pandas as pd
import pytest

from coa_judicial_behavior import __main__ as commands
from coa_judicial_behavior import votes as votes_module

FIRST = 'U.S. Court of Appeals for the First Circuit'
NINTH = 'U.S. Court of Appeals for the Ninth Circuit'
MASSACHUSETTS = 'U.S. District Court for the District of Massachusetts'
CALIFORNIA = 'U.S. District Court for the Central District of California'
APPEALS = 'U.S. Court of Appeals'
DISTRICT = 'U.S. District Court'
CLINTON = ('William J. Clinton', 'Democratic')
BUSH = ('George W. Bush', 'Republican')
OBAMA = ('Barack Obama', 'Democratic')
# Fictional judges: id, last, first, and middle names, sex, race or
# ethnicity, year of birth, type of court, court, appointing president, the
# date of commission, and a Judicial Common Space score.
JUDGES: list[tuple[Any, ...]] = [
    (101, 'Lynch', 'Mary', 'Ann', 'Female', 'White', 1946, APPEALS, FIRST, CLINTON, '1995-03-17', -0.3),
    (102, 'Howard', 'John', 'Q.', 'Male', 'White', 1955, APPEALS, FIRST, BUSH, '2002-04-23', 0.4),
    (103, 'Thompson', 'Rita', 'Mae', 'Female', 'African American', 1951, APPEALS, FIRST, OBAMA, '2010-03-17', -0.4),
    (104, 'Stone', 'Nora', 'H.', 'Female', 'White', 1941, APPEALS, FIRST, BUSH, '2003-04-30', 0.3),
    (105, 'Baron', 'Dale', 'J.', 'Male', 'White', 1967, APPEALS, FIRST, OBAMA, '2014-05-20', -0.2),
    (106, 'Kay', 'William', 'J.', 'Male', 'White', 1953, APPEALS, FIRST, BUSH, '2003-02-13', 0.5),
    (201, 'Graber', 'Susan', 'P.', 'Female', 'White', 1949, APPEALS, NINTH, CLINTON, '1998-03-19', -0.5),
    (202, 'Bea', 'Carlos', 'T.', 'Male', 'Hispanic', 1934, APPEALS, NINTH, BUSH, '2003-10-01', 0.5),
    (203, 'Ikuta', 'Sandra', 'S.', 'Female', 'Asian American', 1954, APPEALS, NINTH, BUSH, '2006-06-23', 0.4),
    (204, 'Hurwitz', 'Andrew', 'D.', 'Male', 'White', 1947, APPEALS, NINTH, OBAMA, '2012-06-27', -0.3),
    (205, 'Nelson', 'Ryan', 'D.', 'Male', 'White', 1973, APPEALS, NINTH, OBAMA, '2012-10-18', -0.2),
    (301, 'Woods', 'Dana', 'Paul', 'Male', 'Hispanic', 1947, DISTRICT, MASSACHUSETTS, CLINTON, '1996-06-16', -0.3),
    (302, 'Gray', 'Ellen', 'R.', 'Female', 'White', 1960, DISTRICT, MASSACHUSETTS, BUSH, '2004-05-12', 0.3),
    (303, 'Hale', 'Peter', 'K.', 'Male', 'White', 1965, DISTRICT, MASSACHUSETTS, OBAMA, '2011-09-01', -0.2),
    (304, 'Lynch', 'Thomas', 'E.', 'Male', 'White', 1958, DISTRICT, MASSACHUSETTS, BUSH, '2005-01-10', 0.4),
    (401, 'Ortiz', 'Ana', 'L.', 'Female', 'Hispanic', 1962, DISTRICT, CALIFORNIA, OBAMA, '2010-04-20', -0.4),
    (402, 'Pruitt', 'James', 'W.', 'Male', 'White', 1957, DISTRICT, CALIFORNIA, BUSH, '2002-07-30', 0.3)]
BENCHES: dict[str, list[str]] = {
    'ca1': ['Lynch', 'Howard', 'Thompson', 'Stone', 'Baron', 'Kay'],
    'ca9': ['Graber', 'Bea', 'Ikuta', 'Hurwitz', 'Nelson']}
# The district judges of each circuit, as an opinion names them, and the
# district court.
DISTRICT_JUDGES: dict[str, list[str]] = {
    'ca1': ['Dana P. Woods', 'Ellen R. Gray', 'Peter K. Hale', 'Thomas E. Lynch'],
    'ca9': ['Ana L. Ortiz', 'James W. Pruitt']}
DISTRICT_COURTS: dict[str, str] = {
    'ca1': 'the District of Massachusetts',
    'ca9': 'the Central District of California'}
CAREERS: list[tuple[int, str]] = [
    (101, 'Assistant attorney general, State of Massachusetts, 1973-1974'),
    (102, 'Assistant U.S. attorney, District of New Hampshire, 1981-1987'),
    (103, 'Assistant public defender, Rhode Island, 1976-1979'),
    (104, 'Judge, Superior Court of Massachusetts, 1990-2003'),
    (204, 'Law clerk, Hon. B. Justice, Supreme Court of the United States, 1972-1973'),
    (205, 'Professor, University of the West School of Law, 2005-2010')]
COURT_NAMES: dict[str, str] = {
    'ca1': 'Court of Appeals for the First Circuit',
    'ca9': 'Court of Appeals for the Ninth Circuit'}
ADDRESSES: dict[str, str] = {
    'ca1': 'http://media.ca1.uscourts.gov/pdf.opinions/{number}P-01A.pdf',
    'ca9': 'https://cdn.ca9.uscourts.gov/datastore/opinions/2015/06/15/{number}.pdf'}
STANDARDS: dict[str, str] = {
    'deferential': 'We review the denial of the motion for abuse of discretion.',
    'non_deferential': 'We review de novo.',
    # An opinion that names both kinds of standard is "unclear".
    'unclear': (
        'We review the findings for clear error and the conclusions of law '
        'de novo.')}


@pytest.fixture(autouse = True)
def restore_library() -> Iterator[None]:
    """Removes the classes that a test adds to the library."""
    saved = copy.deepcopy(chrisjen.library.contents)
    yield
    chrisjen.library.contents.clear()
    chrisjen.library.contents.update(saved)


@pytest.fixture(autouse = True)
def private_folders(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch) -> None:
    """Keeps tests away from the user's real key, bulk files, and roster."""
    monkeypatch.delenv(courtpy.options._ENV_API_KEY, raising = False)
    monkeypatch.setenv(courtpy.options._ENV_CONFIG, str(tmp_path / 'config'))
    monkeypatch.setenv(courtpy.options._ENV_DATA, str(tmp_path / 'courtpy'))
    monkeypatch.setattr(courtpy.secrets, '_keyring', lambda: None)


def fjc_tables() -> dict[str, pd.DataFrame]:
    """Returns the fictional judges as the Federal Judicial Center's files."""
    service, people = [], []
    for nid, last, first, middle, sex, race, born, kind, court, appointer, began, _ in JUDGES:
        president, party = appointer
        service.append({
            'nid': nid, 'Sequence': 1, 'Judge Name': f'{last}, {first} {middle}',
            'Court Type': kind, 'Court Name': court,
            'Appointing President': president,
            'Party of Appointing President': party,
            'ABA Rating': 'Well Qualified', 'Recess Appointment Date': '',
            'Senate Vote Type': 'Voice', 'Ayes/Nays': '',
            'Commission Date': began, 'Senior Status Date': '',
            'Termination Date': ''})
        people.append({
            'nid': nid, 'Last Name': last, 'First Name': first,
            'Middle Name': middle, 'Suffix': '', 'Birth Year': born,
            'Gender': sex, 'Race or Ethnicity': race})
    return {
        'service': pd.DataFrame(service),
        'demographics': pd.DataFrame(people),
        'career': pd.DataFrame(CAREERS, columns = ['nid', 'Professional Career'])}


@pytest.fixture
def roster() -> courtpy.judges.Roster:
    """Returns a roster of the fictional judges, saved where courtpy looks.

    Its careers are coded by this project's rules, and each judge has a
    Judicial Common Space score ("jcs").

    """
    table = courtpy.judges.build_roster(
        **fjc_tables(), rulebook = commands.CAREERS)
    scores = {row[0]: row[-1] for row in JUDGES}
    table['jcs'] = table['nid'].map(scores)
    made = courtpy.judges.Roster(table)
    made.save()
    return made


def make_case(
    number: int,
    court: str,
    panel: list[str],
    *,
    year: int = 2015,
    reversed_: bool = False,
    criminal: bool = True,
    standard: str = 'deferential',
    district_judge: str | None = 'Dana P. Woods',
    dissenter: str | None = None,
    concurrer: str | None = None) -> dict[str, Any]:
    """Returns a fictional appeal from a district court, as courtpy saves it.

    Args:
        number: the case's number.
        court: the CourtListener id of the court of appeals.
        panel: the last names of the panel's judges, the author first.
        year: the year of the decision. Defaults to 2015.
        reversed_: whether the panel reversed. Defaults to `False`.
        criminal: whether the case is a criminal appeal (or else a civil
            rights case under Title VII). Defaults to `True`.
        standard: the standard of review that the opinion names, a key of
            `STANDARDS`. Defaults to "deferential".
        district_judge: the district judge, as the opinion names the judge,
            or `None` for an opinion that does not. Defaults to "Dana P.
            Woods".
        dissenter: the last name of a judge who dissented. Defaults to
            `None`.
        concurrer: the last name of a judge who concurred. Defaults to
            `None`.

    Returns:
        The case.

    """
    decision = 'REVERSED.' if reversed_ else 'AFFIRMED.'
    if criminal:
        caption = (
            '<p>UNITED STATES OF AMERICA, Plaintiff-Appellee, v. JOHN DOE, '
            'Defendant-Appellant.</p>')
        facts = (
            'John Doe appeals his conviction for possession of a firearm. '
            'An Assistant United States Attorney argued for the government.')
        name = f'United States v. Doe {number}'
    else:
        caption = (
            '<p>JANE ROE, Plaintiff-Appellant, v. ACME CORPORATION, '
            'Defendant-Appellee.</p>')
        facts = (
            'Jane Roe appeals the dismissal of her claim of discrimination '
            'under Title VII of the Civil Rights Act of 1964.')
        name = f'Roe v. Acme Corporation {number}'
    judge = (
        f'<p>{district_judge}, District Judge.</p>' if district_judge else '')
    text = (
        f'<p>United States Court of Appeals For the {COURT_NAMES[court].split()[-2]} Circuit</p>'
        f'<p>No. 14-{number:04d}</p>'
        f'{caption}'
        f'<p>Appeal from the United States District Court for {DISTRICT_COURTS[court]}</p>'
        f'{judge}'
        f'<p>Before {panel[0].upper()}, {panel[1].upper()}, and {panel[2].upper()}, Circuit Judges.</p>'
        f'<p>{panel[0].upper()}, Circuit Judge. {facts} '
        f'{STANDARDS[standard]}</p><p>{decision}</p>')
    opinions = [{
        'id': number * 10, 'cluster_id': number, 'type': '010combined',
        'author_id': None, 'author_str': panel[0], 'per_curiam': False,
        'joined_by_str': '',
        'download_url': ADDRESSES[court].format(number = f'14-{number:04d}'),
        'html_with_citations': text}]
    for kind, writer, words in (
        ('040dissent', dissenter, 'dissenting. I would not.'),
        ('030concurrence', concurrer, 'concurring. I agree, but write.')):
        if writer:
            opinions.append({
                'id': number * 10 + len(opinions), 'cluster_id': number,
                'type': kind, 'author_id': None, 'author_str': writer,
                'per_curiam': False, 'joined_by_str': '', 'download_url': '',
                'html_with_citations': f'<p>{writer.upper()}, Circuit Judge, {words}</p>'})
    return {
        'source': 'court_listener',
        'court': {'id': court, 'full_name': COURT_NAMES[court], 'jurisdiction': 'F'},
        'cluster': {
            'id': number, 'docket_id': number + 5000, 'case_name': name,
            'case_name_full': '', 'date_filed': f'{year}-06-15', 'judges': '',
            'precedential_status': 'Published', 'disposition': '',
            'attorneys': '', 'citation_count': 0},
        'docket': None,
        'citations': [],
        'opinions': opinions}


def write_cases(
    folder: pathlib.Path,
    count: int = 600,
    *,
    seed: int = 7,
    activist: str = 'Kay') -> pathlib.Path:
    """Saves fictional appeals whose judges are drawn at random.

    Each judge reverses a fifth of judgments under a deferential standard
    and a third under de novo review, except `activist`, who reverses as
    often under both. Conservative judges reverse Democratic district
    judges more often, and liberal judges Republican ones.

    Args:
        folder: the folder to save the cases in.
        count: the number of cases. Defaults to 600.
        seed: seed of the random numbers. Defaults to 7.
        activist: the judge who does not defer. Defaults to "Kay".

    Returns:
        The folder.

    """
    rng = random.Random(seed)
    parties = {row[1]: (1 if row[9] == BUSH else -1) for row in JUDGES}
    for number in range(1, count + 1):
        court = rng.choice(list(BENCHES))
        panel = rng.sample(BENCHES[court], 3)
        standard = rng.choice(['deferential', 'deferential', 'non_deferential', 'unclear'])
        district = rng.choice(DISTRICT_JUDGES[court])
        district_party = parties[district.split()[-1]] if district.split()[-1] != 'Lynch' else 1
        votes = []
        for judge in panel:
            chance = 0.33 if standard != 'deferential' or judge == activist else 0.2
            chance += 0.1 * parties[judge] * -district_party
            votes.append(rng.random() < chance)
        reversed_ = sum(votes) >= 2
        minority = [j for j, v in zip(panel, votes, strict = True) if v != reversed_]
        case = make_case(
            number, court, panel, year = rng.choice([2014, 2015, 2016, 2017]),
            reversed_ = reversed_, criminal = rng.random() < 0.5,
            standard = standard, district_judge = district,
            dissenter = minority[0] if minority and rng.random() < 0.3 else None,
            concurrer = panel[1] if rng.random() < 0.05 else None)
        path = courtpy.courtlistener.case_path(folder, court, number)
        courtpy.courtlistener.save_case(path, case)
    return folder

# The rate of reversal of a judge with no traits, by whether the case is
# criminal and the standard of review, close to the rates in the studies.
_BASE: dict[tuple[bool, str], float] = {
    (True, 'deferential'): 0.10,
    (True, 'non_deferential'): 0.20,
    (True, 'unclear'): 0.15,
    (False, 'deferential'): 0.20,
    (False, 'non_deferential'): 0.27,
    (False, 'unclear'): 0.24}


@dataclasses.dataclass
class Simulation:
    """Fictional votes and the traits of the judges who cast them.

    Args:
        votes: the table of votes.
        traits: a table with a row for each appellate judge, labeled by the
            judge's number, with "party", "circuit", "ideology", "activism",
            "partisanship", and "independence".

    """

    votes: pd.DataFrame
    traits: pd.DataFrame


def simulate(
    seed: int = 7,
    cases: int = 9000,
    circuits: int = 3,
    judges: int = 14) -> Simulation:
    """Returns fictional votes of judges whose traits are known.

    Args:
        seed: seed of the random numbers. Defaults to 7.
        cases: number of appeals. Defaults to 9,000.
        circuits: number of circuits. Defaults to 3.
        judges: number of appellate judges of each circuit. Defaults to 14.

    Returns:
        The votes and the judges' traits.

    """
    random = np.random.default_rng(seed)
    rows = []
    for circuit in range(1, circuits + 1):
        for place in range(judges):
            party = 1.0 if random.random() < 0.55 else -1.0
            rows.append({
                'nid': circuit * 100 + place,
                'party': party,
                'circuit': circuit,
                'ideology': float(np.clip(
                    0.5 * party + random.normal(0, 0.35), -1, 1)),
                'activism': float(random.uniform(0, 0.12)),
                'partisanship': float(random.uniform(0, 0.12)),
                'independence': float(random.uniform(0, 1)),
                # Two senior judges of each circuit also sit elsewhere.
                'travels': place < 2})
    traits = pd.DataFrame(rows).set_index('nid')
    district = {
        circuit: random.choice([-1.0, 1.0], size = 20)
        for circuit in range(1, circuits + 1)}
    records = []
    for number in range(cases):
        circuit = int(random.integers(1, circuits + 1))
        own = traits.index[traits['circuit'] == circuit].to_numpy()
        panel = list(random.choice(own, size = 3, replace = False))
        if random.random() < 0.08:
            visitors = traits.index[
                traits['travels'] & (traits['circuit'] != circuit)]
            panel[2] = int(random.choice(visitors))
        criminal = bool(random.random() < 0.45)
        standard = str(random.choice(
            ['deferential', 'non_deferential', 'unclear'], p = [0.5, 0.3, 0.2]))
        district_party = float(random.choice(district[circuit]))
        preferences = {}
        for judge in panel:
            trait = traits.loc[judge]
            chance = _BASE[criminal, standard]
            deferring = standard == 'deferential'
            chance += trait['activism'] * deferring
            chance += 0.06 * trait['ideology'] * -district_party
            opposed = trait['party'] != district_party
            chance += trait['partisanship'] * (1 if opposed else -1) * deferring
            preferences[judge] = bool(random.random() < np.clip(chance, 0, 1))
        reversed_ = sum(preferences.values()) >= 2
        majority = [j for j in panel if preferences[j] == reversed_]
        author = int(random.choice(majority))
        for judge in panel:
            trait = traits.loc[judge]
            dissented = (
                preferences[judge] != reversed_
                and random.random() < 0.15 + 0.5 * trait['independence'])
            concurred = (
                not dissented
                and random.random() < 0.005 + 0.04 * trait['independence'])
            records.append({
                'case_id': f'c{number}',
                'judge_nid': judge,
                'judge': f'Judge {judge}',
                'judge_party': trait['party'],
                'judge_designated': trait['circuit'] != circuit,
                'court_num': circuit,
                'year': 2008 + number % 2,
                'type_criminal': criminal,
                'review_standard': standard,
                'outcome_reversal': reversed_,
                'judge_dissented': dissented,
                'judge_concurred': concurred,
                'judge_author': judge == author,
                'district_party': district_party})
    table = pd.DataFrame(records)
    table['vote_reversal'] = (
        table['outcome_reversal'] ^ table['judge_dissented'])
    table.index = pd.Index(
        [f'{c}-{i}' for i, c in enumerate(table['case_id'])], name = 'vote_id')
    return Simulation(
        votes = votes_module.describe_panels(table), traits = traits)


@pytest.fixture(scope = 'session')
def simulation() -> Simulation:
    """Returns fictional votes of judges whose traits are known.

    Returns:
        The simulation.

    """
    return simulate()
