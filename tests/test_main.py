"""Tests the package and its commands."""

from __future__ import annotations

import pathlib

import courtpy
import pandas as pd
import pytest
from conftest import Simulation

import coa_judicial_behavior
from coa_judicial_behavior import __main__ as commands


def test_coa_judicial_behavior() -> None:
    assert coa_judicial_behavior.__version__ == '0.0.1'
    assert coa_judicial_behavior.RULEBOOK.is_file()
    assert commands.CAREERS.is_file()


def test_scores_command(
    simulation: Simulation,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / 'votes.csv'
    simulation.votes.to_csv(source)
    output = tmp_path / 'scores.csv'
    code = commands.main([
        'scores', str(source), '--output', str(output), '--minimum', '100'])
    assert code == 0
    table = pd.read_csv(output)
    assert len(table) == len(simulation.traits)
    assert {'ideology', 'activism', 'partisanship', 'independence'} <= set(
        table.columns)
    assert 'were scored and saved' in capsys.readouterr().out
    assert commands.main(['scores', str(tmp_path / 'missing.csv')]) == 1


def test_judges_command(
    monkeypatch: pytest.MonkeyPatch,
    roster: courtpy.judges.Roster,
    capsys: pytest.CaptureFixture[str]) -> None:
    settings: dict[str, object] = {}

    def from_fjc(**kwargs: object) -> courtpy.judges.Roster:
        settings.update(kwargs)
        return roster

    monkeypatch.setattr(courtpy.judges.Roster, 'from_fjc', from_fjc)
    assert commands.main(['judges']) == 0
    assert settings['rulebook'] == commands.CAREERS
    assert settings['jcs'] is True
    assert 'A roster of 17 judges' in capsys.readouterr().out
    # The project's career rules code the fictional careers.
    coded = roster.data.set_index('nid')
    assert coded.loc[104, 'state_judge']
    assert coded.loc[102, 'justice_department']
    assert coded.loc[205, 'law_professor']
    assert not coded.loc[101, 'justice_department']


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        commands.main(['--help'])
    assert 'two commands of its own' in capsys.readouterr().out
