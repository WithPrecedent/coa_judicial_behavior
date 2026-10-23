# Changelog

All notable changes to this project will be documented in this file.

<!-- insertion marker -->

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
