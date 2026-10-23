"""Sorts judges into judging styles by their four scores.

*A Typology of Judging Styles*, 107 Nw. U. L. Rev. 1757 (2013), grouped the
178 judges with at least 200 interactions by Ward's cluster analysis of four
scores, each from 0 to 100: the Activism, Independence, and Partisanship
Scores and the absolute value of the Ideology Score (so that a judge at -60
and one at 60 are alike in how ideological they are). A group counted as a
style only if its mean differed from every other group's by at least one
standard deviation in at least one score, which left nine styles. The
article named them from their mean scores:

| Style | Ideological | Activism | Partisanship | Independence |
| --- | --- | --- | --- | --- |
| Trailblazing | High | Low | Low | High |
| Consensus Building | High | Below average | Below average | Lowest |
| Stalwart | Highest | Highest | Highest | Below average |
| Regulating | Average | Above average | High | Above average |
| Steadfast | Average | Elevated | Average | Highest |
| Collegial | Below average | Below average | Below average | Below average |
| Incrementalist | Slightly below | Slightly below | Elevated | Below average |
| Minimalist | Average | Lowest | Average | Slightly above |
| Error Correcting | Slightly below | High | Slightly below | Average |

`classify` repeats the analysis (with scipy's Ward linkage, where the article
used Stata's) and names each group for the style whose profile is closest to
the group's standardized mean scores, matching each style to one group. The
names are a guide to reading the groups, not a finding: the groups of other
judges and years need not resemble the article's, and the table of profiles
shows how far each group is from its style.

Contents:
    PROTOTYPES: the profile of each style, in standard deviations from the
        mean of each score.
    STYLES: the names of the nine styles, in the order of the article.
    Typology: the styles of the judges.
    classify: sorts judges into styles by Ward's cluster analysis.

"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy import optimize
from scipy.cluster import hierarchy

STYLES: tuple[str, ...] = (
    'Trailblazing', 'Consensus Building', 'Stalwart', 'Regulating',
    'Steadfast', 'Collegial', 'Incrementalist', 'Minimalist',
    'Error Correcting')
# The profiles are read from the article's descriptions of the styles
# (Part III.B), in standard deviations from the mean: "high" is about one,
# "highest" or "lowest" about one and a half, and "slightly" a quarter.
PROTOTYPES: pd.DataFrame = pd.DataFrame(
    [[1.0, -0.5, -0.5, 1.0],
     [1.0, -0.5, -0.5, -1.5],
     [1.5, 1.5, 1.5, -0.5],
     [0.0, 0.5, 1.0, 0.5],
     [0.0, 0.5, 0.0, 1.5],
     [-0.5, -0.5, -0.5, -0.5],
     [-0.25, -0.25, 0.5, -0.5],
     [0.0, -1.5, 0.0, 0.5],
     [-0.25, 1.0, -0.25, 0.0]],
    index = pd.Index(STYLES, name = 'style'),
    columns = ['ideological', 'activism', 'partisanship', 'independence'])
_FEATURES: tuple[str, ...] = tuple(PROTOTYPES.columns)


@dataclasses.dataclass
class Typology:
    """The styles of the judges.

    Args:
        assignments: a table with a row for each judge who was classified,
            labeled as the table of scores was, with "cluster" (numbered in
            the order of Ward's tree, as the article ordered them) and
            "style".
        profiles: a table with a row for each cluster: its style, number of
            judges, mean of each score, the means in standard deviations
            from the mean of all judges ("{score}_z"), and "distance" (how
            far the standardized means are from the style's profile).
        differences: a square table of the clusters, with the number of
            scores in which the means of each pair differ by at least one
            standard deviation (the article's Figure 1). A typology passes
            the article's test if every pair differs in at least one.

    """

    assignments: pd.DataFrame
    profiles: pd.DataFrame
    differences: pd.DataFrame

    @property
    def distinct(self) -> bool:
        """Returns whether every pair of clusters differs in some score.

        Returns:
            Whether each cluster's means differ from every other's by at
                least one standard deviation in at least one score.

        """
        values = self.differences.to_numpy(dtype = 'float64').copy()
        np.fill_diagonal(values, np.inf)
        return bool((values >= 1).all())


def classify(
    scores: pd.DataFrame,
    clusters: int = 9,
    *,
    names: Sequence[str] | None = None,
    only_qualified: bool = True) -> Typology:
    """Sorts judges into styles by Ward's cluster analysis.

    Args:
        scores: the table of scores (see `score_judges`), with "ideology",
            "activism", "partisanship", and "independence" (and "qualified",
            if `only_qualified`).
        clusters: the number of clusters. Defaults to 9, as in the article.
        names: the names of the styles to match the clusters to. Defaults to
            `None`, in which case they are `STYLES` if `clusters` is 9, and
            else the clusters are named by their numbers.
        only_qualified: whether to classify only the judges who define the
            scales of the scores. Defaults to `True`.

    Raises:
        ValueError: if there are fewer judges to classify than clusters.

    Returns:
        The styles of the judges.

    """
    features = pd.DataFrame({
        'ideological': scores['ideology'].abs(),
        'activism': scores['activism'],
        'partisanship': scores['partisanship'],
        'independence': scores['independence']}, index = scores.index)
    keep = features.notna().all(axis = 1)
    if only_qualified and 'qualified' in scores.columns:
        keep &= scores['qualified'].astype(bool)
    features = features[keep]
    if len(features) < max(clusters, 2):
        message = (
            f'{len(features)} judges cannot be sorted into {clusters} '
            f'clusters')
        raise ValueError(message)
    tree = hierarchy.linkage(features.to_numpy(dtype = 'float64'), 'ward')
    found = hierarchy.fcluster(tree, t = clusters, criterion = 'maxclust')
    # The clusters are numbered in the order that their judges first appear
    # among the leaves of the tree.
    leaves = hierarchy.leaves_list(tree)
    order: dict[int, int] = {}
    for leaf in leaves:
        order.setdefault(int(found[leaf]), len(order) + 1)
    numbered = pd.Series(
        [order[int(c)] for c in found], index = features.index,
        name = 'cluster')
    means = features.groupby(numbered).mean()
    spread = features.std(ddof = 1).replace(0, np.nan)
    standardized = (means - features.mean()) / spread
    labels, distance = _name(
        standardized, list(names) if names is not None else (
            list(STYLES) if len(means) == len(STYLES) else None))
    profiles = pd.concat([
        pd.DataFrame({
            'style': labels, 'judges': numbered.value_counts().sort_index()}),
        means,
        standardized.add_suffix('_z'),
        pd.DataFrame({'distance': distance})], axis = 1)
    profiles.index.name = 'cluster'
    gaps = means.to_numpy()[:, None, :] - means.to_numpy()[None, :, :]
    counts = (np.abs(gaps) >= spread.to_numpy()).sum(axis = 2)
    differences = pd.DataFrame(counts, index = means.index, columns = means.index)
    assignments = pd.DataFrame({
        'cluster': numbered, 'style': numbered.map(labels)})
    return Typology(
        assignments = assignments, profiles = profiles,
        differences = differences)


def _name(
    standardized: pd.DataFrame,
    names: list[str] | None) -> tuple[pd.Series, pd.Series]:
    """Returns the style of each cluster and its distance from the style.

    Args:
        standardized: the clusters' mean scores, in standard deviations.
        names: the styles to match, which must have profiles in
            `PROTOTYPES` and be as many as the clusters, or `None`.

    Returns:
        The style of each cluster, and the distance between its means and
            the style's profile (missing if the clusters were not matched to
            styles).

    """
    if names is None or len(names) != len(standardized):
        labels = pd.Series(
            [f'Cluster {c}' for c in standardized.index],
            index = standardized.index)
        return labels, pd.Series(np.nan, index = standardized.index)
    profiles = PROTOTYPES.loc[names, list(_FEATURES)].to_numpy()
    means = standardized[list(_FEATURES)].fillna(0).to_numpy()
    costs = ((means[:, None, :] - profiles[None, :, :]) ** 2).sum(axis = 2)
    rows, columns = optimize.linear_sum_assignment(costs)
    labels = pd.Series(index = standardized.index, dtype = object)
    distance = pd.Series(index = standardized.index, dtype = 'float64')
    for row, column in zip(rows, columns, strict = True):
        labels.iloc[row] = names[column]
        distance.iloc[row] = float(np.sqrt(costs[row, column]))
    return labels, distance
