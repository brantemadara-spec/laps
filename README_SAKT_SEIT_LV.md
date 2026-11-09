# LAPS — pilns projekts nodošanai izstrādātājam

Eksportēts 09.11.2026. no publicētās mājaslapas 8. versijas.
Mājaslapa: https://laps.dashulyaashsxb.chatgpt.site
Kartīšu forma: **LAPS Marle Rev C**. Podiņa forma: **V4.1**.

## Ātrā palaišana

Izpako visu ZIP vienā mapē. Termināli atver šajā mapē, kur atrodas šis README.
Nepietiek atvērt `dist/index.html` ar dubultklikšķi: 3D faili un dokumentu katalogi jāielādē caur HTTP serveri.

```sh
python -m http.server 8000 --directory dist
```

Ja datorā Python komanda ir `python3` vai `py`, lieto to `python` vietā.
Pārlūkā atver **http://localhost:8000/**. Serveri aptur ar Ctrl+C.
Visām saitēm vajadzīga `dist/` mape kā servera sakne.

## Kas ir iekšā

| Mape / fails | Saturs |
| --- | --- |
| `dist/` | Visa gatavā publicētā mājaslapa ar visiem attēliem, PDF, 3D un lejupielādēm; saglabāta nemainīta. |
| `src/` | Rediģējamie HTML šabloni un JavaScript: 3D apskate, salikšanas animācija, dokumentu lasītājs. |
| `assets/marle_source/` | Kartīšu formas ģeneratoram vajadzīgie CAD, Blender, rasējumu un datu avoti, atgūti no publicētajiem failiem. |
| `content/podins/` | Aktuālais podiņa Python kods un ģeometrijas pārbaudes. |
| `package.json`, `package-lock.json` | Precīzs JavaScript atkarību apraksts pārbūvēšanai. |
| `requirements-content.txt` | PDF un attēlu apstrādes Python atkarības. |
| `DEVELOPER_HANDOFF.md` | Detalizēta informācija nākamajam izstrādātājam angliski. |
| `MODEL_INDEX.md` | Kur atrodas katrs modeļu komplekts un kura versija ir aktuāla. |
| `handoff/` | Izcelsme, veiktās pārbaudes, sākotnējie pielāgoto avotu faili un kontrolsummas. |

Arhīvā ir Blender modeļi un kodi, GLB modeļi mājaslapai, pieejamie USDZ faili iPhone AR, STL/STEP, rasējumi, projekta PDF, iepirkumu saraksti un abi podiņa salikšanas plakāti.
Iepriekšējā Rev A ir saglabāta kā vēsturisks arhīvs. Tā nav aktuālā konstrukcija.

## Izmaiņas un pārbūve

Nepieciešams Node.js 20+ un Python 3.10+.
JavaScript rediģēšanai/pārbūvēšanai:

```sh
npm ci
npm run build
```

HTML satura pārbūvēšanai papildus uzstādi Python atkarības, vēlams virtuālajā vidē:

```sh
python -m pip install -r requirements-content.txt
npm run content
npm run content:podins
npm run build
```

`npm run content` atjauno kartīšu lapas no `src/marle.html` un `assets/marle_source/`.
`npm run content:podins` atjauno podiņa lapu, tās pārbaudes un ZIP; mainot podiņa kodu/modeli, avoti un lejupielādējamie faili vispirms jāsaskaņo.
CSS avoti atrodas `dist/assets/style.css`, `dist/laps-siets/siets.css` un `dist/podins/podins.css`.
Detalizēti soļi un kļūdu saraksts ir `DEVELOPER_HANDOFF.md`.

## Svarīgi par modeļu stāvokli

V4.1 podiņa sānu austiņām ir 45° balsti un M6 atveru jumtiņi. Abas mainītās formas puses ir pārbaudītas kā slēgti tīkli; to STL ir iekļauti.
Visa podiņa prese vēl nav pabeigta: palikuši pamatnes/STOP augstumu, dobuma konusa, pārplūdes kameras un M12 spēka pārvades labojumi. Marles variants podiņam vēl nav ieviests CAD.
Kartīšu un podiņa PETG konstrukcijām nav fiziski pārbaudītas slodzes robežas.
Iepirkuma cenas un veikalu atlikumi šajā eksportā nav pārbaudīti no jauna; datējumi saglabāti dokumentos.

## Failu integritātes pārbaude

```sh
python handoff/verify_manifest.py
```

ZIP ir pilns failu nodošanas komplekts. Tas pats par sevi nedod pieeju esošās mājaslapas publicēšanai.
Esošās vietnes publicēšanas pieeju tās īpašnieks piešķir atsevišķi.
