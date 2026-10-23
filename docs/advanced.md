# Advanced User Guide

This guide gives the formulas of the four scores as `score_judges` computes
them, the differences between the methods of the articles, and the places
where the articles left a choice open and how this project made it.

## Notation

For a judge, `t` is a case type (criminal or civil) and `s` a standard of
review (deferential, nondeferential, or unclear). `share(t)` is the average
judge's share of votes in criminal or civil cases (the mean over judges of
each judge's share), which the articles called "the distribution of the
average judge." Every rate is a judge's mean in a cell, such as the judge's
rate of reversal in civil cases under deferential standards.

**Thin cells.** When a judge has fewer than `cell_minimum` votes (5 by
default) in a cell, the judge's rate in that cell for criminal and civil
cases together is used, and if that is thin too, the rate of all judges in
the cell. The articles "interpolated based upon expected and actual scores
with that judge's case mix"; this is one way to do that, and it never lets a
single vote set a rate.

## Ideology

    Panel Score = sum_t share(t) * (Agree(Rep, t) - Agree(Dem, t))

`Agree(P, t)` is the share of the judge's pairs with copanelists of party
`P` in which the two agreed (both joined the majority, or both dissented).

    District Score = sum_t share(t) * sum_s w(t, s) * (Affirm(Rep, t, s) - Affirm(Dem, t, s))

`Affirm(P, t, s)` is the judge's rate of affirming district judges of party
`P`. The weight of a standard is

    w(t, s) = W(t, s) * n(t, s) / sum_s' W(t, s') * n(t, s')
    W(t, s) = (1 / ReversalRate(t, s)) / sum_s' (1 / ReversalRate(t, s'))

where `n(t, s)` is the judge's number of votes reviewing district judges in
the cell and `ReversalRate(t, s)` the rate of all judges. In the 2010
article's example, the weights of criminal cases were 0.479 (deferential),
0.241 (nondeferential), and 0.280 (unclear), which is what inverse rates of
reversal give. The article's expression divided the weighted sum by the
total number of votes and then halved it "to keep the District Score on the
same relative scale"; normalizing the weights within each case type does
that exactly, for any mix of votes.

The raw score combines the two:

| Method | Raw Ideology Score |
| --- | --- |
| original (2010) | Panel Score + District Score |
| typology (2013) | (d_panel * Panel Score + d_district * District Score) / (d_panel + d_district), where `d` is the rate of disagreement at each level among all judges ("combined based upon the rate of disagreement at each level"). |

**Zero and scale.** The 2010 article put zero at the mean of the k-th and
(k+1)-th most liberal judges, where k is the number of Democratic
appointees, and scaled so that the judge farthest from zero is at -100 or
100. The 2013 article kept zero where it is (equal agreement with both
parties) and chose "the multiplier ... that would either move the highest
score to 100 or lowest score to [-]100."

## Activism

    Activism Differential = sum_t share(t) * (Reversal(deferential, t) - Reversal(nondeferential, t))

Judge Wood's example in the 2011 article (4 reversals in 53 deferential
votes and 13 in 49 de novo votes) is a test of this project. The article's
case-mix expression estimated a judge's criminal and civil rates from the
judge's totals and the average judge's distributions, because its data were
thin; this project computes the rates in each case type directly, with the
fallbacks above. Votes under an unclear standard do not count.

The 2011 article made no super-panel adjustment; the 2013 article did, and
so does `method = "typology"`.

## Partisanship

    Partisanship = sum_t share(t) * ((DefRev(other, t) - DefRev(own, t)) - (NonRev(other, t) - NonRev(own, t)))

`DefRev(other, t)` is the judge's rate of reversing district judges
appointed by the other party under deferential standards, and so on. This is
the 2012 article's raw formula (with Democratic and Republican district
judges) multiplied by the judge's own party (1 for a Republican appointee and
-1 for a Democratic one), which is the article's "one unique alteration": a
Democratic appointee who favors Republican district judges is not partisan.
Writing it with "own" and "other" party lets the traveling judges of a
circuit, who belong to both parties, be scored together.

## Independence

    Independence = sum_t share(t) * (Dissents(t) + Concurrences(t) - E[Dissents(t)] - E[Concurrences(t)])

