# OASB-2 crosswalks

These crosswalks are an analyst reading of where OASB-2 controls and two target frameworks address related outcomes: NIST AI RMF 1.0 subcategories in one file, and articles and annexes of Regulation (EU) 2024/1689, the EU AI Act, in the other. A row records that an analyst read an overlap in subject matter between one OASB-2 control and one subcategory, article, or annex; it does not state that either text requires, replaces, or stands in for the other. These crosswalks are informative, not normative. They are not a conformity assessment, a certification, a statement of compliance, or legal advice, and a row does not mean that implementing the control satisfies the target. No row makes a determination about whether Regulation (EU) 2024/1689 applies to a given system or in which risk category. NIST AI RMF 1.0 is a voluntary framework.

## Scope

These crosswalks read OASB-2 (agent-governance-spec, domains 11-19, 72 controls). They do not read OASB-1 (oasb.ai, domains 1-10, 46 controls). They are not part of the OASB-2 specification and change nothing in it: no control, requirement, scoring rule, or conformance level is added, removed, or interpreted by these files. Every subcategory in the committed NIST list (the GOVERN, MAP, MEASURE, and MANAGE functions) and every article and annex in the committed EU list was read as a candidate target; a row was written only where the analyst read an overlap, and each control without a row appears under the heading "Controls with no mapping asserted" in its crosswalk.

Reading as of 2026-09-01: OASB-2 at commit ec85d16ae5c9c50ef89ed525d5bae928a6ddcfd5 of agent-governance-spec; NIST AI RMF 1.0 (NIST AI 100-1, January 2023, DOI 10.6028/NIST.AI.100-1); Regulation (EU) 2024/1689 (OJ L, 12.7.2024; consolidated text CELEX 02024R1689-20260727, as amended by Regulation (EU) 2026/1744). The rows read the original OJ article and annex numbering recorded in the committed source lists.

## Basis definitions

- `partially-addresses`: what the control requires forms part of what the target describes; the control does not do everything the target describes.
- `evidence-for`: the artifact the control requires (a governance file section, record, or log) is the kind of documentation the target asks an organization to be able to produce.
- `related`: topical overlap only, without either relationship above; not to be cited as evidence.

## Files

- [OASB-2 to NIST AI RMF 1.0 crosswalk](oasb-2-to-nist-ai-rmf-1.0.md), rendered from the [NIST crosswalk CSV](oasb-2-to-nist-ai-rmf-1.0.csv) (canonical).
- [OASB-2 to the EU AI Act crosswalk](oasb-2-to-eu-ai-act-2024-1689.md), rendered from the [EU crosswalk CSV](oasb-2-to-eu-ai-act-2024-1689.csv) (canonical).
- [Source provenance](sources.md), with the committed identifier lists for [NIST AI RMF 1.0 subcategories](sources/nist-ai-rmf-1.0-subcategories.csv) and for [EU AI Act articles and annexes](sources/eu-ai-act-2024-1689-articles.csv).
- [Validator and renderer](../scripts/check_crosswalks.py), run as `python3 scripts/check_crosswalks.py` from the repository root.

## Export contract

The two crosswalk CSV files are the machine readable export of these crosswalks; the .md files are renders of them and carry nothing the CSV does not.

- Header, exactly: `control_id,control_title,target_id,target_title,basis,note`.
- `control_id` is a `SOUL-XX-NNN` id that resolves to a `### SOUL-XX-NNN:` heading under the [domains directory](../domains/), and `control_title` is that heading's title verbatim.
- `target_id` and `target_title` are one row of the committed source list for that crosswalk, verbatim.
- `basis` is one of `partially-addresses`, `evidence-for`, `related`, defined above.
- `note` is one sentence of at most 200 characters ending in a single full stop, free of the vocabulary the validator lists as banned.
- Encoding: UTF-8 without a byte order mark, LF line endings, RFC 4180 with minimal quoting, rows sorted by `control_id` then `target_id`, one row per (control, target) pair.
- Column names in these files are snake case; a JSON rendering of the same rows uses camelCase members (`controlId`, `controlTitle`, `targetId`, `targetTitle`, `basis`, `note`).

Deprecated control ids. A control id is never reused or renumbered (specification.md, section 8.2). When a control is deprecated, its heading stays in its domain file with status `deprecated` and a `replacedBy` id, so its rows here stay valid and are kept; rows for the successor control are added under the successor's id. The pairing is exported in a third canonical file, `deprecated-controls.csv`, with the header `control_id,control_title,replaced_by,deprecated_in`, where `deprecated_in` is the specification version that deprecated the control. That file does not exist while no control is deprecated, which is the case at the reading above; the commit that deprecates the first control creates it and adds its validation rule. The validator holds the number of control headings to a constant (72 at this reading) that counts every published id, active or deprecated, and that moves only in a commit that adds a control.

## Sources

| Source | Version | Links |
| --- | --- | --- |
| NIST AI RMF 1.0 | NIST AI 100-1, January 2023 | [DOI 10.6028/NIST.AI.100-1](https://doi.org/10.6028/NIST.AI.100-1); [NIST AI 100-1 PDF at nvlpubs](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf) |
| EU AI Act | Regulation (EU) 2024/1689, OJ L, 12.7.2024 | [ELI record](http://data.europa.eu/eli/reg/2024/1689/oj); [Official Journal PDF at EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689) |
| OASB-2 | commit ec85d16ae5c9c50ef89ed525d5bae928a6ddcfd5 | [domains directory](../domains/) |

Retrieval dates, checksums, and known text-layer readings are recorded in [sources.md](sources.md).

## How to verify a row

- Open the control in its file under the [domains directory](../domains/) at the commit named above and read the control description.
- Open the target provision in the linked primary document at the version named above and read it in full.
- Read the row's note; it names one overlap in subject matter that both texts contain, and nothing more.
- Check the cited identifier and title against the committed source list for that crosswalk; every cited identifier and title appears there verbatim.

## How to cite

Cite a row by permanent commit URL, in the form `https://github.com/opena2a-standards/agent-governance-spec/blob/COMMIT/crosswalks/FILE`, replacing `COMMIT` with the full hash of the commit being cited and `FILE` with the crosswalk file name.
