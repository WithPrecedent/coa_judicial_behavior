# coa-judicial-behavior

| | |
| --- | --- |
| Version | [![PyPI Latest Release](https://img.shields.io/pypi/v/coa-judicial-behavior.svg?style=for-the-badge&color=cornflowerblue&label=PyPI&logo=PyPI&logoColor=yellow)](https://pypi.org/project/coa-judicial-behavior/) [![GitHub Latest Release](https://img.shields.io/github/v/tag/WithPrecedent/coa_judicial_behavior?style=for-the-badge&color=forestgreen&label=GitHub&logo=github)](https://github.com/WithPrecedent/coa_judicial_behavior/releases) |
| Status | [![Build Status](https://img.shields.io/github/actions/workflow/status/WithPrecedent/coa_judicial_behavior/ci.yml?style=for-the-badge&branch=main&color=cadetblue&label=Tests&logo=pytest)](https://github.com/WithPrecedent/coa_judicial_behavior/actions/workflows/ci.yml?query=branch%3Amain) [![Code Coverage](https://img.shields.io/codecov/c/github/WithPrecedent/coa_judicial_behavior?style=for-the-badge&color=cadetblue&label=Coverage&logo=codecov)](https://app.codecov.io/gh/WithPrecedent/coa_judicial_behavior) [![Development Status](https://img.shields.io/badge/Development-Active-seagreen?style=for-the-badge&logo=git)](https://www.repostatus.org/#active) [![Project Stability](https://img.shields.io/pypi/status/coa-judicial-behavior?style=for-the-badge&logo=pypi&label=Stability&logoColor=yellow)](https://pypi.org/project/coa-judicial-behavior/) |
| Documentation | [![Hosted By](https://img.shields.io/badge/Hosted_by-Github_Pages-blue?style=for-the-badge&color=forestgreen&logo=github)](https://WithPrecedent.github.io/coa_judicial_behavior) |
| Tools | [![Documentation](https://img.shields.io/badge/MkDocs-magenta?style=for-the-badge&color=deepskyblue&logo=markdown&labelColor=gray)](https://squidfunk.github.io/mkdocs-material/) [![Linter](https://img.shields.io/endpoint?style=for-the-badge&url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Type Checker](https://img.shields.io/badge/mypy-steelblue?style=for-the-badge&logo=python&logoColor=white&labelColor=gray)](https://mypy-lang.org/) [![Dependency Manager](https://img.shields.io/badge/uv-mediumpurple?style=for-the-badge&logo=uv&labelColor=gray)](https://docs.astral.sh/uv/) [![Pre-commit](https://img.shields.io/badge/pre--commit-darkolivegreen?style=for-the-badge&logo=pre-commit&logoColor=white&labelColor=gray)](https://pre-commit.com/) [![CI](https://img.shields.io/badge/GitHub_Actions-forestgreen?style=for-the-badge&logo=githubactions&labelColor=gray&logoColor=white)](https://github.com/features/actions) [![Editor Settings](https://img.shields.io/badge/Editor_Config-paleturquoise?style=for-the-badge&logo=editorconfig&labelColor=gray)](https://editorconfig.org/) [![Repository Template](https://img.shields.io/badge/snickerdoodle-bisque?style=for-the-badge&logo=cookiecutter&labelColor=gray)](https://www.github.com/WithPrecedent/snickerdoodle) [![Dependency Maintainer](https://img.shields.io/badge/dependabot-forestgreen?style=for-the-badge&logo=dependabot&logoColor=white&labelColor=gray)](https://github.com/dependabot) |
| Compatibility | [![Compatible Python Versions](https://img.shields.io/pypi/pyversions/coa-judicial-behavior?style=for-the-badge&color=cornflowerblue&label=Python&logo=python&logoColor=yellow)](https://pypi.org/project/coa-judicial-behavior/) [![Linux](https://img.shields.io/badge/Linux-lightseagreen?style=for-the-badge&logo=linux&labelColor=gray&logoColor=white)](https://www.linux.org/) [![MacOS](https://img.shields.io/badge/MacOS-antiquewhite?style=for-the-badge&logo=apple&labelColor=gray)](https://www.apple.com/macos/) [![Windows](https://img.shields.io/badge/Windows-blue?style=for-the-badge)](https://www.microsoft.com/en-us/windows?r=1) |
| Stats | [![PyPI Download Rate (per month)](https://img.shields.io/pypi/dm/coa-judicial-behavior?style=for-the-badge&color=cornflowerblue&label=Downloads%20💾&logo=pypi&logoColor=yellow)](https://pypi.org/project/coa-judicial-behavior/) [![GitHub Stars](https://img.shields.io/github/stars/WithPrecedent/coa_judicial_behavior?style=for-the-badge&color=forestgreen&label=Stars%20⭐&logo=github)](https://github.com/WithPrecedent/coa_judicial_behavior/stargazers) [![GitHub Contributors](https://img.shields.io/github/contributors/WithPrecedent/coa_judicial_behavior?style=for-the-badge&color=forestgreen&label=Contributors%20🙋&logo=github)](https://github.com/WithPrecedent/coa_judicial_behavior/graphs/contributors) [![GitHub Issues](https://img.shields.io/github/issues/WithPrecedent/coa_judicial_behavior?style=for-the-badge&color=forestgreen&label=Issues%20📘&logo=github)](https://github.com/WithPrecedent/coa_judicial_behavior/issues) [![GitHub Forks](https://img.shields.io/github/forks/WithPrecedent/coa_judicial_behavior?style=for-the-badge&color=forestgreen&label=Forks%20🍴&logo=github)](https://github.com/WithPrecedent/coa_judicial_behavior/forks) |
| | |

-----


## What is coa-judicial-behavior?

Debates about judges reach for two labels, "liberal" and "conservative," and
empirical research has mostly measured one dimension, ideology, often by no
more than the party of the president who appointed a judge. A series of
studies of the judges of the federal courts of appeals measured four traits
from what judges actually do, and found that they are distinct: ideology,
activism, partisanship, and independence. This project computes those four
scores for every judge of the courts of appeals from the opinions on
[CourtListener](https://www.courtlistener.com), collected and coded with
[courtpy](https://github.com/WithPrecedent/courtpy), and adds them (and the
variables made from them) to every vote, for control and prediction.

| Score | Study | What it measures | Scale |
| --- | --- | --- | --- |
| Ideology | Corey Rayburn Yung, *Judged by the Company You Keep: An Empirical Study of the Ideologies of Judges on the United States Courts of Appeals*, 51 B.C. L. Rev. 1133 (2010) | How much more often a judge agrees with judges appointed by Republican presidents (copanelists, and the district judges whose judgments the judge affirms) than with those appointed by Democratic presidents. | -100 (liberal) to 100 (conservative) |
| Activism | Corey Rayburn Yung, *Flexing Judicial Muscle: An Empirical Study of Judicial Activism in the Federal Courts*, 105 Nw. U. L. Rev. 1 (2011) | How much more often a judge reverses under deferential standards of review than the judge's own rate under de novo review would predict: failing to defer when the formal model of law says to. | 0 to 100 |
| Partisanship | Corey Rayburn Yung, *Beyond Ideology: An Empirical Study of Partisanship and Independence in the Federal Courts*, 80 Geo. Wash. L. Rev. 505 (2012) | Whether a judge applies a neutral rule (the standard of review) with more deference to district judges appointed by the judge's own party. | 0 to 100 |
| Independence | *Beyond Ideology* (2012) | How often a judge provokes dissents and separate concurrences beyond what the judge's ideological distance from the circuit predicts. | 0 to 100 |

*A Typology of Judging Styles*, 107 Nw. U. L. Rev. 1757 (2013), revised all
four together and sorted the judges into nine judging styles by Ward's
cluster analysis of the scores: Trailblazing, Consensus Building, Stalwart,
Regulating, Steadfast, Collegial, Incrementalist, Minimalist, and Error
Correcting. This project follows the 2013 methods by default
(`method = "typology"`), and each score's first article with
`method = "original"`.

## Why use coa-judicial-behavior?

* **Faithful.** Each score follows the formulas and adjustments of the
  articles: case mix, the "super-panel" of copanelists and district judge,
  circuit differences measured by judges who travel between circuits, and
  common scales. The tests reproduce the worked examples of the articles
  (such as Judge Diane Wood's Activism Differential).
* **Every opinion, every year.** The studies hand-coded the 30,000 votes of
  2008. CourtListener has the published and unpublished opinions of every
  year, and courtpy codes them by rules in spreadsheets, so the scores can be
  computed for any period (or each year separately) and replicated.
* **Ready to predict with.** The scores, the panel's scores, and the
  interactions the articles tested (such as partisanship toward a district
  judge of the other party) are added to every vote, and the studies'
  probit tests are repeated on votes that the scores never saw.

## Methods

Each score starts from a table of votes, with one row for each judge on each
case: whether the judge voted to reverse, dissented, or concurred; the
standard of review ("deferential" for clear error, abuse of discretion,
arbitrary and capricious, substantial evidence, or plain error;
"non_deferential" for de novo review; "unclear" for both or neither); and the
judge's super-panel: the two copanelists and the district judge, and the
parties of the presidents who appointed them (such as "RR-D").

| Score | Raw score |
| --- | --- |
| Ideology | Panel Score: rate of agreement with Republican-appointed copanelists less the rate with Democratic-appointed ones. District Score: the same for affirmances of district judges, weighting each standard of review by the inverse of its rate of reversal. |
| Activism | Reversal rate under deferential standards less the reversal rate under de novo review. |
| Partisanship | (Deferential reversal rate of district judges of the other party less that of the judge's own party) less (the same under nondeferential review). |
| Independence | Rate of dissents plus rate of concurrences (the judge's own, and those against the judge's opinions) less the rates that a regression on the judge's distance from the circuit's mean ideology predicts. |

Then every score is adjusted, as the articles adjusted them:

| Adjustment | How |
| --- | --- |
| Case mix | Each rate is computed for criminal and civil cases separately and weighted by the average judge's shares. Thin cells fall back on the judge's rate in both kinds of cases, then on all judges'. |
| Super-panel effects | The score that a blank-slate judge would have from the six alignments (RR-R, RR-D, DR-R, DR-D, DD-R, DD-D) that the judge happened to sit in is subtracted. |
| Circuit | Judges who sat in more than one circuit are assumed to keep their traits. Their pooled score in each circuit, less their vote-weighted overall scores, is the circuit's differential, which is subtracted per judge (2010, 2011) or per vote (2012, 2013). |
| Scale | The judges with at least 200 interactions (two copanelists and a district judge per vote) define the scales. Independence is put on a logarithmic scale first. |

The [advanced user guide](https://WithPrecedent.github.io/coa_judicial_behavior/advanced)
gives every formula, the differences between the two methods, and the few
places where the articles left a choice open and how this project made it.

## The data

courtpy extracts the opinions of the twelve regional circuits from
CourtListener's bulk data and parses them with its federal rules, which find
the judges of the panel, who wrote, joined, concurred, or dissented, the
disposition, the parties, and four standards of review. This project's
rules, in
[`instructions/review.csv`](https://github.com/WithPrecedent/coa_judicial_behavior/blob/main/src/coa_judicial_behavior/instructions/review.csv),
add what the scores need:

| Variable | Meaning |
| --- | --- |
| `district_judges` | The district judge's name, from the lines about the court appealed from, in each circuit's form ("Catherine C. Blake, District Judge", "(Hon. Lewis A. Kaplan, Judge)", "District Judge: Honorable Joel A. Pisano", and others). |
| `review_district`, `review_agency` | Whether the appeal came from a district court, or is a petition to review an agency. |
| `review_immigration` | Immigration review, which the studies left out (as they left out habeas corpus). |
| `standard_substantial_evidence`, `standard_plain_error`, `standard_named` | Two deferential standards that courtpy does not find, and words that announce any standard of review. |

The techniques (which importing the package adds to the `amos` library) then
build the votes:

| Technique | Adds |
| --- | --- |
| `code_district_judge` | The district judge, found among the district judges of the case's circuit who were serving that year (`district_judge`, `district_judge_nid`), with the party of the appointing president (`district_party`) and Judicial Common Space score (`district_jcs`). |
| `code_review` | `review_standard`, `review_deferential`, `review_de_novo`, `review_has_standard`, `review_excluded` (habeas corpus and immigration), and `review_of_district`. |
| `review_votes` | courtpy's table of votes (one row for each judge on each case, with `vote_reversal`, `judge_dissented`, `judge_concurred`, `judge_author`, and each judge's attributes), with the super-panel: `copanel`, `alignment`, `colleagues_republican`, `district_opposed`, and `panel_unanimous`. |
| `score_judges` | The table of scores and the judging styles (see below), and the predictors on every vote. |
| `validate_scores` | The studies' tests of the scores. |

The roster of judges comes from the Federal Judicial Center's biographical
directory (through courtpy and
[fjc-biographies](https://github.com/WithPrecedent/fjc_biographies)), with
each appointment's Judicial Common Space score and the careers that the
studies tested, coded by the rules in
[`instructions/careers.csv`](https://github.com/WithPrecedent/coa_judicial_behavior/blob/main/src/coa_judicial_behavior/instructions/careers.csv):
prosecutor, public defender, law clerk, law professor, Department of
Justice, state judge, legislative and executive service, and others.

Two differences from the studies' data are worth knowing. The studies coded
2008 from LexisNexis, by hand and later partly by software, and their coders
resolved which standard was actually applied when an opinion named several;
here an opinion that names both kinds is "unclear." And some circuits do not
name the district judge in their opinions (the Fifth Circuit's unpublished
opinions often give only the district court's docket number); those votes
count toward the Panel Score and independence, but not toward the scores
that need the district judge.

## The variables

`score_judges` adds a table, "score_judges", with a row for each judge:

| Column | Meaning |
| --- | --- |
| `judge_nid`, `judge`, `judge_party`, `circuit` | The judge, the party of the appointing president (-1 or 1), and the judge's home circuit. |
| `votes`, `panel_interactions`, `district_interactions`, `interactions`, `traveling_votes`, `qualified` | How much the judge was observed, and whether the judge defines the scales (at least `minimum` interactions). |
| `ideology`, `activism`, `partisanship`, `independence` | The four scores. `ideological` is the absolute Ideology Score. |
| `ideology_panel`, `ideology_district`, `ideology_raw` | The Panel, District, and raw Ideology Scores. |
| `{score}_raw`, `{score}_super_panel`, `{score}_circuit`, `{score}_adjusted` | Each step of the adjustments, for ideology, activism, and partisanship. |
| `dissent_rate`, `concurrence_rate`, `expected_dissent_rate`, `expected_concurrence_rate`, `independence_raw`, `independence_log` | The steps of the Independence Score. |
| `cluster`, `style` | The judge's judging style. |

And every vote gets these variables for control and prediction:

| Variable | Meaning |
| --- | --- |
| `judge_ideology`, `judge_ideological`, `judge_activism`, `judge_partisanship`, `judge_independence`, `judge_style`, `judge_scored` | The judge's scores and style, and whether the judge had enough interactions to define the scales. |
| `colleagues_{score}` | The mean score of the judge's copanelists. |
| `panel_ideology_median`, `panel_ideology_net` | The panel's median and summed Ideology Scores, the measures that the 2010 article tested. |
| `panel_activism_mean`, `panel_partisanship_mean`, `panel_independence_mean`, `panel_independence_max` | The panel's other scores. |
| `ideological_distance` | How far the judge's ideology is from the copanelists'. |
| `circuit_ideology`, `circuit_deviation` | The circuit's mean ideology, and how far the judge is from it (which predicts separate opinions). |
| `ideological_pressure` | The ideology (as -1 to 1) times the district judge's side: positive when a conservative judge reviews a Democratic appointee or a liberal judge a Republican one. |
| `partisan_pressure` | The centered Partisanship Score times 1 for a district judge of the other party and -1 for one of the same party. |
| `activist_pressure` | The centered Activism Score under a deferential standard (0 otherwise). |
| `expected_reversal` | The rate of reversal of all judges in the vote's alignment, case type, and standard: the super-panel effect itself. |
| `concurred_only` | Whether the judge concurred without dissenting. |
| `holdout` | Whether the vote was left out of the scores. |

The controls that the articles used come with the votes: the case type,
the standard of review, the circuit, the year, publication, the super-panel,
and each judge's attributes from the roster (`judge_party`, `judge_jcs`,
`judge_woman`, `judge_minority`, `judge_age`, `judge_senior`,
`judge_designated`, and the careers, such as `judge_law_professor` and
`judge_justice_department`).

## Judging styles

`score_judges` sorts the judges who define the scales into styles by Ward's
cluster analysis of the absolute Ideology Score and the Activism,
Partisanship, and Independence Scores, as the 2013 article did, and names
each cluster for the article's style whose profile its mean scores are
closest to. The "typology" table gives each cluster's mean scores, in points
and in standard deviations, and how far it is from its style's profile;
"typology_differences" is the article's test that every pair of clusters
differs by at least one standard deviation in some score. The names are a
guide to reading the clusters: the clusters of other judges and years need
not look like the article's.

## Testing the scores

`validate_scores` repeats the articles' tests, as probit regressions with
standard errors clustered by case, on the votes left out of the scores:

| Test | Outcome | Measures |
| --- | --- | --- |
| `civil_rights` (2010) | Whether a plaintiff under Title VII, section 1983, or the ADA won | The panel's median and net Ideology Scores, against its median Judicial Common Space score and the mean party of its appointing presidents. |
| `dissent`, `concurrence` (2012) | Whether the judge dissented or concurred | The Independence Score, against the absolute Ideology and Judicial Common Space scores. |
| `partisan_reversal` (2012) | Whether the judge voted to reverse, under a deferential standard | `partisan_pressure`, against `ideological_pressure` and the district judge's party alone. |
| `activist_reversal` (2011) | The same | The Activism Score. |

## Getting started

### Requirements

The project requires Python 3.11 or later and
[uv](https://docs.astral.sh/uv/). It runs on Linux, macOS, and Windows. The
first run downloads CourtListener's bulk files of opinions, clusters, and
dockets (about 63 GB, kept outside the project and reused) unless courtpy has
already downloaded them, and the Federal Judicial Center's files of judges.
No API key is needed.

### Installation

In the project's folder:

```sh
uv sync
```

### Usage

Make the roster of judges once (with the careers and Judicial Common Space
scores), and then run the study:

```sh
uv run coa-judicial-behavior judges
uv run coa-judicial-behavior run studies/judicial_behavior.toml --export
```

The study,
[`studies/judicial_behavior.toml`](https://github.com/WithPrecedent/coa_judicial_behavior/blob/main/studies/judicial_behavior.toml),
scores the judges from the votes through 2020, tests the scores on the later
votes, estimates a probit model of reversal with circuit and year fixed
effects, and compares models that predict the later votes. Every choice is a
setting there, such as `method`, `minimum`, the years scored, or
`by = "year"` to score each year separately, as the studies scored 2008.

In Python:

```python
import coa_judicial_behavior

project = coa_judicial_behavior.Project.create("studies/judicial_behavior.toml")
scores = project.result.tables["score_judges"]
print(scores[scores["qualified"]].sort_values("activism").tail(10))
print(project.result.tables["typology"])
print(project.result.tables["validate_scores"])
```

To score a table of votes that is already saved (one row for each judge on
each case, as `review_votes` makes it):

```python
import pandas as pd
import coa_judicial_behavior

votes = pd.read_parquet("votes.parquet")
scores = coa_judicial_behavior.score_judges(votes, method = "typology", by = "year")
styles = coa_judicial_behavior.classify(scores[scores["year"] == 2008])
predictors = coa_judicial_behavior.add_predictors(votes, scores, by = "year")
```

or from a terminal:

```sh
uv run coa-judicial-behavior scores votes.parquet --output results/judge_scores.csv --by year
```

Every other command is courtpy's (such as `download`, `parse`, and `rules`),
with this project's techniques available.

### Layout

| Path | Holds |
| --- | --- |
| `studies/judicial_behavior.toml` | The settings of the study. |
| `src/coa_judicial_behavior/instructions/` | The rules that find the district judge and the review (`review.csv`), and that code the judges' careers (`careers.csv`). |
| `src/coa_judicial_behavior/votes.py` | `code_review`, `code_district_judge`, and `review_votes`, which make the votes. |
| `src/coa_judicial_behavior/scores.py` | `score_judges`, the four scores. |
| `src/coa_judicial_behavior/typology.py` | `classify`, the judging styles. |
| `src/coa_judicial_behavior/predictions.py` | `add_predictors`, `score_judges` (the technique), and `validate_scores`. |
| `tests/` | Tests, with fictional judges and cases, including a simulation of judges whose traits are known. |

## Contributing

Contributors are always welcome. Feel free to grab an [issue](https://www.github.com/WithPrecedent/coa_judicial_behavior/issues) to work on or make a suggested improvement. If you wish to contribute, please read the [Contribution Guide](https://www.github.com/WithPrecedent/coa_judicial_behavior/blob/main/CONTRIBUTING.md) and [Code of Conduct](https://www.github.com/WithPrecedent/coa_judicial_behavior/blob/main/CODE_OF_CONDUCT.md).

## Similar Projects

* [courtpy](https://github.com/WithPrecedent/courtpy), which collects and
  codes the opinions, and [amos](https://github.com/WithPrecedent/amos),
  which runs the analysis.
* [judicial-common-space](https://github.com/WithPrecedent/judicial_common_space),
  the Judicial Common Space scores that the studies compared their scores
  with.
* [appellate-roulette](https://github.com/WithPrecedent/appellate_roulette),
  which asks whether the draw of judges changes the outcome of criminal
  appeals.

## Acknowledgments

The opinions come from CourtListener, a project of the [Free Law
Project](https://free.law), and the judges' biographies from the [Federal
Judicial Center](https://www.fjc.gov).

## License

Use of this repository is authorized under the [Apache Software License 2.0](https://www.github.com/WithPrecedent/coa_judicial_behavior/blob/main/LICENSE).
