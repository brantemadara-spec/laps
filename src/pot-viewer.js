import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const host=document.querySelector('#pot-model-canvas');
const status=document.querySelector('#pot-model-status');
const choose=document.querySelector('#pot-part');
const partText=document.querySelector('#pot-part-description');
const descriptions={
 all:'V4.1 detaļu katalogs: 9 formas detaļas, tostarp trīs maināmi serdeņi 3 / 4 / 5 mm sienām. Vienlaikus izmanto vienu serdeni.',
 '01_MOLD_LEFT':'Kreisā formas puse ar 45° austiņu balstiem un slīpiem M6 atveru jumtiņiem. Sānu skrūvju asis Z34 / Z54 mm; paplāksnēm paredzētas plakanas balsta vietas.',
 '02_MOLD_RIGHT':'Labā ārējās formas puse ar Ø5,6 mm tapu ligzdām. Nominālā diametru starpība 0,6 mm jeb 0,3 mm radiāli; V4.1 austiņu dalījuma plaknes savietotas bez agrākās 1 mm pārklāšanās. M6 ligzdām saglabāta Ø6,8 mm apaļā brīvtelpa.',
 '03_OVERFLOW_COLLAR':'Pārplūdes kamera: Ø124 / Ø102 mm, augstums 12 mm, apakšējā centrēšanas mala 3 mm. Šim tīklam atrastas 12 neslēgtas robežmalas; nepieciešams labojums.',
 '04_CORE_3MM':'Maināmais serdenis 3 mm nominālai radiālai sienai. STOP Ø118 × 6 mm; faktisko sienas spraugu skatīt pārbaužu tabulā.',
 '05_CORE_4MM':'Maināmais serdenis 4 mm nominālai radiālai sienai. Ar Ø32 × 10 mm augšējo spiediena balstu. Vienā salikumā izmanto vienu serdeni.',
 '06_CORE_5MM':'Maināmais serdenis 5 mm nominālai radiālai sienai. Dobuma 72 mm koniskā griezuma dēļ faktiskais biezums nedaudz mainās ar augstumu; skatīt pārbaudes.',
 '07_BASE':'Ø150 × 10 mm drenāžas pamatne ar 15 Ø5 mm atverēm, formas gredzenveida ligzdu un atsevišķu sietiņa ligzdu. Salikuma augstuma atskaites vēl jāprecizē.',
 '08_SIEVE':'Ø62 × 1,4 mm perforētais ieliktnis ar 19 Ø2,6 mm caurumiem. Metāla M6/M12 stiprinājumi šajā modelī nav drukājamās detaļas.',
 '09_TOP_PLATE':'Ø150 × 10 mm augšējā plāksne ar Ø13,5 mm centrālo M12 caurumu, sešstūra uzgriežņa ligzdu un četriem Ø6,8 mm M6 vītņstieņu caurumiem.'
};
const previewColors={'04_CORE_3MM':0x729849,'05_CORE_4MM':0x277d78,'06_CORE_5MM':0x527aab,'03_OVERFLOW_COLLAR':0xcaa66b};
let renderer,scene,camera,controls,root;
const objects=[];
function render(){renderer?.render(scene,camera);}
function resize(){if(!renderer)return;const {width,height}=host.getBoundingClientRect();renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();render();}
function frame(){
 if(!root)return;
 const selected=choose.value==='all'?root:objects.find(obj=>obj.name===choose.value);
 const box=new THREE.Box3().setFromObject(selected||root);
 const center=box.getCenter(new THREE.Vector3());const radius=box.getSize(new THREE.Vector3()).length()/2;
 controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(1,1.35,1.3).normalize().multiplyScalar(radius*(choose.value==='all'?2.8:2.4)));
 camera.near=Math.max(radius/100,.0001);camera.far=Math.max(radius*50,10);camera.updateProjectionMatrix();controls.minDistance=radius*.6;controls.maxDistance=radius*8;controls.update();render();
}
function showPart(){
 for(const obj of objects)obj.visible=choose.value==='all'||obj.name===choose.value;
 partText.textContent=descriptions[choose.value]||descriptions.all;frame();
}
async function initViewer(){
try{
 renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'default'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setClearColor(0xf2f6f6);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;
 renderer.domElement.setAttribute('aria-label','Podiņa formas detaļu interaktīvs modelis');renderer.domElement.setAttribute('role','img');host.appendChild(renderer.domElement);
 scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(38,1,.001,10);
 const pmrem=new THREE.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(new RoomEnvironment(),.04).texture;pmrem.dispose();
 scene.add(new THREE.HemisphereLight(0xffffff,0xb6c6c2,1.5));const sun=new THREE.DirectionalLight(0xffffff,2);sun.position.set(.4,.8,.5);scene.add(sun);
 controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=false;controls.addEventListener('change',render);new ResizeObserver(resize).observe(host);
 choose.addEventListener('change',showPart);document.querySelector('#pot-reset').addEventListener('click',frame);
 const gltf=await new GLTFLoader().loadAsync('/podins/models/podins.glb?v=41-ears45-20261026');root=gltf.scene;
 root.traverse(obj=>{if(obj.isMesh){obj.name=obj.name.replace(/_WEB$/,'');obj.material=obj.material.clone();obj.material.color.setHex(previewColors[obj.name]??0x497a60);objects.push(obj);}});scene.add(root);showPart();resize();status.hidden=true;host.dataset.ready='true';choose.disabled=false;
 window.__POT_VIEWER={get state(){const box=new THREE.Box3().setFromObject(root);return {ready:true,version:'V4.1',selected:choose.value,objects:objects.map(obj=>({name:obj.name,visible:obj.visible})),bounds:box.getSize(new THREE.Vector3()).toArray()};}};
}catch(error){status.textContent='3D apskati neizdevās ielādēt. Blender un GLB failus vari lejupielādēt zemāk.';choose.disabled=true;document.querySelector('#pot-reset').disabled=true;console.error(error);}
}
initViewer();

const copyButton=document.querySelector('#copy-pot-code');
copyButton.addEventListener('click',async()=>{
 const text=document.querySelector('#pot-code').textContent;
 try{await navigator.clipboard.writeText(text);document.querySelector('#copy-status').textContent='Kods nokopēts. Blenderī atver jaunu ainu un ielīmē to Text Editor.';}
 catch{
  document.querySelector('#pot-code-details').open=true;
  const selection=getSelection(),range=document.createRange();range.selectNodeContents(document.querySelector('#pot-code'));selection.removeAllRanges();selection.addRange(range);
  document.querySelector('#copy-status').textContent='Kods atlasīts. Nokopē to ar Ctrl+C vai ierīces kopēšanas izvēlni.';
 }
});
