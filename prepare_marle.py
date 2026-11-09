"""Prepare the current Rev C content; the original project remains in /arhivs/."""
from pathlib import Path
import html, json, shutil, zipfile
import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'assets/marle_source'
PUBLIC = ROOT / 'dist/laps-siets'
e = html.escape
renders = [
    ('01_assembled_45deg.png', 'Salikta forma · 45°'),
    ('02_exploded_assembly.png', 'Izjaukts salikums'),
    ('03_grid_and_gauze_detail.png', 'PETG režģis un kokvilnas marle'),
    ('04_all_calibration_bases_and_shims.png', 'Četri kalibratori un trīs starpliku izmēri'),
    ('05_assembled_side.png', 'Saliktas formas sānskats'),
]
pdf_name = 'LAPS_Marle_Rasejumi_un_Pamaciba_LV.pdf'
proc_name = 'LAPS_Marle_Iepirkums_LV.pdf'
cad_files = sorted(SOURCE.joinpath('cad').glob('*.stl')) + sorted(SOURCE.joinpath('cad').glob('*.step'))
assert len(cad_files) == 17, 'Expected 8 printable STL, 8 component STEP and one assembly STEP.'
required = [SOURCE/'docs'/pdf_name, SOURCE/'procurement/LAPS_Marle_Iepirkums_DEPO_Bergi_LV.pdf',
    SOURCE/'blender/LAPS_Marle_Prototips.blend', SOURCE/'blender/LAPS_Marle_Blender.py', SOURCE/'visual/LAPS_Marle.blend']
required += [SOURCE/'visual/renders'/name for name, _ in renders]
required += [SOURCE/'visual/models'/f'{name}.{ext}' for name in ('assembly','grid','shims') for ext in ('glb','usdz')]
assert all(path.is_file() for path in required), 'Finish generating source assets before packaging.'
# Remove only the superseded, generated Rev B variant assets, after source checks.
for folder in ('files', 'models', 'documents', 'images'):
    target = PUBLIC / folder
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(target.rglob('*'), reverse=True):
        if path.is_file(): path.unlink()
        elif path.is_dir(): path.rmdir()
files = PUBLIC/'files'
for source, name in [(SOURCE/'docs'/pdf_name,pdf_name),
        (SOURCE/'procurement/LAPS_Marle_Iepirkums_DEPO_Bergi_LV.pdf',proc_name),
        (SOURCE/'procurement/LAPS_Marle_Iepirkums_DEPO_Bergi_LV.csv','LAPS_Marle_Iepirkums_LV.csv'),
        (SOURCE/'procurement/LAPS_Marle_Cenu_alternativas_LV.csv','LAPS_Marle_Cenu_alternativas_LV.csv'),
        (SOURCE/'blender/LAPS_Marle_Prototips.blend','LAPS_Marle_Prototips.blend'),
        (SOURCE/'blender/LAPS_Marle_Blender.py','LAPS_Marle_Blender.py'),
        (SOURCE/'visual/LAPS_Marle.blend','LAPS_Marle_Vizualizacija.blend')]:
    shutil.copy2(source,files/name)
for mode in ('assembly','grid','shims'):
    shutil.copy2(SOURCE/'visual/models'/f'{mode}.glb',PUBLIC/'models'/f'{mode}.glb')
    shutil.copy2(SOURCE/'visual/models'/f'{mode}.usdz',files/f'{mode}.usdz')

docs = json.loads((SOURCE/'docs/catalog.json').read_text())
pages = []
for page in docs['pages']:
    name = Path(page['path']).name
    shutil.copy2(SOURCE/'docs'/page['path'],PUBLIC/'documents'/name)
    pages.append({**page,'image':'/laps-siets/documents/'+name})
