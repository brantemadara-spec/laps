import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const host=document.querySelector('#model-canvas');
const status=document.querySelector('#model-status');
const slider=document.querySelector('#assembly-progress');
const playButton=document.querySelector('#play-assembly');
const modeSelect=document.querySelector('#model-choice');
const partTitle=document.querySelector('#part-title');
const partText=document.querySelector('#part-text');
const output=document.querySelector('#assembly-output');
const stageText=document.querySelector('#assembly-stage');
const modelUrls={forma:'/models/forma.glb',starplikas:'/models/starplikas.glb',plaksne:'/models/drenazas_plaksne.glb'};
const description={
 lowerSteel:['Apakšējais tērauda atbalsts','130 × 100 × 8 mm. Izgatavo no tērauda, ar 8 × Ø6,6 mm urbumiem. Sadala slodzi uz PETG plāksni.'],
 lowerPetg:['Apakšējā PETG plāksne','130 × 100 × 12 mm. 77 drenāžas caurumi Ø2 mm; aizmugures rievas 1,6 × 1,2 mm aizvada ūdeni uz malām.'],
 ring:['Maināmā starplika','Šajā salikumā: 3,4 mm augstums 3 mm mitrajai spraugai, pieņemot divus sietus pa 0,20 mm. Kartītes atvērums 85 × 55 mm, R3.'],
 lowerMesh:['Apakšējais šķiedru siets','84,5 × 54,5 mm. Smalks siets notur šķiedras; vēlams 100–200 µm acs. Attēlots sieta biezuma apvalks. Reālo saspiesto biezumu izmēra.'],
 pulp:['Mitrās celulozes masa','85 × 55 mm laukums, šajā salikumā 3 mm mitrais slānis. Šis ir masas apjoma attēlojums; sauso biezumu nosaka žāvēšanas eksperiments.'],
 upperMesh:['Augšējais šķiedru siets','Otrs siets virs masas. Tam jāpaliek dobuma iekšpusē; sietu nedrīkst pārklāt pāri starplikas balsta virsmai.'],
 upperPetg:['Augšējā PETG plāksne','Identiska 12 mm PETG plāksne, salikumā apgriezta ar gludo preses virsmu pret celulozi. Rievas ir ārpusē pret tēraudu.'],
 upperSteel:['Augšējais tērauda atbalsts','Otra 8 mm tērauda plāksne. PETG, siets un metāla atbalsts ir atsevišķas detaļas.'],
 hardware:['M6 metāla stiprinājumi','8 pilnas vītnes M6 × 60 skrūves, 8 M6 uzgriežņi un 16 platās DIN 9021 paplāksnes Ø18 mm. Skrūvju pievilkšana nedod zināmu masas spiedienu.'],
 plate:['Drenāžas plāksne drukāšanai','130 × 100 × 12 mm PETG. Grozi modeli, lai apskatītu aizmugures izvadus. Gludā virsma ir pret masu, rievas — pret tēraudu.']
};
let renderer,scene,camera,controls,currentRoot,currentMode='forma',progress=1,playing=false,lastTime=0,animationFrame=0,requestId=0;
let meshes=[],selected=null;
let highlighted=[];
const cache=new Map();
const loader=new GLTFLoader();
const raycaster=new THREE.Raycaster();
const pointer=new THREE.Vector2();
let pointerStart=null;

function groupFor(mesh,mode){
 if(mode==='plaksne')return 'plate';
 if(mode==='starplikas')return 'spacer';
 const groups=['lowerSteel','lowerPetg','ring','lowerMesh','pulp','upperMesh','upperPetg','upperSteel'];
 const n=parseInt(mesh.name.slice(0,2),10);
 return Number.isFinite(n)&&n>=1&&n<=8?groups[n-1]:'hardware';
}