`Dissents(t)` is the judge's dissents per vote plus, by default, the dissents
of copanelists against opinions that the judge wrote (`provoked =
"author"`, the 2012 article's "writes an opinion that draws a dissenting
opinion"). `provoked = "panel"` counts dissents against any majority that the
judge joined, which is how the 2013 article's footnote ("the difference
between dissenting and being dissented against is simply how the third judge
on the panel voted") can be read. A concurrence in part and dissent in part
is a dissent only.

The expected rates are the fitted values of a linear regression, across the
judges who define the scales, of each rate on the absolute distance between
the judge's ideology and the mean ideology of the judges of the judge's
circuit. The 2012 article used the scaled Ideology Score; the 2013 article
used "the degree to which a judge's Raw Ideology Score differed from the
mean of the circuit," which `method = "typology"` uses (the adjusted raw
score, before scaling).

The raw scores are shifted so that the lowest is `log_offset` (0.01 by
default), and their logarithm is scaled from 0 to 100. The articles placed
the scores "on a logarithmic scale (to create a normal distribution)" without
saying how they made them positive; the offset is that choice, and a smaller
one spreads out the lowest scores.

## Adjustments

**Super-panel effects.** Each vote has an alignment: the parties of the two
copanelists and of the district judge (RR-R, RR-D, DR-R, DR-D, DD-R, DD-D).
For each alignment, case type, and standard, the rates of agreement and
reversal of all judges are what a blank-slate judge would do there. The
score is computed again with those rates in place of the judge's own, and
that "expected" score is subtracted. So alignments that offset each other
(thirty RR-R panels against ten DD-D panels, in the articles' example)
cancel, and only the excess pulls the score, as the articles described.

**Circuit.** For each circuit, the votes there of judges who sat in more than
one circuit are scored together as one hypothetical judge ("actual"), and
compared with those judges' overall scores weighted by their votes there
("expected"). The differential, actual less expected, is subtracted:

| `circuit` | Amount subtracted from a judge's score | Used by |
| --- | --- | --- |
| `per_judge` | The differential of the judge's home circuit / (2 * the judges of the circuit) | 2010 (ideology) and 2011 (activism) |
| `per_vote` | The sum over circuits of the differential / the traveling votes there * the judge's votes there | 2012 (partisanship) and 2013 (all three) |
| `full` | The sum over circuits of the differential * the judge's share of votes there | Not in the articles |
| `none` | Nothing | Independence, in both |

The `per_vote` formula follows the 2012 and 2013 appendices literally ("the
raw adjustment number was then divided by the number of traveling votes in
the circuit ... Then each judge within the circuit would have the circuit
adjustment applied based upon the number of votes he or she issued"). When a
circuit has few traveling votes and its judges many votes, it can be larger
than the differential itself; the `{score}_circuit` column shows its size,
and `circuit = "full"` is the alternative that never is.

**Scale.** The judges with at least `minimum` interactions (200 in the
articles) define every scale. Activism, partisanship, and independence are
shifted so that the lowest of them is 0 and multiplied so that the highest
is 100; other judges can fall outside 0 to 100.

## Methods at a glance

| Choice | `method = "original"` | `method = "typology"` |
| --- | --- | --- |
| Raw Ideology Score | Panel + District | Weighted by the rates of disagreement |
| Ideology's zero | The k-th judge (k = Democratic appointees) | Equal agreement with both parties |
| Super-panel adjustment | Ideology, partisanship | Ideology, activism, partisanship |
| Circuit adjustment | Per judge (ideology, activism), per vote (partisanship) | Per vote |
| Independence's expected rates | Scaled Ideology Score | Adjusted raw Ideology Score |

## Scoring periods

The articles scored one year. `by = "year"` (or any column) scores each value
separately, with its own context (shares, weights, alignments, travelers, and
scale), so the scores of different years are each relative to their own
judges. A judge needs `minimum` interactions within a period to define its
scales, so with one year at a time a lower `minimum` may be needed in small
circuits.

## Judging styles

`classify` uses scipy's Ward linkage on the four scores (the absolute
Ideology Score, which is from 0 to 100, and the other three), cuts the tree
into `clusters` groups, and numbers them in the order of the tree's leaves.
With nine clusters, each is matched to one of the article's styles by the
smallest total squared distance between the clusters' standardized means
and the styles' profiles (read from the article's descriptions in Part
III.B: "high" is about one standard deviation, "highest" or "lowest" about
one and a half). The "distance" column of the "typology" table says how
well each cluster fits its style.
