# Crosswalk source documents

Provenance for the target-framework identifier lists under `crosswalks/sources/`.
Every identifier and title in those CSV files was extracted by script from the
retrieved documents listed here, not transcribed by hand.

## NIST AI Risk Management Framework (AI RMF 1.0)

- Title: Artificial Intelligence Risk Management Framework (AI RMF 1.0)
- Publisher: National Institute of Standards and Technology, U.S. Department of Commerce
- Version and date: AI RMF 1.0, NIST AI 100-1, January 2023
- DOI: 10.6028/NIST.AI.100-1
- URL used: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf
- Retrieval date: 2026-09-01
- SHA-256: 7576edb531d9848825814ee88e28b1795d3a84b435b4b797d3670eafdc4a89f1
- Reuse: NIST publications are works of the U.S. government and are in the
  public domain in the United States.
- Derived file: `sources/nist-ai-rmf-1.0-subcategories.csv` (72 subcategories
  from Tables 1 to 4 of the framework core, Chapter 5).

## Regulation (EU) 2024/1689 (EU AI Act)

- Title: Regulation (EU) 2024/1689 of the European Parliament and of the
  Council of 13 June 2024 laying down harmonised rules on artificial
  intelligence (Artificial Intelligence Act)
- Publisher: Publications Office of the European Union, Official Journal of the
  European Union
- Version and date: Official Journal L series, 12.7.2024 (as published; not the
  consolidated version)
- Identifiers: Regulation (EU) 2024/1689; OJ L, 12.7.2024;
  ELI http://data.europa.eu/eli/reg/2024/1689/oj; CELEX 32024R1689
  (consolidated text CELEX 02024R1689-20260727)
- URL used: https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689
- Retrieval date: 2026-09-01
- SHA-256: bba630444b3278e881066774002a1d7824308934f49ccfa203e65be43692f55e
- Reuse: (c) European Union, 1998-2026. Reuse is permitted under the Commission
  reuse policy (Decision 2011/833/EU) provided the source is acknowledged.
- Amendment status: the consolidated text (CELEX 02024R1689-20260727) is
  amended by Regulation (EU) 2026/1744. The CSV here is extracted from the
  original OJ publication of 12.7.2024; article numbering (Articles 1 to 113)
  and annex numbering (Annexes I to XIII) are those of the original act.
- Derived file: `sources/eu-ai-act-2024-1689-articles.csv` (113 articles and
  13 annexes with their headings).
- Known text-layer readings kept verbatim: the Article 111 heading in the OJ
  PDF text layer ends "already placed on the marked"; a stray backtick after
  the Article 1 heading "Subject matter" was removed as an extraction artifact.
