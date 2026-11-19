"""Runs courtpy's commands, and the project's own, with its techniques.

`python -m coa_judicial_behavior` (or `coa-judicial-behavior`) is courtpy's
program (see `courtpy.cli`) with one more command, and with this project's
techniques available, because importing coa_judicial_behavior adds them to
the `amos` library:

* `coa-judicial-behavior judges` is courtpy's `judges` command, which makes
  the roster of judges that courtpy uses to identify the judges of each
  panel and the district judges, from the Federal Judicial Center's files,
  with each appointment's Judicial Common Space score. Here its careers are
  coded by this project's rules ("instructions/careers.csv") unless
  "--rulebook" names others.
* `coa-judicial-behavior scores VOTES` scores the judges of a saved table of
  votes (such as the one that a study exports) and saves the scores.

So `coa-judicial-behavior run studies/judicial_behavior.toml --export` works
like `courtpy run ...`, except that the study's settings can name this
project's techniques.

Contents:
    CAREERS: the path of the rules that code the judges' careers.
    main: runs a command.

"""

from __future__ import annotations

import argparse
import pathlib
import sys
from collections.abc import Sequence
from typing import Any

import pandas as pd
from courtpy import cli

from . import scores

CAREERS: pathlib.Path = (
    pathlib.Path(__file__).parent / 'instructions' / 'careers.csv')


def main(argv: Sequence[str] | None = None) -> int:
    """Runs a courtpy command or one of this project's commands.

    Args:
        argv: the command's arguments. Defaults to `None`, in which case the
            arguments of the program are used.

    Returns:
        0 if the command succeeded, and 1 if it failed.

    """
    return cli.main(
        argv, prog = 'coa-judicial-behavior',
        description = 'Score the judges of the federal courts of appeals.',
        add_commands = _add_commands)


""" Commands """


def _scores(arguments: argparse.Namespace) -> int:
    """Scores the judges of a table of votes ("coa-judicial-behavior scores").

    Args:
        arguments: the parsed arguments: "votes", "output", "method",
            "minimum", and "by".

    Raises:
        FileNotFoundError: if there is no file of votes.

    Returns:
        0.

    """
    source = pathlib.Path(arguments.votes)
    if not source.is_file():
        message = f'there is no table of votes at {source}'
        raise FileNotFoundError(message)
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


def _add_commands(commands: Any) -> None:
    """Adds this project's command to courtpy's, and sets its career rules.

    Args:
        commands: the subparsers of courtpy's program, whose `choices` has
            courtpy's commands by name.

    """
    commands.choices['judges'].set_defaults(rulebook = str(CAREERS))
    scored = commands.add_parser(
        'scores', help = 'score the judges of a saved table of votes')
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


if __name__ == '__main__':
    sys.exit(main())
