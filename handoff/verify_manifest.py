"""Verify the extracted handoff payload against its SHA-256 manifest."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
manifest=json.loads((root/'handoff/FILE_MANIFEST.json').read_text())
failures=[]
for item in manifest['files']:
 p=root/item['path']
 if not p.is_file():failures.append('Missing: '+item['path']);continue
 if p.stat().st_size!=item['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:failures.append('Changed: '+item['path'])
if failures:
 print('\n'.join(failures));sys.exit(1)
print('PASS: '+str(len(manifest['files']))+' files match the export manifest.')
