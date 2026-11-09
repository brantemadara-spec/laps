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
const modelUrls={assembly:'/laps-siets/models/assembly.glb',grid:'/laps-siets/models/grid.glb',shims:'/laps-siets/models/shims.glb'};
const description={"lowerPetg": ["Apakšējā PETG plāksne", "130 × 100 × 10 mm, R6. 345 kvadrātveida 2 × 2 mm atvērumi, 1,6 mm ribas. Četri Ø6,6 mm stūra urbumi. Aizmugurē drenāžas kanāli abos virzienos."], "upperPetg": ["Augšējā PETG plāksne", "Identiska 10 mm plāksne, apgriezta ar gludo darba virsmu pret masu. Augšpusē redzams vienmērīgs drenāžas režģis."], "lowerGauze": ["Apakšējā marle", "Pērkama tīra kokvilnas marle, 84,5 × 54,5 mm. Sāk ar vienu atlocītu kārtu. Modelī 0,20 mm ir piemērs; faktisko saspiesto biezumu izmēra."], "upperGauze": ["Augšējā marle", "Otrs kokvilnas marles gabals pret kartīti. Abās pusēs jābūt vienmērīgiem slāņiem. Kārtu skaita vai marles maiņa prasa jaunu biezuma kalibrāciju."], "base": ["Izvēlētais 0,4 mm kompensācijas gredzens", "Modelī šis ir piemērs divām 0,20 mm marles kārtām. Reāli izvēlas vienu no 0,2 / 0,4 / 0,6 / 0,8 mm gredzeniem pēc abu saspiesto marles paku kopējā izmērītā biezuma."], "shim05": ["0,5 mm papildu starplika", "Fiziskais biezums 0,5 mm. 130 × 100 mm, dobums 85 × 55 mm R3, četri stūra urbumi. Summē ar pārējiem papildu gredzeniem."], "shim10": ["1 mm papildu starplika", "Fiziskais biezums 1 mm. Komplektā drukā divus. Saspiestā marle un izvēlētais kompensācijas gredzens nosaka faktisko mitro spraugu."], "shim15": ["1,5 mm papildu starplika", "Fiziskais biezums 1,5 mm. Šajā salikumā 0,5 + 1 + 1,5 mm papildgredzeni dod 3 mm mērķi tikai tad, ja kompensācija sakrīt ar marles biezumu."], "pulp": ["Papīra un lapu masa", "85 × 55 mm, R3. Attēlots 3 mm mitrās spraugas piemērs. Marles nospiedumu, šķiedru zudumu un sauso biezumu nosaka ar reālo masu."], "hardware": ["Četri M6 × 40 stiprinājumi", "4 pilnas vītnes metāla M6 × 40 skrūves, 4 M6 uzgriežņi un 8 DIN 9021 paplāksnes Ø18 × 1,6 mm. Galvas augšā, uzgriežņi apakšā. Pievelk pakāpeniski pa diagonāli."], "base02": ["0,2 mm kompensācijas gredzens", "Izvēlas vienu atbilstoši abu saspiesto marles paku kopējam biezumam. 0,2 mm ir fiziska detaļas dimensija, nevis zināms marles biezums."], "base04": ["0,4 mm kompensācijas gredzens", "Izvēlas vienu atbilstoši abu saspiesto marles paku kopējam biezumam. 0,4 mm ir fiziska detaļas dimensija, nevis zināms marles biezums."], "base06": ["0,6 mm kompensācijas gredzens", "Izvēlas vienu atbilstoši abu saspiesto marles paku kopējam biezumam. 0,6 mm ir fiziska detaļas dimensija, nevis zināms marles biezums."], "base08": ["0,8 mm kompensācijas gredzens", "Izvēlas vienu atbilstoši abu saspiesto marles paku kopējam biezumam. 0,8 mm ir fiziska detaļas dimensija, nevis zināms marles biezums."]};
let renderer,scene,camera,controls,currentRoot,currentMode='assembly',progress=1,playing=false,lastTime=0,animationFrame=0,requestId=0;
let meshes=[],motionTargets=[],selected=null;
let highlighted=[];
const cache=new Map();
const loader=new GLTFLoader();
const raycaster=new THREE.Raycaster();
const pointer=new THREE.Vector2();
let pointerStart=null;

function groupFor(mesh,mode){
 let ancestor=mesh;while(ancestor){if(ancestor.userData.part)return ancestor.userData.part;ancestor=ancestor.parent;}
 if(mode==='grid')return 'lowerPetg';
 const name=mesh.name.toLowerCase();
 if(name.includes('compensation'))return 'base';
 if(name.includes('shim_0'))return 'shim05';
 if(name.includes('shim_1.5'))return 'shim15';
 if(name.includes('shim_1.0'))return 'shim10';
 return 'lowerPetg';
}
function isAssembly(){return currentMode==='assembly';}

