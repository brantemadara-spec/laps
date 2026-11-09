# Model and document index

Paths are relative to the project root. Existing download ZIPs are intentionally retained inside this full handoff.

## Current card press — LAPS Marle Rev C

- Editable print Blender scene: `dist/laps-siets/files/LAPS_Marle_Prototips.blend`.
- Self-contained Blender generator: `dist/laps-siets/files/LAPS_Marle_Blender.py` (also `assets/marle_source/blender/`).
- Render/assembly Blender scene: `dist/laps-siets/files/LAPS_Marle_Vizualizacija.blend`.
- Directly accessible STL and STEP, including the assembled STEP: `assets/marle_source/cad/` — 8 unique STL and 9 STEP.
- Web GLB: `dist/laps-siets/models/assembly.glb`, `grid.glb`, `shims.glb`.
- iPhone USDZ: `dist/laps-siets/files/assembly.usdz`, `grid.usdz`, `shims.usdz`.
- Original full prototype ZIP and print-only ZIP: `dist/laps-siets/files/`.
- Technical PDF, procurement PDF/CSVs and instructions: `dist/laps-siets/files/`.
- Editable drawing SVGs and dimensional JSON: `assets/marle_source/docs/` and `assets/marle_source/data/`.
- Original PNG renders plus web previews: `dist/laps-siets/images/`.

## Current pot mold — V4.1

- Blender scene and source: `dist/podins/files/NO_KOKA_UZ_KOKU_Podina_prototips.blend` and `.py`.
- Generator input used by page builder: `content/podins/NO_KOKA_UZ_KOKU_Podina_prototips.py`.
- Two revised STL halves: `dist/podins/files/01_MOLD_LEFT.stl` and `02_MOLD_RIGHT.stl`.
- Nine-part web catalogue: `dist/podins/models/podins.glb`.
- Current reports: `dist/podins/files/V41_Geometrijas_parbaude_LV.txt` and `V41_Parbaudes_dati.json`; source JSON under `content/podins/`.
- V41 comparison PNG and both earlier assembly posters: `dist/podins/images/`.
- Combined Blender/source/report/two-STL ZIP: `dist/podins/files/NO_KOKA_UZ_KOKU_Podina_prototips.zip`.
- The remaining seven objects are retained in BLEND/GLB/Python. They are not supplied as separately validated STL files. No pot STEP or pot USDZ was present in the saved source.

## Historical card press — Rev A

- Full original project ZIP: `dist/files/LAPS_Pulp_Press_Complete.zip`.
  Inside: CAD/STL/STEP, SVG/DXF drawings, Blender/Python, AR GLB/USDZ, source calculations, documentation and renders.
- Other Blender/download archives and PDFs: `dist/files/`.
- Web models: `dist/models/forma.glb`, `drenazas_plaksne.glb`, `starplikas.glb`.
- AR: `dist/files/Pulp_Press_assembled.usdz` and `Pulp_Press_exploded.usdz`.
- Original project PDF: `dist/files/Laps.pdf`.
- All document page images/catalogue: `dist/documents/`.
- Historical page: `dist/arhivs/index.html`.

Rev A files may show steel plates and older hardware/mesh; the current card form is Rev C. Pot V4 report files are also retained for history; use V41 reports for the current revision.
