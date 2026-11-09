# LAPS developer handoff

Export date: 2026-11-09. Public Site: https://laps.dashulyaashsxb.chatgpt.site
Saved Site version: 8. Source commit: `028185700c22cf091a5f689942a47965b97c4a25`.
This package contains all 138 files tracked in that source snapshot. The complete `dist/` tree is byte-for-byte preserved.
Two source-only portability/documentation adaptations are recorded in `handoff/PROVENANCE.json`; their originals are retained under `handoff/`.
The live Site was not changed by this export.

## Architecture and routes

This is a static HTML/CSS/JavaScript site, not a React/Next project. Three.js 0.180 and esbuild 0.25.10 are pinned by package-lock.json. There is no application server, database, required runtime secret, or external model CDN.

| Route | Content | Entry sources |
| --- | --- | --- |
| `/` | Current card press, Marle Rev C | `src/marle.html`, `src/marle-viewer.js` |
| `/laps-siets/` | Preserved alias with the same current card page | Same sources; assets under `dist/laps-siets/` |
| `/podins/` | Pot mold V4.1, nine-part catalogue, Python code, checks, posters, gauze/experiment advice | `src/podins.html`, `src/pot-viewer.js`, `src/pot_ears_update.html`, `src/pot_posters_and_advice.html` |
| `/arhivs/` | Historical Rev A card press | `src/archive.html`, `src/viewer.js`; retained `dist/arhivs/index.html` |

The Marle viewer supports model selection, part selection, exploded/assembled states and a procedural assembly animation. This animation is implemented in JavaScript; it is not a promised baked animation in every model file.
The pot viewer is a parts catalogue. Its laid-out GLB/BLEND object positions are not an assembled mold.

## Local preview and dependency setup

Serve the already-built site without any dependency installation:

```sh
python -m http.server 8000 --directory dist
```

Use http://localhost:8000/ and Ctrl+C to stop. File URLs will break fetch/model loading. Absolute URL paths assume hosting at the domain root. For a subpath host, rewrite the root-relative paths and test all routes.

For JavaScript changes, use Node 20+:

```sh
npm ci
npm run build
```

`npm run build` bundles the three viewers into `dist/assets/app.js`, `dist/laps-siets/marle.js` and `dist/podins/podins.js`. It does not regenerate HTML.
CSS is edited directly in `dist/assets/style.css`, `dist/laps-siets/siets.css` and `dist/podins/podins.css`.

For generated HTML/content, use Python 3.10+, ideally in a virtual environment, and install `requirements-content.txt`. Then run in this order:

```sh
python -m pip install -r requirements-content.txt
npm run content
npm run content:podins
npm run build
```

`prepare_marle.py` originally depended on `/workspace/laps_marle`, which was outside the saved source. This handoff reconstructs its 55 required source inputs from the published files/prototype ZIP into `assets/marle_source/` and changes only its SOURCE assignment to that relative directory. The published outputs remain untouched until you explicitly regenerate them. PDF/render source authoring programs missing from the saved Site were not recreated or invented; editable STEP, SVG and Blender/Python inputs are included where available.

`prepare_podins.py` is already relative to the project root. It reads `content/podins/`, inserts the code/review HTML, writes the reports and creates the downloadable prototype ZIP from files already under `dist/podins/files/`. When updating pot geometry, replace both `content/podins/NO_KOKA_UZ_KOKU_Podina_prototips.py` and the corresponding downloaded PY; update the BLEND, the two STL files and `dist/podins/models/podins.glb`, rerun geometry checks, and update the JSON review inputs before regenerating the page. Exporting STL alone does not validate fit or strength. Version the viewer/model cache-busting query when replacing the GLB.
The archived Rev A HTML is retained as built output; changing its template requires explicitly updating `dist/arhivs/index.html` as well.

## CAD and model editing

See `MODEL_INDEX.md` for exact paths. Keep print geometry, scene catalogues and web/AR models distinct.
Marle STL/STEP are in millimetres. GLB/USDZ use real metre scale. The pot source uses millimetre-valued coordinates; follow its bundled README for STL export. The 150 mm base should measure 0.15 m in GLB.
The current Marle Python generator is self-contained for Blender 4.x/5.x; inspect its OUTPUT_DIR before running. The pot script clears active scene objects: save work and run in a new scene. Previous exports were checked with Blender 4.3.2; geometry was not rerun in Blender as part of this file-transfer task.