function setPart(mesh){
 for(const previous of highlighted)previous.material.emissive?.setHex(0);
 highlighted=[];
 selected=mesh;
 document.querySelectorAll('[data-part]').forEach(button=>button.classList.toggle('selected',mesh?.userData.part===button.dataset.part));
 if(!mesh){partTitle.textContent='Izvēlies detaļu';partText.textContent='Pieskaries detaļai modelī vai izvēlies to sarakstā, lai apskatītu izmērus un pielietojumu.';render();return;}
 let desc=description[mesh.userData.part];
 if(mesh.userData.part==='spacer'){
  const match=mesh.name.match(/Starplika_(\d+)mm/);const gap=match?Number(match[1]):3;
  desc=[`${gap} mm mitrās spraugas starplika`, `Fiziskais augstums ${(gap+0.4).toFixed(1).replace('.',',')} mm, ārējais izmērs 130 × 100 mm, dobums 85 × 55 mm, R3. Vienlaikus izmanto vienu gredzenu. Augstums paredz divus 0,20 mm sietus.`];
 }
 partTitle.textContent=desc?.[0]??'Detaļa';partText.textContent=desc?.[1]??'';
 highlighted=mesh.userData.part==='hardware'?meshes.filter(part=>part.userData.part==='hardware'):[mesh];
 for(const part of highlighted)part.material.emissive?.setHex(0x7a3305);
 render();
}

function render(){if(renderer&&scene)renderer.render(scene,camera);}
function resize(){if(!renderer)return;const {width,height}=host.getBoundingClientRect();renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();render();}
function frame(){
 if(!currentRoot)return;
 const box=new THREE.Box3().setFromObject(currentRoot);const center=box.getCenter(new THREE.Vector3());
 const radius=box.getSize(new THREE.Vector3()).length()/2;
 controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(1,.8,1.3).normalize().multiplyScalar(radius*3.1));
 camera.near=Math.max(.0001,radius/100);camera.far=10;camera.updateProjectionMatrix();controls.minDistance=radius*.65;controls.maxDistance=radius*12;controls.update();render();
}

function explodedOffset(mesh){
 const layer={lowerSteel:0,lowerPetg:.020,lowerMesh:.041,ring:.046,pulp:.057,upperMesh:.074,upperPetg:.085,upperSteel:.115};
 const p=mesh.userData.part;
 if(p!=='hardware')return layer[p]??0;
 const n=mesh.name.toLowerCase();
 return (n.includes('upper')||n.includes('nut')) ? .144 : 0;
}

function assemblyStage(t){
 if(t>=.999)return 'Forma salikta · uzgriežņus pievelk pakāpeniski pa diagonāli';
 if(t<.22)return '1 / 5 · apakšējā PETG plāksne un apakšējais siets';
 if(t<.45)return '2 / 5 · starplika un mitrā celulozes masa';
 if(t<.65)return '3 / 5 · augšējais siets un PETG plāksne';
 if(t<.85)return '4 / 5 · augšējais tērauda atbalsts';
 return '5 / 5 · paplāksnes un uzgriežņi';
}

function closeFraction(part,t){
 const ranges={lowerPetg:[0,.22],lowerMesh:[0,.22],ring:[.18,.45],pulp:[.18,.45],upperMesh:[.40,.65],upperPetg:[.40,.65],upperSteel:[.60,.85],hardware:[.78,1]};
 const range=ranges[part]??[0,1];const u=THREE.MathUtils.clamp((t-range[0])/(range[1]-range[0]),0,1);
 return u*u*(3-2*u);
}

function setAssembly(value){
 progress=THREE.MathUtils.clamp(value,0,1);
 if(currentMode==='forma')for(const mesh of meshes){
  mesh.position.copy(mesh.userData.rest);
  mesh.position.y+=explodedOffset(mesh)*(1-closeFraction(mesh.userData.part,progress));
 }
 slider.value=String(Math.round(progress*100));output.value=`${Math.round(progress*100)}%`;output.textContent=output.value;
 const stage=assemblyStage(progress);if(stageText.textContent!==stage)stageText.textContent=stage;
 slider.setAttribute('aria-valuetext',`${Math.round(progress*100)} procenti salikts`);render();
}

