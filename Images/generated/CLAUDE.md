# Images/generated/ — Figure generate dalla pipeline Python

Questa directory contiene i PDF prodotti da `python/final_thesis_figure.py` (e pochi PNG da `python/final_umap.py` tramite `python/outputs/`). Le figure vengono incluse in `chapters/cap6_risultati.tex`.

## Sottodirectory per dataset

| Cartella | Campione | Script di origine | Dataset RAW |
|----------|----------|-------------------|-------------|
| `lambdaquarti_50deg/` | lamina λ/4 (3 lunghezze d'onda) | `final_thesis_figure.py` | `raw/lambdaquarti_50deg/` |
| `lambdamezzi_50deg/` | lamina λ/2 | `final_thesis_figure.py` | `raw/lambdamezzi_50deg/` |
| `strati_v2/` (o `strati_fit/`) | nastro adesivo multistrato | `final_thesis_figure.py` + `final_plot_strati.py` | `raw/strati_v2/` |
| `zucchero/` | soluzione di zucchero | `final_thesis_figure.py` | `raw/zucchero/` |
| `barraon_v2/` | cantilever caricato | `final_thesis_figure.py` | `raw/barraon_v2/` |
| `barraoff_v2/` | cantilever scarico | `final_thesis_figure.py` | `raw/barraoff_v2/` |
| `righello_v2/` | righello di plastica | `final_thesis_figure.py` | `raw/righello_v2/` |

## Convenzione di nomenclatura

`<channel>_<parametro>.pdf`

- `<channel>` ∈ {`R`, `G`, `B`}
- `<parametro>` ∈ {`S0`, `S1`, `S2`, `S3`, `DoLP`, `AoLP`, `delta`, `theta`, `mask`}

Esempio: `B_delta.pdf` = canale blu, retardance. Generato con la pipeline arctan2 ([0°, 360°)) dal 2026-04.

## Rigenerare

1. Impostare `TARGET_FOLDER` e `TARGET_CHANNEL_IDX` in `python/final_utils.py`.
2. Eseguire `python python/final_thesis_figure.py`.
3. I PDF finiscono in `Images/generated/<dataset>/`.

Per l'UMAP: `python python/final_umap.py` produce PNG in `python/outputs/` (non qui).

## Note

- I PDF più vecchi possono essere basati sulla vecchia pipeline `arccos`. Quando si rigenera un dataset, **rigenerare tutti e tre i canali insieme** per coerenza.
- I PDF NON sono tutti inclusi nella tesi — la selezione è dell'utente, vedi `TODO.md`.
- `Images/generated/barraon_v2/` (al 2026-04-20) contiene 9 PDF ancora untracked in git: committare dopo validazione visiva.