The pot has nine named printable-design objects:
`01_MOLD_LEFT`, `02_MOLD_RIGHT`, `03_OVERFLOW_COLLAR`, `04_CORE_3MM`, `05_CORE_4MM`, `06_CORE_5MM`, `07_BASE`, `08_SIEVE`, `09_TOP_PLATE`.
Choose one of the three cores in an assembly. Metal M6/M12 fasteners are purchased hardware, not printed threads. Only the two revised mold-half STL files are provided separately; do not infer that nine validated STL files exist.

## Known next engineering work

The V4.1 revision fixed the two side lugs with 45-degree lower supports, teardrop M6 roofs retaining a 6.8 mm circular clearance, a common split plane and a cavity recut. The two mold-half native meshes/STLs passed their recorded closed-mesh checks. Side bolt axes are Z34/Z54 mm; side joints use four fully-threaded M6 x 40 bolts, four nuts and eight DIN125 OD12 washers. OD15-or-smaller thin-wall socket clearance was checked. Marle card washers are DIN9021 OD18; do not confuse those separate hardware lists.

Remaining pot issues documented in `content/podins/engineering_review.json` and the current V41 downloadable report:

1. The original cavity taper spans 72 mm while the target pot/core height is 70 mm. Nominal outer targets are upper diameter 90 mm, lower diameter 65 mm, H70 mm, bottom 4 mm; actual datums still need correction.
2. The base seat interferes by approximately 0.035–0.069 mm. Base, gauze/support working plane, core bottom and STOP must share consistent datums. The reported 1.5 mm bottom / 67.5 mm height case is a conditional fully-seated calculation, not a verified assembly.
3. The unchanged overflow collar has 12 open native boundary edges and remaining STL defects; vertical M6 rods have zero nominal reserve against the collar. Fix mesh and positive clearances.
4. The M12 nut pocket on top of the top plate does not by itself retain the upward axial reaction. Design a captured metal load path and measure force.
5. Gauze needs a rigid, flat, draining backing. The pot CAD still includes the original perforated sieve; the proposed integrated gauze support is advice, not an implemented feature. Measure compressed wet fabric and recalibrate bottom/STOP.
6. Inspect unchanged horizontal alignment pins and all other overhangs in the slicer. The ear revision does not certify the whole mold as support-free.

There is no measured PETG force/torque rating, creep test or wet-pulp press validation. Preserve these limitations while developing the next revision. The two assembly posters illustrate older V4 rectangular lugs and are labelled as historical principles on the current page; the V41 close-up and active 3D model show the revised lugs.

For experiments, changing the core alone does not guarantee equal dry height, pressure or density. Keep recipe/water ratio/gauze/drying controlled, dose dry material against target volume and measure actual force, dry mass, dimensions and density. Existing project notes explain these distinctions.

## Publishing and ownership

The package can be hosted as a static `dist/` directory. Preserve content types for .glb and .usdz; existing static header hints are in `dist/_headers`.
`.openai/hosting.json` records the existing Site ID and `dist` directory. It contains no credentials. Updating the original public address requires the owner's hosting authorization; possession of this ZIP does not grant it. Preserve the same Site/URL when authorized to update it. A separate host can serve `dist/` independently.
No deployment credentials, browser cookies, Git internals, node_modules or session files are included. Project and package dependency licensing metadata are retained; the project is marked UNLICENSED rather than automatically relicensed for public reuse.

## Verification and provenance

`handoff/EXPORT_VALIDATION.json` records export checks; `handoff/FILE_MANIFEST.json` lists every packaged payload file with SHA-256 and size. Run `python handoff/verify_manifest.py` after extraction.
The original downloadable ZIP files, PDFs, CSVs and 3D binaries are retained. The archived Rev A may contain old steel/mesh/bolt assumptions that do not apply to current Marle Rev C. Original procurement dates/prices were not refreshed during export.
