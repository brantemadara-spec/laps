"""Build the focused V4.1 ear revision from its source and measured reports."""
from pathlib import Path
import html,json,zipfile
r=Path(__file__).resolve().parent
p=r/'dist/podins';s=r/'content/podins';stem='NO_KOKA_UZ_KOKU_Podina_prototips'
code=(s/(stem+'.py')).read_text()
native=json.loads((s/'review.json').read_text())
eng=json.loads((s/'engineering_review.json').read_text())
escape=html.escape
verification=f"V4.1 izpildīts Blender 4.3.2: 9 formas detaļas un {native['boolean_apply_successful_returns']} Boolean darbības. Jaunajām austiņām ir 45° apakšējie balsti un M6 atveru jumtiņi. Modeļa mērogs: pamatnes Ø150 mm atbilst 0,15 m."
notes='Austiņu iepriekšējā pārklāšanās un ievirzīšanās dobumā ir novērsta; atjauninātie mērījumi norādīti zemāk. Pamatnes/STOP atskaites un dobuma koniskums vēl jākoriģē, bet pārplūdes kamerai joprojām ir atvērtas malas. V4.1 ir fokusēts austiņu labojums, un visa prese vēl nav apstiprināta darbībai.'
def table(head,rows):
 return '<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+escape(v)+'</th>' for v in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