catalog = [{**docs,'short_title':'Rasējumi un pamācība','pdf':'/laps-siets/files/'+pdf_name,'pages':pages}]
purchase_titles = ['Nepieciešamie izmēri · DEPO Berģi', 'Pārbaudītās cenu alternatīvas', 'Avoti un iepakojumu budžets']
with fitz.open(files/proc_name) as pdf:
    purchase_pages=[]
    for index, page in enumerate(pdf):
        name=f'procurement-{index+1:02}.webp'
        pix=page.get_pixmap(matrix=fitz.Matrix(1000/page.rect.width,1000/page.rect.width),alpha=False)
        image=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        image.save(PUBLIC/'documents'/name,'WEBP',quality=90)
        purchase_pages.append({'number':index+1,'title':purchase_titles[index],'image':'/laps-siets/documents/'+name,'width':pix.width,'height':pix.height})
catalog.append({'id':'procurement','title':'LAPS Marle — aktuālais iepirkums','short_title':'Iepirkums un cenas','language':'lv','pdf':'/laps-siets/files/'+proc_name,'pages':purchase_pages})
(PUBLIC/'documents/catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')

p = json.loads((SOURCE/'procurement_verified.json').read_text())
def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+e(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+cell+'</td>' for cell in row)+'</tr>' for row in rows)+'</tbody></table></div>'
rows = [[e(item['part_lv']),str(item['qty']),e(item['dimensions']),'Cena un krājumi nav apstiprināti'] for item in p['required']]
procurement = '<p><strong>DEPO Berģi, Siguldas šoseja 6.</strong> Zemāk ir vajadzīgie izmēri un daudzumi, ko meklēt veikalā. Konkrētā veikala cenas un atlikums šajā pārbaudē nav apstiprināti.</p>'
procurement += table(['Detaļa','Vajag','Izmērs','DEPO Berģi'],rows)
alternatives = [item for item in p['verified_alternatives'] if item.get('sku') not in ('FOR-933-6X40','93310M-6X40')]
rows=[]
for item in alternatives:
    price=next(item[key] for key in ('calculated_pack_price_eur_with_vat','published_pack_price_eur_with_vat','published_pack_price_eur') if key in item)
    note=item.get('availability_lv') or 'Cena pārbaudīta; atlikums nav apstiprināts.'
    if item['required_id']=='bolts': note += ' A2 materiāls; stiprības klase nav norādīta.'
    rows.append([e(item['part_lv']),f'<a href="{e(item["source_url"],quote=True)}" target="_blank" rel="noopener">{e(item["supplier"])}</a>',str(item['pack_qty']),f'{price:.2f} €'.replace('.',','),e(note)])
procurement += '<h3>Pārbaudītas alternatīvas ārpus DEPO</h3><p>Cenas pārbaudītas 07.10.2026. Norādīta viena pilna iepakojuma cena ar PVN; nepieciešamais detaļu skaits ir mazāks par iepakojumu. Piegāde nav iekļauta.</p>'
procurement += table(['Prece','Veikals un avots','Iepakojumā','Iepakojuma cena','Pieejamības piezīme'],rows)
procurement += '<p>Šo alternatīvu iepakojumi — A2 skrūves, uzgriežņi, paplāksnes un marle — kopā <strong>13,34 €</strong>. Ar jaunu PETG spoli: <strong>28,24 €</strong>. Tā ir alternatīvu pirkuma summa. DEPO kopējā cena nav zināma. Esošos piemērotos uzgriežņus, paplāksnes un PETG vari izmantot atkārtoti.</p>'

gallery=[]
for name, title in renders:
    source=SOURCE/'visual/renders'/name
    shutil.copy2(source,PUBLIC/'images'/name)
    image=Image.open(source).convert('RGB'); image.thumbnail((1200,900))
    preview=Path(name).stem+'.webp'; image.save(PUBLIC/'images'/preview,'WEBP',quality=87)
    gallery.append(f'<figure><a href="/laps-siets/images/{name}" target="_blank" rel="noopener"><img src="/laps-siets/images/{preview}" alt="{e(title,quote=True)}" loading="lazy" width="1200" height="900"></a><figcaption>{e(title)} · <a href="/laps-siets/images/{name}" download>PNG</a></figcaption></figure>')
