"""Authenticated NASA DAP4 subsets, resumable, six concurrent requests, no secrets saved."""
from pathlib import Path
import requests,json,datetime,concurrent.futures,hashlib,time
R=Path(__file__).resolve().parents[1]; O=R/'data/raw/pesquisa_chuva/imerg'; O.mkdir(exist_ok=True)
token=next(l.split('=',1)[1].strip().strip('\"').strip("'") for l in (R/'.env').read_text().splitlines() if l.startswith('EARTHDATA_TOKEN='))
BASE='https://opendap.earthdata.nasa.gov/collections/C2723754864-GES_DISC/granules/'
CE=';'.join(v+'[0:1:0][1290:1:1290][722:1:722]' for v in ['precipitation','precipitation_cnt','randomError'])+';lat[722:1:722];lon[1290:1:1290];time'
def get(d):
 name=f'3B-DAY.MS.MRG.3IMERG.{d:%Y%m%d}-S000000-E235959.V07B.nc4';p=O/f'{d:%Y%m%d}.nc4'
 if p.exists():return True
 url=BASE+'GPM_3IMERGDF.07%3A'+name+'.dap.nc4'
 for attempt in range(3):
  try:
   r=requests.get(url,params={'dap4.ce':CE},headers={'Authorization':'Bearer '+token},timeout=50)
   if r.status_code==200 and r.content.startswith(b'\x89HDF'):
    p.write_bytes(r.content);p.with_suffix('.meta.json').write_text(json.dumps({'url':url,'constraint':CE,'obtido_em':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(r.content).hexdigest()}));return True
   status=r.status_code
   if status in [401,403,404]:break
  except requests.RequestException as e:status=type(e).__name__
 p.with_suffix('.error.json').write_text(json.dumps({'url':url,'status':status}));return False
# Jan-Jun across all seven local station years; context Jul-Dec in 2025 only.
dates=[]
for y in [2025,2022,2008,2012,2016,2019,2024]:
 d=datetime.date(y,1,1); end=datetime.date(y,9,30) if y==2025 else datetime.date(y,6,30)
 while d<=end:dates.append(d);d+=datetime.timedelta(days=1)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 ok=0
 for i,result in enumerate(pool.map(get,dates),1):
  ok+=result
  if i%50==0:print(f'{i}/{len(dates)} completed, {ok} cached',flush=True)
print(f'DONE {ok}/{len(dates)}',flush=True)

# Keep a global reference file for an independent subset verification.
parent=O.parent
reference=parent/'imerg_20250101.nc4'
g=json.loads((parent/'imerg_granules.json').read_text())['feed']['entry'][0]
u=next(x['href'] for x in g['links'] if x['href'].startswith('https://data.gesdisc.earthdata.nasa.gov/data/'))
if not reference.exists():
 r=requests.get(u,headers={'Authorization':'Bearer '+token},timeout=90);r.raise_for_status()
 assert r.content.startswith(b'\x89HDF')
 reference.write_bytes(r.content)
reference.with_suffix('.nc4.meta.json').write_text(json.dumps({'url':u,'obtido_em_aproximado_file_mtime':datetime.datetime.fromtimestamp(reference.stat().st_mtime,datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(reference.read_bytes()).hexdigest()}))
subset=parent/'imerg_subset_test.nc4'
if not subset.exists():subset.write_bytes((O/'20250101.nc4').read_bytes())
subset.with_suffix('.nc4.meta.json').write_text(json.dumps({'url':BASE+'GPM_3IMERGDF.07%3A3B-DAY.MS.MRG.3IMERG.20250101-S000000-E235959.V07B.nc4.dap.nc4','constraint':CE,'obtido_em_aproximado_file_mtime':datetime.datetime.fromtimestamp(subset.stat().st_mtime,datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(subset.read_bytes()).hexdigest()}))