function setPart(mesh){
 for(const previous of highlighted)previous.material.emissive?.setHex(0);
 highlighted=[];
 selected=mesh;
 document.querySelectorAll('[data-part]').forEach(button=>button.classList.toggle('selected',mesh?.userData.viewerPart===button.dataset.part));
 if(!mesh){partTitle.textContent='Izvēlies detaļu';partText.textContent='Pieskaries detaļai modelī vai izvēlies to sarakstā, lai apskatītu izmērus un pielietojumu.';render();return;}
 let desc=description[mesh.userData.viewerPart];

 partTitle.textContent=desc?.[0]??'Detaļa';partText.textContent=desc?.[1]??'';
 highlighted=meshes.filter(part=>part.userData.viewerPart===mesh.userData.viewerPart);
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

function explodedOffset(node){
 const layer={lowerPetg:0,lowerGauze:.020,base:.031,shim05:.043,shim10:.055,shim15:.067,pulp:.082,upperGauze:.099,upperPetg:.120};
 if(node.userData.viewerPart!=='hardware')return layer[node.userData.viewerPart]??0;
 const name=node.name.toLowerCase();
 return name.includes('nut')||name.includes('lower')?-.020:.145;
}
function assemblyStage(t){
 if(t>=.999)return 'Forma salikta · četrus uzgriežņus pievelk pakāpeniski pa diagonāli';
 if(t<.23)return '1 / 4 · apakšējā plāksne un marle';
 if(t<.55)return '2 / 4 · izvēlētā kompensācija un papildu starplikas';
 if(t<.78)return '3 / 4 · masa, augšējā marle un vāks';
 return '4 / 4 · četras skrūves, paplāksnes un uzgriežņi';
}

function closeFraction(part,t){
 const ranges={lowerGauze:[0,.23],base:[.13,.34],shim05:[.20,.41],shim10:[.27,.48],shim15:[.34,.55],pulp:[.45,.64],upperGauze:[.54,.72],upperPetg:[.60,.78],hardware:[.75,1]};
 const range=ranges[part]??[0,1];const u=THREE.MathUtils.clamp((t-range[0])/(range[1]-range[0]),0,1);
 return u*u*(3-2*u);
}

function setAssembly(value){
 progress=THREE.MathUtils.clamp(value,0,1);

 if(isAssembly())for(const mesh of motionTargets){
  mesh.position.copy(mesh.userData.rest);mesh.quaternion.copy(mesh.userData.restRotation);mesh.visible=true;
  mesh.position.y+=explodedOffset(mesh)*(1-closeFraction(mesh.userData.viewerPart,progress));
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
   model.traverse(node=>{if(node.userData.part){node.userData.rest=node.position.clone();node.userData.restRotation=node.quaternion.clone();node.userData.viewerPart=node.userData.part;}if(node.isMesh){node.material=node.material.clone();node.userData.viewerPart=groupFor(node,mode);node.material.side=THREE.DoubleSide;}});
   cache.set(mode,model);
  }
  if(id!==requestId)return;
  if(currentRoot)scene.remove(currentRoot);currentRoot=model;currentMode=mode;scene.add(model);meshes=[];
  motionTargets=[];model.traverse(node=>{if(node.isMesh)meshes.push(node);if(node.userData.part){let parent=node.parent;let nested=false;while(parent&&parent!==model){if(parent.userData.part)nested=true;parent=parent.parent;}if(!nested)motionTargets.push(node);}});
  setPart(null);document.querySelector('#assembly-controls').hidden=!isAssembly();document.querySelector('#part-buttons').hidden=!isAssembly();
  setAssembly(1);frame();status.hidden=true;
  document.querySelector('#model-label').textContent={assembly:'Forma · 3 mm mitrās spraugas piemērs',grid:'345 šūnu režģis un marle · plāksne 10 mm',shims:'4 kompensācijas varianti + 0,5 / 1 / 1,5 mm papildgredzeni'}[mode];
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
 document.querySelectorAll('[data-part]').forEach(button=>button.addEventListener('click',()=>setPart(meshes.find(mesh=>mesh.userData.viewerPart===button.dataset.part))));
 document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
 window.__LAPS_VIEWER={get state(){return {mode:currentMode,progress,playing,meshes:meshes.length,parts:motionTargets.length,topBounds:(()=>{const obj=motionTargets.find(o=>o.userData.part==='upperPetg');if(!obj)return null;const b=new THREE.Box3().setFromObject(obj);return [b.min.toArray(),b.max.toArray()];})(),roles:[...new Set(meshes.map(m=>m.userData.viewerPart))],selected:selected?.userData.viewerPart};}};
 resize();loadMode('assembly');
}catch(error){
 status.textContent='Šajā ierīcē 3D apskate nav pieejama. Modeļus vari lejupielādēt Blender vai iPhone AR skatam.';console.error(error);
 document.querySelectorAll('#viewer-panel button,#viewer-panel input,#viewer-panel select').forEach(control=>control.disabled=true);
}

async function initDocuments(){
 const tabs=document.querySelector('#document-tabs');const select=document.querySelector('#document-choice');const pageImage=document.querySelector('#document-image');
 try{
  const response=await fetch('/laps-siets/documents/catalog.json');if(!response.ok)throw new Error('catalog');const docs=await response.json();
  let docIndex=0,pageIndex=0;
  function paint(){
   const doc=docs[docIndex],page=doc.pages[pageIndex];
   pageImage.src=page.image;pageImage.alt=`${doc.title}, ${pageIndex+1}. lapa — ${page.title}`;
   document.querySelector('#document-title').textContent=doc.title;
   document.querySelector('#page-title').textContent=page.title;
   document.querySelector('#page-count').textContent=`${pageIndex+1} / ${doc.pages.length}`;
   document.querySelector('#document-pdf').href=doc.pdf;
   document.querySelector('#document-fullpage').href=page.image;
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