function stop(){playing=false;playButton.textContent='Salikšanas animācija';playButton.setAttribute('aria-pressed','false');if(animationFrame)cancelAnimationFrame(animationFrame);animationFrame=0;}
function tick(time){
 if(!playing)return;
 if(!lastTime)lastTime=time;
 const delta=Math.max((time-lastTime)/1000,0);lastTime=time;setAssembly(progress+delta/9);
 if(progress>=1){stop();frame();return;}
 animationFrame=requestAnimationFrame(tick);
}
function play(){
 if(playing){stop();return;}
 if(progress>=.999)setAssembly(0);
 playing=true;lastTime=0;playButton.textContent='Apturēt animāciju';playButton.setAttribute('aria-pressed','true');
 frame();animationFrame=requestAnimationFrame(tick);
}

async function loadMode(mode){
 const id=++requestId;stop();status.hidden=false;status.textContent='Ielādē 3D modeli…';modeSelect.disabled=true;
 try{
  let model=cache.get(mode);
  if(!model){
   const gltf=await loader.loadAsync(modelUrls[mode]);model=gltf.scene;
   model.traverse(mesh=>{if(mesh.isMesh){mesh.material=mesh.material.clone();mesh.userData.rest=mesh.position.clone();mesh.userData.part=groupFor(mesh,mode);mesh.material.side=THREE.DoubleSide;}});
   cache.set(mode,model);
  }
  if(id!==requestId)return;
  if(currentRoot)scene.remove(currentRoot);currentRoot=model;currentMode=mode;scene.add(model);meshes=[];
  model.traverse(mesh=>{if(mesh.isMesh)meshes.push(mesh);});
  setPart(null);document.querySelector('#assembly-controls').hidden=mode!=='forma';document.querySelector('#part-buttons').hidden=mode!=='forma';
  setAssembly(mode==='forma'?progress:1);frame();status.hidden=true;
  document.querySelector('#model-label').textContent={forma:'Forma · 3 mm mitrā sprauga',starplikas:'Piecas starplikas · 1–5 mm mitrā sprauga',plaksne:'PETG drenāžas plāksne · abi sāni'}[mode];
  host.dataset.ready='true';host.dataset.mode=mode;
 }catch(error){status.hidden=false;status.textContent='3D modeli nevarēja ielādēt. Izmanto lejupielādējamo Blender failu vai mēģini vēlreiz.';console.error(error);}
 finally{if(id===requestId)modeSelect.disabled=false;}
}

try{
 renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'default'});
 renderer.setPixelRatio(Math.min(window.devicePixelRatio,1.5));renderer.setClearColor(0xf2f6f6);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.95;
 renderer.domElement.setAttribute('aria-label','Interaktīvs 3D presformas modelis');renderer.domElement.setAttribute('role','img');host.appendChild(renderer.domElement);
 scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(37,1,.001,10);
 const environment=new THREE.PMREMGenerator(renderer);scene.environment=environment.fromScene(new RoomEnvironment(),.04).texture;scene.environmentIntensity=.85;environment.dispose();
 scene.add(new THREE.HemisphereLight(0xffffff,0x9baeb6,.7));
 const light=new THREE.DirectionalLight(0xffffff,1.2);light.position.set(.3,.5,.4);scene.add(light);
 const fill=new THREE.DirectionalLight(0xdef4f4,.4);fill.position.set(-.4,.2,-.3);scene.add(fill);
 controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=false;controls.addEventListener('change',render);
 new ResizeObserver(resize).observe(host);
 renderer.domElement.addEventListener('pointerdown',event=>{pointerStart=[event.clientX,event.clientY];});
 renderer.domElement.addEventListener('pointerup',event=>{
  if(!pointerStart||Math.hypot(event.clientX-pointerStart[0],event.clientY-pointerStart[1])>6)return;
  const rect=renderer.domElement.getBoundingClientRect();pointer.set((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);
  raycaster.setFromCamera(pointer,camera);const hits=raycaster.intersectObjects(meshes,false);if(hits.length)setPart(hits[0].object);
 });
 modeSelect.addEventListener('change',()=>loadMode(modeSelect.value));
 playButton.addEventListener('click',play);
 slider.addEventListener('input',()=>{stop();setAssembly(Number(slider.value)/100);});
 document.querySelector('#assembled').addEventListener('click',()=>{stop();setAssembly(1);frame();});
 document.querySelector('#exploded').addEventListener('click',()=>{stop();setAssembly(0);frame();});
 document.querySelector('#reset-camera').addEventListener('click',frame);
 document.querySelectorAll('[data-part]').forEach(button=>button.addEventListener('click',()=>setPart(meshes.find(mesh=>mesh.userData.part===button.dataset.part))));
 document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
 window.__LAPS_VIEWER={get state(){return {mode:currentMode,progress,playing,meshes:meshes.length,selected:selected?.userData.part};}};
 resize();loadMode('forma');
}catch(error){
 status.textContent='Šajā ierīcē 3D apskate nav pieejama. Modeļus vari lejupielādēt Blender vai iPhone AR skatam.';console.error(error);
 document.querySelectorAll('#viewer-panel button,#viewer-panel input,#viewer-panel select').forEach(control=>control.disabled=true);
}