labels={'pins_holes':'Nominālā sprauga der; jāpārbauda PETG paraugs','overflow_fit':'Sēžas sprauga der; ir citas neatbilstības','core_stop':'STOP sakrīt; dibena atskaite jākoriģē'}
result=table(['Pārbaude','Rezultāts','Konstatētais'],[[c['title_lv'],labels.get(c['id'],'Jālabo'),c['details_lv']] for c in eng['categories']])
wall=next(c for c in eng['categories'] if c['id']=='wall_thickness')
def mm(v):return f'{v:.3f}'.replace('.',',')
result+='<h3>Sieniņas radiālā sprauga pie konstrukcijas atskaitēm</h3><p>V4.1 dobums atkārtoti izgriezts pēc austiņu pievienošanas, novēršot to ievirzīšanos masā. Paliek sākotnējais 72 mm dobuma koniskums; šīs nominālās spraugas joprojām nedaudz mainās ar augstumu.</p>'
result+=table(['Serdenis','Radiāli Z4','Radiāli Z70','Perpendikulāri serdei pie Z4','Perpendikulāri serdei pie Z70'],[[str(int(w['named_wall_mm']))+' mm',mm(w['unobstructed_radial_gap_z4_mm'])+' mm',mm(w['unobstructed_radial_gap_z70_mm'])+' mm',mm(w['normal_to_core_gap_at_outer_z4_mm'])+' mm',mm(w['normal_to_core_gap_at_outer_z70_mm'])+' mm'] for w in wall['wall_results']])
numeric_rows=[
['Tapas un ligzdas','Ø5 / Ø5,6 mm: 0,3 mm radiāli un 0,8 mm aksiāli; jāizmēģina PETG paraugs.'],
['Formas pušu austiņas','V4.1 dalījuma plaknes X0; slīpie balsti 45°. Vecā 1 mm sadure labota. Jaunās M6 asis Z34/Z54 mm un balsta plaknes X±12 mm.'],
['Pamatnes ligzdas mala','Atstarpe −0,069 līdz −0,035 mm — negatīva vērtība nozīmē saduri.'],
['Kameras svārks','Atstarpe ≈0,370–0,415 mm uz pusi; nomināli Ø110,8 uz Ø110.'],
['M6 stieņi pret kameru','Nomināli 0 mm rezerve: R65 − 3 − R62 = 0; jāparedz pozitīva atstarpe.'],
['STOP atdure','Kameras augša un STOP apakša Z82; kontakta josla R51–R59 ir 8 mm plata.'],
['Dibens un gala augstums','Ja forma hipotētiski pilnībā iesēstos 2,5 mm ligzdā, dibens būtu 1,5 mm un augstums 67,5 mm. Pilnu iesēšanos vēl traucē pamatnes ligzdas sadure; tas nav apstiprināts gala podiņš.'],
['Dobuma gala diametri','Nominālās atskaitēs Ø65,347 pie Z0 un Ø89,653 pie Z70; vajadzīgie Ø65/Ø90 nav precīzi saglabāti.']]
result+='<h3>Konkrētās salāgošanas spraugas</h3>'+table(['Vieta','Izmērītais / aprēķinātais'],numeric_rows)
native_parts=next(c for c in eng['categories'] if c['id']=='native_manifold')['per_part']
stl_parts={v['name']:v for v in next(c for c in eng['categories'] if c['id']=='stl_recheck')['per_part']}
result+='<h3>Visu deviņu detaļu topoloģija</h3>'+table(['Detaļa','Native atvērtās malas','Native neatbilstošās malas','STL deģenerēti trijstūri','STL neatbilstošās malas'],[[v['name'],v['boundary_edges'],v['nonmanifold_edges'],stl_parts[v['name']]['degenerate_triangles'],stl_parts[v['name']]['nonmanifold_edges']] for v in native_parts])
result+='<p>V4.1 mainītajām formas pusēm piemērota dokumentēta mikroskopisku triangulācijas defektu tīrīšana un pārbaudīti faktiskie STL. Kamerai joprojām ir atvērtas robežmalas; šī atjauninātā tabula attiecas uz V4.1 failiem. Visa komplekta atlikušajiem labojumiem vajadzīga atkārtota pārbaude.</p>'
advice=json.loads((s/'gauze_and_experiment_advice.json').read_text())
volume_rows=[[str(int(v['nominal_radial_wall_mm']))+' mm',f"{v['ideal_material_volume_cm3']:.3f}".replace('.',',')+' cm³',f"{v['dry_mass_ratio_for_equal_apparent_density']:.3f}".replace('.',',')] for v in advice['ideal_target_geometry']['rows']]
extra=(r/'src/pot_posters_and_advice.html').read_text().replace('__POT_VOLUME_TABLE__',table(['Mērķa radiālā siena','Aprēķinātais materiāla tilpums','Relatīvā sausā deva'],volume_rows))
page=(r/'src/podins.html').read_text().replace('__POT_POSTERS_ADVICE__',extra).replace('__POT_EAR_UPDATE__',(r/'src/pot_ears_update.html').read_text())
for marker,value in [('__POT_VERIFICATION__',escape(verification)),('__POT_GEOMETRY_NOTES__',escape(notes)),('__POT_ENGINEERING_TABLE__',result),('__POT_LINE_COUNT__',str(len(code.splitlines()))),('__POT_CODE__',escape(code))]:page=page.replace(marker,value)
assert '__POT_' not in page
(p/'index.html').write_text(page)
report='NO KOKA UZ KOKU — V4.1 ĢEOMETRIJAS PĀRBAUDE / 26.10.2026.\n\n'+verification+'\n\n'+notes+'\n\n'
for c in eng['categories']:report+=c['title_lv']+'\n'+c['details_lv']+'\n\n'
report+='SIENAS (radiāli Z4 / Z70)\n'
for w in wall['wall_results']:report+=f"Serdenis {w['named_wall_mm']:g} mm: {mm(w['unobstructed_radial_gap_z4_mm'])} / {mm(w['unobstructed_radial_gap_z70_mm'])} mm.\n"
report+='\nSALĀGOŠANA\n'+'\n'.join(a+': '+b for a,b in numeric_rows)
report+='\n\nKopīgās atskaites: formas nominālā ģeometrija Z0..70, serdes apakša Z4, STOP Z82. Kameru sēžai pārvieto +70. Detaļu kataloga pozīcijas nav salikuma pozīcijas. Hipotētiskais dibens 1,5 mm / augstums 67,5 mm nav apstiprināts salikums — iesēšanos bloķē sadures.\n'
report+='\nŠie rezultāti nepārbauda PETG faktisko precizitāti, spēka/griezes momenta nestspēju, ilglaicīgo deformāciju vai sausa podiņa sarukumu. Skaitliskie dati: V41_Parbaudes_dati.json.\n'
(p/'files/V41_Geometrijas_parbaude_LV.txt').write_text(report)
(p/'files/V41_Parbaudes_dati.json').write_text(json.dumps({'prototype':'V4.1','native':native,'engineering':eng,'proposed_gauze_and_experiment_advice':advice},ensure_ascii=False,indent=2)+'\n')
readme='''NO KOKA UZ KOKU — PODIŅA PROTOTIPS V4.1
V4.1 pielāgots no iesūtītā V4: mainītas sānu austiņas un atveres, atkārtoti izgriezts dobums un tapu ligzdas, tīrīti tikai mainīto daļu mikroskopiskie triangulācijas defekti.

PY — aktuālais V4.1 kods; BLEND — tā detaļu kataloga izpildes rezultāts Blender 4.3.2.
Izvēlies vienu no 3/4/5 mm serdeņiem. Kodā deviņas formas detaļas; metāla M6/M12 stiprinājumus nedrukā.

Kods izdzēš visus aktīvās ainas objektus. Saglabā esošo darbu un atver jaunu ainu. Scripting > New > ielīmē kodu > Run Script (Alt+P koda logā). BLEND: File > Open.

Kods pats STL neeksportē. Atlasi vienu detaļu: File > Export > STL, Selection Only, Apply Modifiers. Vienības mm: Scale 1, Scene Unit izslēgts, ja redzama šī opcija. Slicerī pārbaudi pamatnes/augšējās plāksnes Ø150 mm un drukas orientāciju. Detaļu katalogs nav salikta forma.

Pirms drukas jānovērš norādītās neatbilstības. ZIP nav apstiprināts drukai.

'''+report+'\nAustiņas drukā stāvus ar Z asi augšup. Sānu M6: DIN125 OD12 paplāksnes; 10 mm plānsienu muciņa ar ārējo OD līdz15 mm. Slīpie balsti un caurumu jumtiņi samazina austiņu pārkares, bet pārējo virsmu/tapu atbalsti jāpārbauda slicerī.\n\nMarles risinājums un vienādu apstākļu plāns ir atsevišķas ieteikumu norādes. V4.1 CAD failos saglabāts sākotnējais perforētais ieliktnis. Lai atteiktos no atsevišķā ieliktņa, jāpārveido pamatnes cietais balsts un jāprecizē STOP atskaites. Pilns skaidrojums Marle_un_izmeginajums_LV.txt un mājaslapā.\n\nPilna pamācība: https://laps.dashulyaashsxb.chatgpt.site/podins/\n'
(p/'files/README_LV.txt').write_text(readme)
with zipfile.ZipFile(p/'files'/(stem+'.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for ext in ['.py','.blend']:z.write(p/'files'/(stem+ext),stem+ext)
 for name in ['01_MOLD_LEFT.stl','02_MOLD_RIGHT.stl']:z.write(p/'files'/name,'Mainitas_STL_dalas/'+name)
 for name in ['README_LV.txt','V41_Geometrijas_parbaude_LV.txt','V41_Parbaudes_dati.json','Marle_un_izmeginajums_LV.txt']:z.write(p/'files'/name,name)
card='''<!-- PODINS_SECTION_START -->
<section id="podins"><p class="eyebrow">Jaunākā podiņa versija · V4.1</p><h2>Podiņa prototips V4.1</h2><p>Divdaļīga forma, maināmi 3 / 4 / 5 mm serdeņi, pārplūdes kamera un drenāžas pamatne. Gala podiņa mērķa izmēri: augša Ø90 mm, apakša Ø65 mm, augstums 70 mm.</p><p class="small">V4.1 sānu austiņām ir 45° pārejas un M6 atveru jumtiņi. Atjaunināts modelis, Blender kods un pārbaudes; pārējo mezglu atlikušās neatbilstības norādītas podiņa lapā.</p><a class="prototype-card-link" href="/podins/"><strong>Atvērt podiņa prototipu V4.1 →</strong><span>9 detaļu apskate · abi salikšanas plakāti · marle un salīdzināms eksperiments</span></a></section>
<!-- PODINS_SECTION_END -->
'''
for target in [r/'src/marle.html',r/'dist/index.html',r/'dist/laps-siets/index.html']:
 text=target.read_text();before,rest=text.split('<!-- PODINS_SECTION_START -->',1);_,after=rest.split('<!-- PODINS_SECTION_END -->',1);target.write_text(before+card+after.lstrip('\n'))
print(json.dumps({'version':'V4.1','code_lines':len(code.splitlines()),'source_matches_download':(s/(stem+'.py')).read_bytes()==(p/'files'/(stem+'.py')).read_bytes(),'engineering_categories':len(eng['categories']),'zip_bytes':(p/'files'/(stem+'.zip')).stat().st_size}))