ar=[]
for mode, title, image in [('assembly','Visa forma iPhone AR',renders[0][0]),('grid','Režģis un marle iPhone AR',renders[2][0]),('shims','Kalibratori un starplikas iPhone AR',renders[3][0])]:
    ar.append(f'<a rel="ar" class="ar-link" href="/laps-siets/files/{mode}.usdz"><img src="/laps-siets/images/{Path(image).stem}.webp" alt="{e(title,quote=True)}" width="1200" height="900"><strong>{e(title)}</strong><span>USDZ · atvērt telpā</span></a>')
template=(ROOT/'src/marle.html').read_text()
template=template.replace('__MARLE_PROCUREMENT__',procurement).replace('__MARLE_GALLERY__',''.join(gallery)).replace('__MARLE_AR__',''.join(ar))
assert '__MARLE_' not in template
(ROOT/'dist/index.html').write_text(template)
(PUBLIC/'index.html').write_text(template)

readme=(SOURCE/'docs/README_LV.txt').read_text()+'''\nDRUKAS FAILI\nSTL koordinātas ir milimetros. Drukā marle_plate_PRINT_2.stl divreiz; marle_shim_0.5 / 1.0 / 1.5mm_PRINT_2.stl katru divreiz. Izvēlies vienu kompensācijas gredzenu; kalibrācijas izmēģinājumam var izdrukāt visus četrus. Marles un masas aploksnes nav drukājamas detaļas.\n\nBlender: File > Open gatavo BLEND, vai Scripting > New > ievieto PY > Run Script. Kods saglabā savu ainu un eksportē STL norādītajā direktorijā. Pirms drukas pārbaudi slicer izmērus, orientāciju un tiltiņus. Aizmugures kanāli ir 1,2 mm dziļi, to īsos tiltiņus un pirmā slāņa saķeri izmēģina uz pirmās plāksnes. Neaizpildi drenāžas kanālus ar balstiem un neieslēdz fuzzy skin uz piespiešanas/atdures virsmām.\n\nŠajā ZIP ir izgatavošanas faili un LAPS_Marle_Vizualizacija.blend — salikuma aina ar kamerām, apgaismojumu un iekļautām tekstūrām. 3D tīmekļa GLB, iPhone USDZ un PNG skati pieejami atsevišķi mājaslapā. Pastāvīgā adrese: https://laps.dashulyaashsxb.chatgpt.site\n'''
(files/'README_LV.txt').write_text(readme)
with zipfile.ZipFile(files/'LAPS_Marle_Drukas_faili.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as out:
    for source in sorted(SOURCE.joinpath('cad').glob('*.stl')): out.write(source,'STL/'+source.name)
    out.writestr('README_LV.txt',readme)
with zipfile.ZipFile(files/'LAPS_Marle_Prototips.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as out:
    for source in cad_files: out.write(source,'CAD/'+source.name)
    for name in ('LAPS_Marle_Prototips.blend','LAPS_Marle_Blender.py','LAPS_Marle_Vizualizacija.blend'): out.write(files/name,'Blender/'+name)
    for name in (pdf_name,proc_name,'LAPS_Marle_Iepirkums_LV.csv','LAPS_Marle_Cenu_alternativas_LV.csv'): out.write(files/name,'Dokumenti/'+name)
    for source in sorted(SOURCE.joinpath('docs').glob('*.svg')): out.write(source,'Rasejumi_SVG/'+source.name)
    out.write(SOURCE/'data/marle_dimensions.json','Dati/marle_dimensions.json')
    out.write(SOURCE/'procurement_verified.json','Dati/procurement_verified.json')
    out.writestr('README_LV.txt',readme)
for path in PUBLIC.rglob('*'):
    if path.is_file(): assert path.stat().st_size < 25*1024*1024, f'Static asset too large: {path}'
print(json.dumps({'revision':'C','documents':len(catalog),'pages':sum(len(d['pages']) for d in catalog),'renders':len(renders),'stl':8,'full_zip_bytes':(files/'LAPS_Marle_Prototips.zip').stat().st_size}))
