# Tutorial

This tutorial computes the four scores for the judges of the federal courts
of appeals, from the opinions on CourtListener to a table of scores.

## 1. Install

In the project's folder:

```sh
uv sync
```

## 2. Make the roster of judges

The roster identifies the judges of each panel and the district judges, with
the party of the president who appointed each, their careers, and their
Judicial Common Space scores. It downloads three small files from the Federal
Judicial Center and the scores' sources, and saves the roster where courtpy
looks for it:

```sh
uv run coa-judicial-behavior judges
```

## 3. Try the rules on a few cases

Before parsing every opinion, extract a few and check what the rules find:

```sh
uv run coa-judicial-behavior download bulk --courts ca4 --start 2019-01-01 --end 2019-01-31 --folder data/court_listener
uv run coa-judicial-behavior parse data/court_listener --rulebooks federal src/coa_judicial_behavior/instructions/review.csv --output data/sample.csv
```

In `data/sample.csv`, `district_judges` should name the district judge of
most appeals from district courts, and the `standard_...` columns the
standards of review.

## 4. Run the study

```sh
uv run coa-judicial-behavior run studies/judicial_behavior.toml --export
```

The first run extracts every opinion of the twelve regional circuits since
2008 (a few hours), parses and codes them, and saves the coded appeals in
`data/appeals.parquet`, which later runs reuse. The results are exported to
`results/`:

| Table | Holds |
| --- | --- |
| `score_judges` | A row for each judge: the four scores, each step of their adjustments, and the judging style. |
| `typology`, `typology_differences` | The judging styles and the article's test that they are distinct. |
| `validate_scores` | The studies' tests of the scores on votes after 2020. |
| `fixest_coefficients` | A probit model of reversal with circuit and year fixed effects. |
| `analyst_comparison`, `scorecard`, `permutation_importance` | How well models predict the votes after 2020, and which variables matter most. |

## 5. Change the study

Every choice is a setting in `studies/judicial_behavior.toml`:

* `method = "original"` follows each score's first article instead of the
  2013 revision.
* `by = "year"` scores each year separately, as the studies scored 2008
  (with a lower `minimum`, such as 100, for small circuits).
* `train` sets the votes that the scores come from, and so the votes they
  are tested on.
* Add `and court_num != 12` to the query of `filter_rows` to leave out the
  D.C. Circuit, as the studies did.

Delete `data/appeals.parquet` after changing the rules, the roster, or the
loader's parameters, so that the opinions are parsed again.
