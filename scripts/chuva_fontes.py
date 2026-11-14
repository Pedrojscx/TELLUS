"""Fetch public source records; cache bodies; never persist authentication material."""
from pathlib import Path
import requests, json, datetime, hashlib, re
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data/raw/pesquisa_chuva'; OUT.mkdir(exist_ok=True,parents=True)
def fetch(name,url,params=None):
 p=OUT/name
 if p.exists(): return json.loads(p.read_text()) if name.endswith('.json') else p.read_text()
 r=requests.get(url,params=params,timeout=90,headers={'User-Agent':'nasa26-research/1.0'}); r.raise_for_status(); p.write_bytes(r.content)
 (OUT/(name+'.meta.json')).write_text(json.dumps({'url':r.url,'obtido_em':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(r.content).hexdigest(),'status':r.status_code},indent=2))
 return r.json() if name.endswith('.json') else r.text
fetch('power_utc_2008_2025.json','https://power.larc.nasa.gov/api/temporal/daily/point',dict(parameters='PRECTOTCORR',community='AG',longitude=-50.92,latitude=-17.80,start=20080101,end=20251231,format='JSON',**{'time-standard':'UTC'}))
urls={
 'power_daily.html':'https://power.larc.nasa.gov/docs/services/api/temporal/daily/',
 'inmet_historicos.html':'https://portal.inmet.gov.br/dadoshistoricos',
 'imerg_technical.html':'https://gpm.nasa.gov/data/imerg',
 'gesdisc_access.html':'https://disc.gsfc.nasa.gov/data-access',
}
for name,url in urls.items():
 try: fetch(name,url); print(name,'cached')
 except Exception as e: print(name,type(e).__name__)
c=fetch('imerg_collections.json','https://cmr.earthdata.nasa.gov/search/collections.json',{'short_name':'GPM_3IMERGDF','version':'07','page_size':10})
entries=c['feed']['entry']; print('collections',[(e['id'],e['title']) for e in entries])
if entries:
 cid=entries[0]['id']; g=fetch('imerg_granules.json','https://cmr.earthdata.nasa.gov/search/granules.json',{'collection_concept_id':cid,'temporal':'2025-01-01T00:00:00Z,2025-01-01T23:59:59Z','page_size':1})
 links=g['feed']['entry'][0]['links']; print('links',[(l.get('rel'),l['href']) for l in links])
# Same station point and native-grid checks; older project point crosses a cell edge.
for name,lat,lon,start,end in [('power_station_utc_2008_2025.json',-17.78527777,-50.965,20080101,20251231),('power_center_west.json',-18,-51.25,20250101,20250131),('power_center_east.json',-18,-50.625,20250101,20250131)]:
 fetch(name,'https://power.larc.nasa.gov/api/temporal/daily/point',dict(parameters='PRECTOTCORR',community='AG',longitude=lon,latitude=lat,start=start,end=end,format='JSON',**{'time-standard':'UTC'}))
fetch('power_meteorology_current.html','https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/')
fetch('power_services.html','https://power.larc.nasa.gov/docs/services/')
fetch('inmet_glossario.html','https://portal.inmet.gov.br/glossario/tempo')
