import {build} from 'esbuild';
await Promise.all([build({entryPoints:['src/viewer.js'],bundle:true,format:'esm',minify:true,outfile:'dist/assets/app.js'}),build({entryPoints:['src/marle-viewer.js'],bundle:true,format:'esm',minify:true,outfile:'dist/laps-siets/marle.js'}),build({entryPoints:['src/pot-viewer.js'],bundle:true,format:'esm',minify:true,outfile:'dist/podins/podins.js'})]);
console.log('Built current, pot and archival LAPS viewers.');
