# Analysis data

games.csv has one row per GPT-5 game in the available OSF export (148 rows).
It contains the new detector measurements together with the minimum derived
source metadata needed to reproduce this analysis. It does not contain chat
transcripts, participant explanations or full Pangram reports.

| Column | Meaning |
|---|---|
| game_id | Game identifier from the original export, retained for matching back to OSF. |
| interrogator_id | A consistently pseudonymized participant identifier. |
| human_witness_id | Identifier from the same pseudonym scheme, preserving repeats across roles. |
| human_correct | 1 if the person selected the actual human witness, otherwise 0. |
| gpt5_words | Whitespace-separated words in the concatenated GPT-5 witness messages. |
| human_words | Whitespace-separated words in the concatenated human witness messages. |
| gpt5_scan_id | Neutral scan label used in the Pangram submission. |
| gpt5_verdict | AI, Human or Mixed, from the report's written assessment. |
| gpt5_human_written_share | Normalized human-written fraction, between 0 and 1. |
| human_scan_id | Neutral scan label for the matched human witness. |
| human_verdict | AI, Human or Mixed, from the report's written assessment. |
| human_human_written_share | Normalized human-written fraction, between 0 and 1. |

The source participant identifiers were replaced consistently across all games
and both roles. Repeated-person structure is retained so the script can rebuild
the participant-connected groups without publishing the original identifiers.

Detector fields are empty for the 45 games failing the minimum of 50 words per
witness. Empty means unscanned, not a zero score or a failed detector call.

## Preparation of the curated values

Each witness's messages were concatenated chronologically with a consistent
separator. Questions from the interrogator were excluded. Source wording,
punctuation, spelling, slang, casing and typos were preserved, including any
anonymization already performed by the original authors.

The 206 submitted texts were shuffled under neutral Scan001-Scan206 labels.
Full reports were downloaded manually and linked back using the scan key.
Their analyzed texts matched the submitted inputs after Unicode NFKC
normalization and removal of PDF layout whitespace.

The written document assessment determines the categorical verdict. It is not
replaced with the broader chart heading or history-page label. In particular,
Scan201 has a Mixed written assessment despite an AI chart headline.

Human-written shares were normalized from the PDF's segment labels:

- All segments Human Written: share 1.
- No Human Written segments: share 0.
- Genuinely mixed segments: the displayed Human Written percentage divided by 100.

This prevents an incidental 0.1% display artifact on a wholly AI report from
breaking a tie. The shares are not probabilities that a document is human.

The two scripts reproduce the final statistics from these curated values.
They do not redownload OSF, extract PDFs or make detector calls. The original
transcripts and full reports were retained separately for the collection and
verification work. Provenance links and raw-source hashes are in provenance.json.
