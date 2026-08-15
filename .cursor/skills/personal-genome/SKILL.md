---
name: personal-genome
description: Look up this project's 23andMe genotypes for health, pharmacogenomics, and personality/cognition markers. Use when the user asks about SNPs, rsIDs, genes, traits, drug response, disease risk, or their genome file.
---

# Personal genome lookup

23andAgent holds one local 23andMe raw file. Chat about **health, PGx, and traits** — not ancestry.

## Always do this

1. Read `AGENTS.md` if not already in context.
2. Look up genotypes with the local CLI (never read the raw 600k-line file into chat):

```powershell
python scripts/lookup.py rsid rs429358 rs7412
python scripts/lookup.py panel personality
python scripts/lookup.py gene APOE
python scripts/lookup.py search caffeine
python scripts/lookup.py panels
python scripts/lookup.py stats
```

This workspace's default shell is **Windows PowerShell 5**:
- Do not chain with bash `&&`. Use separate tool calls or `;`.
- For HTTP, call `curl.exe` (PowerShell `curl` is `Invoke-WebRequest`).
- `annotate` talks to Ensembl/GWAS/MyVariant. If one host times out, keep going with the other APIs and skills; do not treat a timeout as a missing genotype.

3. If the catalog has no entry, still look up the rsID locally, then annotate:

```powershell
python scripts/lookup.py annotate rs123
```

VNTRs and indels (DRD4-7R, MAOA-uVNTR, 5-HTTLPR) are `not_on_chip`. Nearby SNPs are not substitutes.

4. For literature / ClinVar / GWAS / PharmGKB, use the installed skills and **send rsIDs only**:
   - `.agents/skills/database-lookup` — ClinVar, GWAS Catalog, dbSNP, gnomAD, ClinPGx, Ensembl
   - `.agents/skills/paper-lookup` — PubMed / OpenAlex papers
   - `.agents/skills/gget` — gene/variant helper (optional)

## Output rules

- Lead with the genotype and whether it is `called`, `nocall`, or `not_on_chip`.
- State **evidence level** from the catalog: `clinical` / `replicated_gwas` / `exploratory`.
- Compare plus-strand `genotype_sorted` vs `complement_sorted` before quoting SNPedia or a paper.
- Personality and most common health SNPs have **small effects**. Say so.
- Never diagnose, never recommend starting/stopping a drug. Flag PGx hits as educational and suggest a clinician + confirmatory test for anything actionable (DPYD, Factor V, HFE C282Y homozygote, APOE, TPMT, etc.).
- Never paste more than a handful of genotypes. Never upload or attach the raw file to any API.

## Panels

`personality`, `pharmacogenomics`, `cardiovascular`, `thrombosis`, `neurology`, `iron`, `methylation`, `nutrition`, `metabolic`, `athletic`, `eye`, `immune`, `sensory`, `sleep`, `substance`, `hematology`
