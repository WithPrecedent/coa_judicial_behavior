# Changelog

All notable changes to this project will be documented in this file.

<!-- insertion marker -->

## Unreleased

* The project uses courtpy 0.4.0 and amos 0.10.1. pyarrow is no longer a
  direct dependency (amos brings it).
* **Breaking:** the rules that found the district judge, the origin of the
  appeal, immigration review, and two more deferential standards
  (`instructions/review.csv`) are part of courtpy's "federal" rulebook now,
  so the file and `RULEBOOK` are gone, and the study's settings name only
  "federal".
* The settings use courtpy's new names for its coders: `code_panels` (for
  `code_judges`) and `add_politics` (for `code_politics`).
* `coa-judicial-behavior` is courtpy's program (`courtpy.cli.main`) with
  this project's `scores` command added, so `coa-judicial-behavior judges`
  is courtpy's `judges` command (with its options, such as
  `--martin-quinn` and `--output`), coding careers with
  `instructions/careers.csv` by default.
* The scores, predictions, and votes use courtpy's helpers for tables of
  cases (`column_as_flags`, `flags_as_numbers`, `select_whole_cases`, and
  `split_cell`) and settings (`listify` and `to_bool`) in place of their own
  copies. A `train` query that does not select rows raises courtpy's
  `ValueError`, which names the query (courtpy 0.4.1).

## 0.0.1

* Created the repository from the `snickerdoodle` template.
* Added the four scores of Corey Rayburn Yung's studies of the judges of the
  federal courts of appeals (`score_judges`): ideology (2010), activism
  (2011), partisanship and independence (2012), with the 2013 revisions
  (`method = "typology"`, the default) or each score's first article
  (`method = "original"`), and their case-mix, super-panel, circuit, and
  scaling adjustments.
* Added the judging styles of *A Typology of Judging Styles* (`classify`), by
  Ward's cluster analysis, with the article's test that the styles are
  distinct.
* Added the variables for control and prediction (`add_predictors`) and the
  studies' probit tests of the scores (`validate_scores`), on votes left out
  of the scores.
* Added rules that find the district judge, the origin of the appeal,
  immigration review, and two more deferential standards in CourtListener
  opinions (`instructions/review.csv`), and rules that code the judges'
  careers (`instructions/careers.csv`).
* Added the techniques `code_review`, `code_district_judge`, and
  `review_votes`, the commands `judges` and `scores`, and the study
  `studies/judicial_behavior.toml`.
