"""Independent spot checks from raw CSV/NetCDF, not processed intermediates."""
from pathlib import Path
import csv,datetime,math,json
import netCDF4
R=Path(__file__).resolve().parents[1]
p=next((R/'data/raw/conferencia').glob('*01-01-2025*.CSV'))
with p.open(encoding='latin1') as f:
 for _ in range(8):next(f)
 records=list(csv.reader(f,delimiter=';'))[1:]
hours={}
for r in records:
 t=datetime.datetime.strptime(r[0]+' '+r[1][:4],'%Y/%m/%d %H%M')
 try:v=float(r[2].replace(',','.'))
 except ValueError:v=None
 hours[t]=v if v is not None and v>=0 else None
with (R/'data/processed/pesquisa_chuva/daily.csv').open() as f:days={r['date']:r for r in csv.DictReader(f)}
for day in ['2025-01-01','2025-01-21','2025-04-12','2025-06-30']:
 d=datetime.datetime.fromisoformat(day);values=[hours.get(d+datetime.timedelta(hours=i)) for i in range(1,25)]
 if any(v is None for v in values):assert days[day]['inmet']=='',day
 else:assert math.isclose(sum(values),float(days[day]['inmet']),abs_tol=1e-6),day
with netCDF4.Dataset(R/'data/raw/pesquisa_chuva/imerg_20250101.nc4') as full,netCDF4.Dataset(R/'data/raw/pesquisa_chuva/imerg_subset_test.nc4') as sub:
 for variable in ['precipitation','precipitation_cnt','randomError']:
  assert math.isclose(float(full[variable][0,1290,722]),float(sub[variable][0,0,0]))
 assert full['precipitation'].units=='mm/day'
 assert full['precipitation_cnt'][0,1290,722]==48
print('PASS: 4 independent hourly sums/missing checks; full global IMERG vs cell subset; units and count')
