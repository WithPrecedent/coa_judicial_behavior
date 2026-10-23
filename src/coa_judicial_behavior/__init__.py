"""Ideology, activism, partisanship, and independence of appellate judges.

The scores follow the methods of Corey Rayburn Yung's studies of the judges
of the federal courts of appeals (see `coa_judicial_behavior.scores`), from
opinions that courtpy collects from CourtListener and codes. Importing the
package adds its techniques to the `amos` library, so a study's settings can
name them: `code_review`, `code_district_judge`, `review_votes`,
`score_judges`, and `validate_scores`.

Contents:
    CodeDistrictJudge: finds the district judge whose judgment each case
        reviews.
    CodeReview: sorts each case by its standard of review.
    PREDICTORS: the variables for control and prediction that the scores
        add to the votes.
    Project: `amos.Project` (which courtpy offers under the same name), which
        loads and analyzes the cases that a settings file describes.
    ReviewVotes: makes the table of votes, with each vote's super-panel.
    RULEBOOK: the path of the rules that find what the scores need in each
        opinion.
    ScoreJudges: scores the judges and adds the predictors to the votes.
    Typology: the judging styles of the judges.
    ValidateScores: repeats the studies' tests of the scores.
    add_predictors: adds the scores to a table of votes.
    classify: sorts judges into judging styles.
    score_judges: returns the four scores of every judge.
    validate: returns the studies' tests of the scores.

"""

from __future__ import annotations

__version__ = '0.0.1'

__author__: str = 'Corey Rayburn Yung'

__all__: list[str] = [
    'PREDICTORS',
    'RULEBOOK',
    'CodeDistrictJudge',
    'CodeReview',
    'Project',
    'ReviewVotes',
    'ScoreJudges',
    'Typology',
    'ValidateScores',
    'add_predictors',
    'classify',
    'predictions',
    'score_judges',
    'scores',
    'typology',
    'validate',
    'votes',
]

from courtpy import Project

from . import predictions, scores, typology, votes
from .predictions import (
    PREDICTORS,
    ScoreJudges,
    ValidateScores,
    add_predictors,
    validate,
)
from .scores import score_judges
from .typology import Typology, classify
from .votes import RULEBOOK, CodeDistrictJudge, CodeReview, ReviewVotes
