# Deep Review & Advancement of the Polarimetro Smartphone Thesis

You are taking over an active BSc thesis project (Ingegneria Fisica, Politecnico di Milano) on low-cost 2D imaging polarimetry using a smartphone CMOS sensor. Author: Filippo Narici. Relatore: Prof. Maurizio Zani. Your job is to push the thesis to a **near-final draft** and clean up the Python pipeline, while respecting a strict **human-in-the-loop boundary**: high-level visual interpretation of polarimetric maps belongs to the user, not to you.

## Before anything else — read these files

1. `CLAUDE.md` (root) — persona, style rules, navigation index.
2. `CLAUDE_bib_section.md` — citation workflow (mandatory before touching `.bib`).
3. `TODO.md` — current status.
4. `python/CLAUDE.md`, `chapters/CLAUDE.md`, `Images/generated/CLAUDE.md` — directory guides.

Do not begin work until you have read these. They contain non-negotiable constraints.

## Non-negotiable rules

1. **Persona & style** — Italian formal impersonale, physicist voice. NO AI clichés (`È importante notare che`, `Tuffiamoci`, `Un approccio innovativo`, em-dashes used as rhetorical pauses). NO bullet lists to explain concepts (prose only). See `CLAUDE.md` for the full anti-IA list.
2. **Citations** — Never fabricate. Use `tools/search_refs.py`, verify DOIs, follow `CLAUDE_bib_section.md`. Show the user candidate DOIs before adding to `Thesis_bibliography.bib`.
3. **Commits** — Italian, `[area]: descrizione breve` format. One logical change per commit. Push freely to `main` once tested locally.
4. **Human-in-the-loop boundary (critical)** — your perception of polarimetric maps is unreliable. You must:
   - NEVER pick which figures to embed in the thesis. Always ask the user.
   - NEVER interpret what a map shows physically (retardance structure, fast-axis patterns, anisotropy features). Always ask the user for the experimental insight first, then write the prose around it.
   - NEVER claim a result "validates" or "confirms" theory without explicit user sign-off.
   - You MAY: run the pipeline, regenerate outputs, propose candidate figures with reasoning, refactor code, edit text structurally, expand the bibliography, build infrastructure, and write prose around user-provided insights.
5. **Use `AskUserQuestion` liberally** — every ambiguity becomes a question. It is cheaper than redoing work.
6. **Compression modes (caveman etc.) never touch the thesis** — any active output-compression mode applies only to chat replies and code comments. `.tex` content, figure captions, abstract, and any text written into the thesis must always be full Italian formal prose per `CLAUDE.md`.

## Agent model selection

To save tokens without losing quality, override the model per agent:
- Phase 1 Explore agents (Python Auditor, Thesis Reviewer) — `model: sonnet`.
- Phase 1 Bibliographer — `model: sonnet`.
- Phase 2 Plan agent — leave default (Opus).
- Main Claude (orchestration, Italian prose, physics review) — leave default (Opus).

Pass `model` in the `Agent` tool call. If omitted, the agent inherits from the parent.

## Your three-phase approach

### Phase 1 — Reconnaissance (launch 3 Explore agents in parallel in ONE message)

#### Agent A — "Python Auditor" (Explore, very thorough)

Brief:

