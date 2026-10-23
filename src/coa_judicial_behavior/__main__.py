"""Runs the project's commands.

`python -m coa_judicial_behavior` (or `coa-judicial-behavior`) has two
commands of its own:

* `coa-judicial-behavior judges` makes the roster of judges that courtpy
  uses to identify the judges of each panel and the district judges, from
  the Federal Judicial Center's files, with each appointment's Judicial
  Common Space score and the careers that the studies tested (coded by the
  rules in "instructions/careers.csv"), and saves it where courtpy looks for
  it.
* `coa-judicial-behavior scores VOTES` scores the judges of a saved table of
  votes (such as the one that a study exports) and saves the scores.

Every other command is courtpy's (such as `run`, `parse`, `download`, and
`rules`), with this project's techniques available, because importing
coa_judicial_behavior adds them to the `amos` library. So
`coa-judicial-behavior run studies/judicial_behavior.toml --export` works
like `courtpy run ...`, except that the study's settings can name them.

Contents:
    CAREERS: the path of the rules that code the judges' careers.
    main: runs a command.

"""

from __future__ import annotations

import argparse
import logging
import pathlib
import sys
from collections.abc import Sequence

import pandas as pd
import requests
from courtpy import cli, judges

from . import scores

CAREERS: pathlib.Path = (
    pathlib.Path(__file__).parent / 'instructions' / 'careers.csv')
_COMMANDS: dict[str, str] = {
    'judges': "make the roster of judges from the Federal Judicial Center's "
              'files, with their careers and Judicial Common Space scores',
    'scores': 'score the judges of a saved table of votes'}


def main(argv: Sequence[str] | None = None) -> int:
    """Runs one of this project's commands, or else a courtpy command.

    Args:
        argv: the command's arguments. Defaults to `None`, in which case the
            arguments of the program are used.

    Returns:
        0 if the command succeeded, and 1 if it failed.

    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] in {'-h', '--help'}:
        print('coa-judicial-behavior has two commands of its own:')
        for name, purpose in _COMMANDS.items():
            print(f'  {name:9}{purpose}')
        print('Every other command is one of courtpy:\n')
    if arguments[:1] and arguments[0] in _COMMANDS:
        parsed = _parser().parse_args(arguments)
        logging.basicConfig(
            level = logging.INFO, format = '%(levelname)s: %(message)s')
        try:
            return int(parsed.command(parsed) or 0)
        except (
            FileNotFoundError, KeyError, LookupError, OSError, ValueError,
            requests.RequestException) as error:
            print(f'coa-judicial-behavior: {error}', file = sys.stderr)
            return 1
    return cli.main(arguments)


""" Commands """


def _judges(arguments: argparse.Namespace) -> int:
    """Makes and saves the roster of judges ("coa-judicial-behavior judges").

    Args:
        arguments: the parsed arguments: "update" (whether to download the
            Federal Judicial Center's files again) and "no_jcs".

    Returns:
        0.

    """
    roster = judges.Roster.from_fjc(
        update = arguments.update, jcs = not arguments.no_jcs,
        rulebook = CAREERS)
    path = roster.save()
    people = roster.data['nid'].nunique()
    print(f'A roster of {people} judges was saved to {path}')
    return 0


def _scores(arguments: argparse.Namespace) -> int:
    """Scores the judges of a table of votes ("coa-judicial-behavior scores").

    Args:
        arguments: the parsed arguments: "votes", "output", "method",
            "minimum", and "by".

    Returns:
        0.

    """
    source = pathlib.Path(arguments.votes)
    votes = (
        pd.read_parquet(source) if source.suffix == '.parquet'
        else pd.read_csv(source, low_memory = False))
    table = scores.score_judges(
        votes, method = arguments.method, minimum = arguments.minimum,
        by = arguments.by)
    output = pathlib.Path(arguments.output)
    output.parent.mkdir(parents = True, exist_ok = True)
    table.to_csv(output, index = False)
    qualified = int(table['qualified'].sum())
    print(f'{len(table)} judges ({qualified} with enough interactions to '
          f'define the scales) were scored and saved to {output}')
    return 0


""" Private Functions """


def _parser() -> argparse.ArgumentParser:
    """Builds the parser of this project's own commands.

    Returns:
        The parser. The function for each command is its "command".

    """
    parser = argparse.ArgumentParser(
        prog = 'coa-judicial-behavior',
        description = 'Score the judges of the federal courts of appeals.')
    commands = parser.add_subparsers(title = 'commands', required = True)
    roster = commands.add_parser('judges', help = _COMMANDS['judges'])
    roster.add_argument(
        '--update', action = 'store_true',
        help = "download the Federal Judicial Center's files again")
    roster.add_argument(
        '--no-jcs', action = 'store_true',
        help = 'leave out the Judicial Common Space scores')
    roster.set_defaults(command = _judges)
    scored = commands.add_parser('scores', help = _COMMANDS['scores'])
    scored.add_argument(
        'votes', help = 'a CSV or parquet file of votes, one row for each '
                        'judge on each case, as review_votes makes them')
    scored.add_argument(
        '--output', default = 'results/judge_scores.csv',
        help = 'file to save the scores in. Default: results/judge_scores.csv')
    scored.add_argument(
        '--method', choices = scores.METHODS, default = 'typology',
        help = "'typology' (the 2013 article's methods) or 'original' (each "
               "score's first article). Default: typology")
    scored.add_argument(
        '--minimum', type = int, default = 200,
        help = 'fewest interactions for a judge to define the scales. '
               'Default: 200')
    scored.add_argument(
        '--by', help = 'a column whose values are scored separately, such '
                       'as year')
    scored.set_defaults(command = _scores)
    return parser


if __name__ == '__main__':
    sys.exit(main())
