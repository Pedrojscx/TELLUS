"""Check official access with existing token; output status only, no secrets."""
from pathlib import Path
import json,datetime,requests
R=Path(__file__).resolve().parents[1]; O=R/'data/raw/pesquisa_chuva'
g=json.loads((O/'imerg_granules.json').read_text())['feed']['entry'][0]
token=None
p=R/'.env'
if p.exists():
 for line in p.read_text().splitlines():
  if line.startswith('EARTHDATA_TOKEN='): token=line.split('=',1)[1].strip().strip('\"').strip("'")
rows=[]
for link in g['links']:
 u=link['href']
 if not (u.startswith('https://data.gesdisc.earthdata.nasa.gov/data/') or u.startswith('https://opendap.earthdata.nasa.gov/collections/')): continue
 if 'opendap' in u: u+='.dds'
 try:
  r=requests.get(u,headers={'Authorization':'Bearer '+token} if token else {},timeout=40,stream=True)
  chunk=next(r.iter_content(4096),b''); eula=b'EULA' in chunk
  rows.append({'url':u,'status':r.status_code,'token_present':bool(token),'eula_failure':eula,'final_host':requests.utils.urlparse(r.url).hostname,'content_type':r.headers.get('Content-Type'),'obtido_em':datetime.datetime.now(datetime.timezone.utc).isoformat()});r.close()
 except requests.RequestException as e: rows.append({'url':u,'error_type':type(e).__name__})
(O/'imerg_access.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
