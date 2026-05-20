# Images/generated/ — Figure generate dalla pipeline Python

Questa directory contiene i PDF prodotti da `python/final_thesis_figure.py` (mappe polarimetriche), `python/final_delta_histogram.py` (istogrammi δ), `python/final_slice_figure.py` (slice δ multistrato) e `python/final_umap.py` (mappe + scatter + istogrammi UMAP nelle sottocartelle `aolp_umap/` e `delta_umap/`). Le figure vengono incluse in `chapters/cap6_risultati.tex`.

## Sottodirectory per dataset

| Cartella | Campione | Script di origine | Dataset RAW |
|----------|----------|-------------------|-------------|
| `lambdaquarti_50deg/` | lamina λ/4 (3 lunghezze d'onda) | `final_thesis_figure.py` | `raw/lambdaquarti_50deg/` |
| `lambdamezzi_50deg/` | lamina λ/2 | `final_thesis_figure.py` | `raw/lambdamezzi_50deg/` |
| `strati_v2/` (o `strati_fit/`) | nastro adesivo multistrato | `final_thesis_figure.py` + `final_fit_plot_strati.py` | `raw/strati_v2/` |
| `zucchero/` | soluzione di zucchero | `final_thesis_figure.py` | `raw/zucchero/` |
| `barraon_v2/` | cantilever caricato | `final_thesis_figure.py` | `raw/barraon_v2/` |
| `barraoff_v2/` | cantilever scarico | `final_thesis_figure.py` | `raw/barraoff_v2/` |
| `righello_v2/` | righello di plastica | `final_thesis_figure.py` | `raw/righello_v2/` |

## Convenzione di nomenclatura

PDF principali in `<dataset>/`:
`<channel>_<parametro>.pdf`

- `<channel>` ∈ {`R`, `G`, `B`}
- `<parametro>` ∈ {`S0`, `S1`, `S2`, `S3`, `DoLP`, `AoLP`, `delta`, `theta`, `mask`, `hist_delta`, `slice`}

Esempio: `B_delta.pdf` = canale blu, retardance. Generato con la pipeline arctan2 ([0°, 360°)) dal 2026-04.

Sottocartelle UMAP in `<dataset>/{aolp_umap,delta_umap}/<CH>/`:
- `aolp_map.pdf` / `delta_map.pdf` — mappa 2D del parametro
- `umap_scatter.pdf` — embedding 2D colorato per AoLP/δ
- `aolp_hist.pdf` / `delta_hist.pdf` — istogramma del parametro

HTML interattivi plotly in `<dataset>/interactive/`:
- `*_slice.html`, `*_hist_delta.html` — tracked (leggeri)
- `*_<parametro>.html` heatmap — gitignored (50-160 MB ciascuno a DS=1)

## Rigenerare

1. Impostare `TARGET_FOLDER` e `TARGET_CHANNEL_IDX` in `python/final_utils.py`.
2. Eseguire `python python/final_thesis_figure.py` (singolo dataset/canale) oppure `python python/final_thesis_figure_all.py` (batch 7×3×9).
3. I PDF finiscono in `Images/generated/<dataset>/`.

UMAP: `python python/final_umap.py batch <dataset> --color-by both` produce 6 PDF per canale (3 aolp + 3 delta) direttamente in `Images/generated/<dataset>/{aolp_umap,delta_umap}/<CH>/`.

## Note

- I PDF più vecchi possono essere basati sulla vecchia pipeline `arccos`. Quando si rigenera un dataset, **rigenerare tutti e tre i canali insieme** per coerenza.
- I PDF NON sono tutti inclusi nella tesi — la selezione è dell'utente, vedi `TODO.md`.