async function initDocuments(){
 const tabs=document.querySelector('#document-tabs');const select=document.querySelector('#document-choice');const pageImage=document.querySelector('#document-image');
 try{
  const response=await fetch('/documents/catalog.json');if(!response.ok)throw new Error('catalog');const docs=await response.json();
  let docIndex=0,pageIndex=0;
  function paint(){
   const doc=docs[docIndex],page=doc.pages[pageIndex];
   pageImage.src="/"+page.image;pageImage.alt=`${doc.title}, ${pageIndex+1}. lapa — ${page.title}`;
   document.querySelector('#document-title').textContent=doc.title;
   document.querySelector('#page-title').textContent=page.title;
   document.querySelector('#page-count').textContent=`${pageIndex+1} / ${doc.pages.length}`;
   document.querySelector('#document-pdf').href='/' +doc.pdf;
   document.querySelector('#document-fullpage').href='/' +page.image;
   document.querySelector('#document-language').textContent=doc.language==='en'?'Angliski':'Latviski';
   document.querySelector('#previous-page').disabled=pageIndex===0;document.querySelector('#next-page').disabled=pageIndex===doc.pages.length-1;
   document.querySelectorAll('[data-document]').forEach(button=>button.setAttribute('aria-pressed',String(Number(button.dataset.document)===docIndex)));
   select.value=String(pageIndex);document.querySelector('#document-reader').dataset.document=doc.id;document.querySelector('#document-reader').dataset.page=String(pageIndex+1);
  }
  function switchDoc(index){
   docIndex=index;pageIndex=0;select.innerHTML='';
   docs[docIndex].pages.forEach((page,i)=>{const option=document.createElement('option');option.value=String(i);option.textContent=`${i+1}. ${page.title}`;select.append(option);});paint();
  }
  docs.forEach((doc,i)=>{
   const button=document.createElement('button');button.type='button';button.className='doc-tab';button.dataset.document=String(i);button.textContent=`${doc.short_title} · ${doc.pages.length}`;button.addEventListener('click',()=>switchDoc(i));tabs.append(button);
  });
  select.addEventListener('change',()=>{pageIndex=Number(select.value);paint();});
  document.querySelector('#previous-page').addEventListener('click',()=>{if(pageIndex>0){pageIndex--;paint();}});
  document.querySelector('#next-page').addEventListener('click',()=>{if(pageIndex<docs[docIndex].pages.length-1){pageIndex++;paint();}});
  pageImage.addEventListener('load',()=>pageImage.classList.add('loaded'));
  switchDoc(0);
 }catch(error){document.querySelector('#document-title').textContent='Dokumentu lapas nevarēja ielādēt. PDF faili ir pieejami lejupielāžu sadaļā.';console.error(error);}
}
initDocuments();
