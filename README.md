# LAPS — mājaslapa un 3D prototipi

Pilns LAPS projekta avota kods, 3D modeļi, rasējumi un lietošanas dokumenti.
Šī versija sagatavota no publicētās mājaslapas **8. versijas** un 09.11.2026. nodošanas komplekta.

**Mājaslapa:** https://laps.dashulyaashsxb.chatgpt.site/

- **Kartīšu forma:** LAPS Marle Rev C — divas PETG plāksnes, marle, četri stūra stiprinājumi un maināmas starplikas.
- **Podiņa forma:** V4.1 — divdaļīga forma, 3 / 4 / 5 mm serdeņi, slīpi 45° austiņu balsti.
- **Arhīvs:** iepriekšējās Rev A konstrukcijas faili un dokumenti.

## Sāc šeit

- [Palaišana un projekta apraksts latviski](README_SAKT_SEIT_LV.md)
- [Detalizētas norādes izstrādātājam](DEVELOPER_HANDOFF.md)
- [3D modeļu un dokumentu saraksts](MODEL_INDEX.md)

## Vietējā apskate

Izpako vai noklonē repozitoriju un atver termināli projekta saknē:

```sh
python -m http.server 8000 --directory dist
```

Atver **http://localhost:8000/**. Ja vajag, `python` vietā lieto `python3` vai `py`.
3D modeļiem vajadzīgs HTTP serveris; neatver HTML tieši kā failu.

## Izstrāde

Node.js 20+ un Python 3.10+.

```sh
npm ci
npm run build
```

Lai pārbūvētu arī HTML saturu un dokumentu lapas:

```sh
python -m pip install -r requirements-content.txt
npm run content
npm run content:podins
npm run build
```

## Failu struktūra

| Mape | Saturs |
| --- | --- |
| `dist/` | Gatava mājaslapa ar visām lapām, attēliem, PDF, 3D modeļiem un lejupielādēm |
| `src/` | HTML šabloni un JavaScript: 3D apskate, animācija, dokumentu lasītājs |
| `assets/marle_source/` | Kartīšu formas STL, STEP, Blender, SVG rasējumi un ģeneratora ievaddati |
| `content/podins/` | Podiņa Python kods un ģeometrijas pārbaudes |
| `handoff/` | Izcelsmes dati, pārbaudes un failu SHA-256 kontrolsummas |

Blender, STL, STEP, GLB un pieejamie iPhone AR USDZ faili ir saglabāti. Vecie lejupielāžu ZIP arhīvi arī ir iekļauti.

## Modeļu stāvoklis

Podiņa V4.1 divām mainītajām formas pusēm ir pārbaudīti slēgti STL tīkli. Pamatnes/STOP atskaites, dobuma konuss, pārplūdes kamera, marles balsts un M12 spēka pārvade vēl jāpārstrādā. Konstrukcijām nav fiziski pārbaudītas PETG slodzes robežas. Sīkāka informācija ir [izstrādātāja piezīmēs](DEVELOPER_HANDOFF.md#known-next-engineering-work).

Failu sākotnējo integritāti var pārbaudīt ar:

```sh
python handoff/verify_manifest.py
```

Kontrolsummas attiecas uz sākotnējo nodošanas komplektu; pēc izmaiņām atjauno arī manifestu un pārbaužu datus.

Esošās LAPS mājaslapas publicēšana ir atsevišķs solis; repozitorija atjaunināšana pati par sevi nemaina publicēto vietni.
