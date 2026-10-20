# Human and AI detector errors on GPT-5 conversations

Do people and automated detectors make the same mistakes when identifying
AI-generated chats? This repository contains the final descriptive analysis and
figure code for a comparison of human judgments with Pangram 4.1 on Jones and
Bergen's 15-minute GPT-5 Turing-test conversations.

This is an independent analysis prepared for a job application. It is not an
Epoch AI publication or a general benchmark of Pangram.

## Main results

- Pangram gave an AI verdict to all 62 GPT-5 texts from games people got wrong.
- It gave an AI verdict to 38 of 41 GPT-5 texts from games people got right.
- Overall, it flagged 100 of 103 GPT-5 texts; three human texts received AI
  verdicts and another five received Mixed verdicts.
- The paired authorship-share comparison correctly ordered 97 pairs and tied
  on six, without reversing any. Ties receive half credit in the plotted score.
- The paired score was 98.4% on human-fooled games and 95.1% on human-correct
  games: a difference of 3.27 percentage points, with a 90% interval of
  -0.04 to 7.32 points.

![Main figure](figures/main_figure.png)

The full write-up is in [INSIGHT.md](INSIGHT.md).

## Reproduce the results

Use Python 3.12 or later. The recorded environment was Python 3.12.14, NumPy
2.3.5 and Matplotlib 3.10.8.

    python -m pip install -r requirements.txt
    python analyse.py
    python plot.py

Both scripts resolve paths relative to this repository, so they also run from
another working directory. No API key, detector subscription or network access
is needed. These commands analyse the recorded observations; they do not
rescan the conversations with a newer detector.

## Files

| File | Purpose |
|---|---|
| analyse.py | Apply the length rule, compare paired scores and actual verdicts, calculate uncertainty, and write tables. |
| plot.py | Generate the two-panel figure in PNG, SVG and PDF, and export its plotted values. |
| data/games.csv | Curated numeric and categorical observations for all 148 available GPT-5 games; scores are blank for the 45 unscanned, excluded games. |
| data/README.md | Column definitions, preparation and scoring rules. |
| data/provenance.json | Source links, version/date information and source-file hashes. |
| results/ | Recomputed estimates, retained game outcomes, overlap and classification tables, and graph data. |
| figures/ | The graph in raster and vector formats. |
| INSIGHT.md | The accompanying insight draft. |
| LICENSE | MIT licence for the original Python code. |
| DATA_RIGHTS.md | What is included and the separate status of the source data and detector reports. |

## Analysis choices

The source export has 148 GPT-5 games, including 87 in which people selected
GPT-5 as human. The paper reports 150 and 89 respectively; this discrepancy
precedes this analysis and is not attributed to our exclusions. Requiring at
least 50 whitespace-separated words from each witness leaves 103 games,
62 human-fooled and 41 human-correct, comprising 206 texts and 24,969 words.

The original inputs combined each witness's messages chronologically,
preserving the supplied wording and omitting interrogator messages. All 206
downloaded reports were checked against those inputs after Unicode NFKC
normalization and removal of PDF layout whitespace. Reports identify Pangram
4.1 and are dated 19 October 2026.

For standalone classification, use the PDF's written assessment: AI, Human or
Mixed. A clean AI verdict counts as detecting a GPT-5 text. Mixed is kept
separate from an AI-only accusation against a human text. For strict
source-classification accuracy, Mixed counts as incorrect for either source.
This gives 195 of 206 strictly correct classifications.

For paired comparison, the PDF reports provide authorship shares, not continuous
human-likelihood probabilities. The human-written share is normalized to 1 for
reports containing only Human Written segments, 0 for reports with no Human
Written segments, and the displayed human-written fraction for genuinely mixed
reports. This avoids breaking ties using tiny 0.1% display artifacts on
otherwise wholly AI/human reports. No numeric probability is inferred from
High/Medium/Low confidence labels. A higher share for the actual human is
correct; an equal share is a tie; a lower share is reversed. Credit is 1, 0.5
or 0 respectively. This is an adaptation of the initial probability-ranking
proposal, not an exact reproduction of that measurement.

Games sharing a participant in either role are joined into connected groups.
The retained sample contains 151 people and 48 groups. The script resamples
those whole groups 10,000 times with seed 20261016. Intervals are the 5th and
95th percentiles; differences use the same draws for both groups.

An all-success group produces a degenerate empirical bootstrap interval. The
zero-miss bar therefore has no whisker: a 100-100% interval would not give a
useful population-risk bound. The AI-flag-rate difference is included in the
estimates CSV for transparency, but its bootstrap interval shares this boundary
limitation. It must not be read as conclusive evidence of a general inverse
relationship. The three observed GPT-5 misses are a small number of events.

These scripts contain the descriptive analyses reported in INSIGHT.md. They do
not include the earlier exploratory regressions, alternative scoring rules or
anonymization sensitivities. The study was not preregistered; the report-based
scoring adaptation was settled after inspecting a pilot batch.

## Sources and scope

- [Jones and Bergen paper](https://doi.org/10.1073/pnas.2524472123).
- [Original OSF project](https://osf.io/jk7bw/), using files under 15_mins/.
- [Related Epoch detector insight](https://epoch.ai/data-insights/ai-detectors-false-negatives).
- Pangram 4.1: 206 full reports downloaded from scans performed on 19 October 2026.

The detector saw completed witness-only text; people participated interactively
and saw their own questions. One model persona and detector version cannot
establish results for other systems. Public-source labels identify the human
witness, rather than independently verifying the authorship of every phrase.
Training exposure to these public conversations is unknown. These results do
not identify the cues used or predict the effect of giving people detector
advice.
