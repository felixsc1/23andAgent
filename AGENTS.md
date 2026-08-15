# 23andAgent

Local, educational discussion of **one person's** 23andMe raw genotypes. Focus: **health markers, pharmacogenomics, and personality/cognition traits**. Skip ancestry unless asked.

This is **not medical advice** and **not a diagnostic test**. 23andMe itself labels the file as research/educational only. Array data misses most rare variants, cannot phase haplotypes reliably, and has a non-trivial error rate for rare calls.

## Data

| Item | Path |
|------|------|
| Raw 23andMe TSV | `raw_genome/genome_*.txt` (gitignored) |
| Fast index | `data/genome.sqlite` (gitignored; build with `python scripts/lookup.py index`) |
| Curated markers | `data/panels/markers.json` |
| Lookup CLI | `python scripts/lookup.py` |

Format: `rsid`, `chromosome`, `position`, `genotype`. **Build GRCh37 / hg19**, **plus strand**. No-calls are `--`. Internal 23andMe IDs start with `i` (not in dbSNP).

Do **not** read the raw genome file into the conversation. Use the CLI. Do **not** upload the raw file anywhere. Public APIs may receive **rsIDs only**.

## How to answer questions

1. Map the question to rsIDs or a panel (`personality`, `pharmacogenomics`, `cardiovascular`, …). Run `python scripts/lookup.py panels` if unsure.
2. Fetch local genotypes:
   - `python scripts/lookup.py rsid rs429358 rs7412`
   - `python scripts/lookup.py panel personality`
   - `python scripts/lookup.py gene COMT`
   - `python scripts/lookup.py search caffeine`
3. Interpret using catalog `evidence` plus public sources. For anything not in the catalog, run `python scripts/lookup.py annotate <rsid>` and/or the `database-lookup` skill (ClinVar, GWAS Catalog, ClinPGx, dbSNP, gnomAD).
4. For papers, use the `paper-lookup` skill. Prefer GWAS Catalog and ClinVar over blog posts and SNPedia when they disagree.

### Strand

23andMe alleles are plus-strand. SNPedia and some papers use minus strand. The CLI returns `genotype_sorted` and `complement_sorted`. If a source says the risk allele is `T` and the plus-strand call is `A`, check whether they are complements before concluding mismatch.

### Evidence language

| Level | How to talk about it |
|-------|----------------------|
| `clinical` | Established Mendelian or CPIC/PGx marker. Still confirm before acting. |
| `replicated_gwas` | Real association, usually tiny effect. Not a diagnosis. |
| `exploratory` | Candidate-gene / consumer-report favorite. Lead with uncertainty. |

Personality genetics is **highly polygenic**. Single SNPs (COMT, BDNF, OXTR, 5-HTTLPR proxies, MAOA) do **not** determine personality. The famous MAOA-uVNTR, 5-HTTLPR indel, and DRD4 exon-3 7-repeat (wanderlust) VNTRs are **not** reliably on this chip; nearby SNPs are not substitutes.

## Windows / PowerShell

The default shell here is Windows PowerShell 5, not bash.

- Do **not** chain commands with `&&`. Use separate tool calls, or `;`.
- PowerShell's `curl` is `Invoke-WebRequest` and will reject `--data-urlencode`. Call **`curl.exe`**.
- `python scripts/lookup.py annotate` hits Ensembl, GWAS Catalog, and MyVariant. If one host times out, report that source as failed and continue with the others / the database-lookup and paper-lookup skills. A timeout is not a missing genotype.

APOE e2/e3/e4 needs **both** `rs429358` and `rs7412`. CYP2D6 metabolizer status **cannot** be called from one or two SNPs.

## Privacy

- Do not commit or push `raw_genome/` or `data/genome.sqlite`.
- Do not echo long genotype lists or the file header identifiers into git, issues, or remote tools.
- If a tool would transmit the raw file, refuse and use rsID lookup instead.

## Installed agent skills

| Skill | Role |
|-------|------|
| `.cursor/skills/personal-genome` | This project's lookup workflow |
| `.agents/skills/database-lookup` | ClinVar, GWAS, dbSNP, gnomAD, PharmGKB/ClinPGx, Ensembl |
| `.agents/skills/paper-lookup` | PubMed / OpenAlex / preprint lookup |
| `.agents/skills/gget` | Optional gene/variant CLI helpers |

Open resources worth citing: [GWAS Catalog](https://www.ebi.ac.uk/gwas/), [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/), [ClinPGx/PharmGKB](https://www.pharmgkb.org/), [CPIC](https://cpicpgx.org/), [SNPedia](https://www.snpedia.com/) (strand-check), [PGS Catalog](https://www.pgscatalog.org/), [OpenDNA](https://github.com/corbett3000/OpenDNA) (local panel reports), [ClawBio](https://github.com/ClawBio/ClawBio) (`pharmgx-reporter`, `gwas-lookup`; ancestry skills are out of scope).