> Audit `python/` in depth. Report, with file:line references:
> - Physics-correctness concerns: Stokes pseudo-inverse conditioning; retardance wrapping/arctan2 branch; masking (`bg_mask_ref` vs `bg_mask_display`); dark-frame subtraction; saturation tracking; waveplate S3 extraction; reference-frame alignment via 2D polynomial surfaces.
> - Bugs, dead code, regressions. Confirm uncommitted work in `final_polarimeter.py`, `final_utils.py` and the untracked `final_umap.py`, `Images/generated/barraon_v2/`, `python/outputs/umap_*.png`.
> - Missing dependencies (e.g. `umap-learn` not in `requirements.txt`).
> - Magic numbers, hardcoded paths, duplicated logic.
> - Script↔thesis-figure dependency map.
> - Intentional-approximation flags (don't mark something a bug without checking if it is physics-justified).
> Report <1000 words, structured, concrete.

#### Agent B — "Thesis Reviewer" (Explore, very thorough)

Brief:

> Read every file under `chapters/` plus `Thesis.tex` (abstract, appendix, acknowledgements). Report per-chapter:
> - Physics-correctness concerns (equations, terminology, unit consistency).
> - Style violations vs. `CLAUDE.md`: AI clichés, bullet lists for concepts, English anglicisms, em-dashes, non-impersonal voice.
> - Claims that lack citations; citations that look plausible but unverified.
> - Internal inconsistencies — especially cap5 describing the current pipeline vs. cap6 tables/expected values that still reflect the old `arccos` method.
> - Placeholder boxes, missing captions, missing cross-references.
> - `CLAUDE.md` gaps: Appendix A code listings, acknowledgements placeholder.
> - Per finding, classify as: fixable mechanically vs. needs user input.
> Report <1000 words.

#### Agent C — "Bibliographer" (general-purpose with WebSearch)

Brief:

> Current `Thesis_bibliography.bib` has ~6 entries — mostly textbooks (Hecht, Born-Wolf, Goldstein, Collett, PoliMi lab manual, Solomatov & Akkaynak 2023). The thesis covers imaging polarimetry on smartphone CMOS, Stokes/Mueller formalism, Bayer demosaicing, optical activity (sucrose), photoelasticity, and UMAP. Using the workflow in `CLAUDE_bib_section.md` (`tools/search_refs.py`, DOI verification, no hallucinations), propose 10–15 additional entries covering:
> - Smartphone / low-cost imaging polarimetry (≥3)
> - CMOS division-of-focal-plane polarimetry (≥2)
> - Mueller-matrix imaging applications, including biomedical or material-science cases (≥2)
> - Bayer demosaicing (≥1)
> - Photoelasticity (beyond Goldstein, ≥1 review article)
> - Sucrose optical rotation / Drude dispersion (≥1)
> - UMAP (McInnes, Healy, Melville 2018)
> For each: title, authors, year, venue, DOI, one-line justification with the sentence/section it would cite.
> Do NOT write to `.bib` — propose only. User reviews and approves.
> Report <800 words.

After Phase 1: aggregate the three reports. Show a concise summary to the user. Ask the top three highest-priority questions (figure selection, retardance-table updates, UMAP positioning).

### Phase 2 — Plan (1 Plan agent)

Brief the Plan agent with: the three Phase-1 reports, `CLAUDE.md`, `TODO.md`, and the four user decisions (RAW=full, commit+push free, UMAP=formal subsection, scope=near-final draft with human interpretation). Request a dependency-ordered step-by-step execution plan. Review the returned plan yourself before executing.

### Phase 3 — Execute (human-in-the-loop)

Work the plan. Suggested order (adapt based on Phase-2 output):

1. **Commit pending saturation work** — granular Italian commits for `final_polarimeter.py` and `final_utils.py` uncommitted changes.
2. **Add `umap-learn` to `requirements.txt`; commit `final_umap.py`** and the new `Images/generated/barraon_v2/` figures.
3. **Re-run pipeline** on every dataset (strati_v2, lambdaquarti_50deg, lambdamezzi_50deg, zucchero, barraon_v2, barraoff_v2, righello_v2) across all three channels — regenerate the full PDF set in `Images/generated/`.
4. **Show the user the regenerated outputs**; ask which datasets and which parameters (S0/S1/S2/S3/DoLP/AoLP/δ/θ) are thesis-worthy per chapter.
5. **Re-run `final_plot_strati.py`** with the arctan2-based pipeline; report the new retardance values to the user for table updates.
6. **Remeasure retardance** for the user-selected quartz-plate figures and hand the user a compact table to confirm and interpret.
7. **Embed user-selected figures in cap6** — replace placeholder boxes with `\includegraphics`. Write draft captions (sample, channel, parameter, physical meaning). Ask the user to approve each caption before committing.
8. **Ask the user for 1–2 sentences of experimental insight per embedded figure / per dataset.** Integrate as discursive prose — do not invent physical readings.
9. **Write the UMAP subsection** in cap6 using the user's interpretation plus the correlation numbers from `final_umap.py`. Include both `umap_lambdaquarti.png` and `umap_strati.png` if the user approves.
10. **Complete Appendix A** — Python code listings via `lstlisting`. Don't dump all ~1800 lines. Ask the user which scripts go in full vs. excerpt; default: `final_utils.py` excerpts (Stokes, retardance, masking), `final_polarimeter.py` in full, `final_umap.py` in full, others as one-line summaries.
11. **Expand the bibliography** with the user-approved Phase-1-Agent-C entries via the `CLAUDE_bib_section.md` workflow.
12. **Resolve cap5 script-version ambiguity** — make cap5 prose match the current pipeline (arctan2 wrapping to [0°, 360°), saturation masking, 2D polynomial surface alignment, dark-frame subtraction, waveplate axes swap flag for lambdamezzi).
13. **Style pass on every chapter** — strip em-dashes used as rhetorical pauses, AI clichés from the CLAUDE.md blacklist, any bullet lists that explain concepts, English anglicisms.
14. **Leave acknowledgements placeholder** — user writes these.
15. **Light Python quality improvements** (only if time allows after the thesis is in draft):
    - Central `python/config.py` (or TOML) for magic numbers; keep module `final_utils.py` importing from it.
    - Module docstrings on every script.
    - Optional minimal pytest with ~5 sanity checks on Stokes math (identity state → [1,1,0,0]; linear horizontal → DoLP=1, AoLP=0°; etc.).
16. **Keep infrastructure current** — update `TODO.md` as tasks complete; update `python/CLAUDE.md`, `chapters/CLAUDE.md`, `Images/generated/CLAUDE.md` whenever structure changes (new script, new chapter section, regenerated figures).
17. **Final compile pass** — `pdflatex`/`bibtex` clean; figure inclusion verified; `TODO.md` reflects truth.
18. **Commit & push** the final state to `main`.

## Claude-friendly infrastructure you inherit (do not duplicate, do update)

- `CLAUDE.md` (root) — persona, style, navigation index, gotchas, human-interpretation boundary, self-maintenance rules.
- `TODO.md` (root) — living status board. Update as you go. Single source of truth for "where are we".
- `python/CLAUDE.md` — script map and gotchas.
- `chapters/CLAUDE.md` — chapter status, per-chapter TODOs.
- `Images/generated/CLAUDE.md` — figure naming convention, per-dataset contents, regeneration pointer.
- Maintenance rules (in root `CLAUDE.md`): status info lives in `TODO.md`, not `CLAUDE.md`; structural changes → update the relevant nested `CLAUDE.md`; do not add new nav files unless strictly necessary.

## Success criteria (check these at the end)

- [ ] All previously-pending Python work committed and pushed.
- [ ] Pipeline rerun; outputs verified; saturation masking active in every dataset's output.
- [ ] User-selected figures embedded in cap6 with user-approved captions.
- [ ] Retardance tables updated with new arctan2 pipeline values (user-approved).
- [ ] UMAP subsection in cap6 written with user's interpretation.
- [ ] Appendix A complete with user-approved scripts/excerpts.
- [ ] Bibliography expanded with user-approved entries.
- [ ] Cap5 pipeline description matches current code.
- [ ] Style pass done on every chapter.
- [ ] `TODO.md` and nested `CLAUDE.md` files up to date.
- [ ] `pdflatex` + `bibtex` compile clean.
- [ ] `main` pushed.

## What stays with the user (handoffs)

- Acknowledgements text.
- Experimental / map-visual interpretation per dataset.
- Figure-selection calls.
- Any physics claim you cannot verify from existing text alone.
- Final defense-specific content.

## When to stop and ask (always use AskUserQuestion)

- Any map interpretation.
- Any figure selection.
- Any new citation — show DOI first.
- Any physics claim you cannot verify.
- Any scope creep beyond one session — ask to prioritize.
- Any pipeline output that looks anomalous (NaN patches, wrap artefacts, masking holes).

Be rigorous, be terse, defer to the human on interpretation. Execute everything else.
