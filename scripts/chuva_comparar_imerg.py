"""Compare cached NASA daily cell extracts with QC station days. No network."""
from pathlib import Path
import json,hashlib,math,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/nasa26-matplotlib')
import netCDF4,numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; O=R/'data/processed/pesquisa_chuva';F=R/'docs/pesquisa_chuva';D=R/'data/raw/pesquisa_chuva'
def save(a,n):a.to_csv(O/(n+'.csv'),index=False,float_format='%.6f')
rows=[];meta=[]
for p in sorted((D/'imerg').glob('*.nc4')):
 with netCDF4.Dataset(p) as f:
  assert f.variables['precipitation'].units=='mm/day'
  assert f.BeginTime=='00:00:00.000Z' and f.EndTime=='23:59:59.999Z'
  assert f.BeginDate==pd.to_datetime(p.stem).strftime('%Y-%m-%d')
  def val(k):
   v=f.variables[k][:].reshape(-1)[0];return np.nan if np.ma.is_masked(v) else float(v)
  row=dict(date=f.BeginDate,imerg_raw=val('precipitation'),imerg_count=val('precipitation_cnt'),imerg_random_error=val('randomError'),lat=val('lat'),lon=val('lon'))
  row['imerg']=row['imerg_raw'] if row['imerg_count']==48 and row['imerg_raw']>=0 else np.nan
  rows.append(row);meta.append(dict(file=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
a=pd.DataFrame(rows);assert not a.date.duplicated().any();save(a,'imerg_daily');(O/'imerg_inputs.json').write_text(json.dumps(meta,indent=2))
b=pd.read_csv(O/'daily.csv'); b=b.merge(a,on='date',how='left',validate='one_to_one');b['date']=pd.to_datetime(b.date);save(b,'daily_all_sources')
def stats(a,src):
 d=a[src]-a.inmet
 return dict(n=len(a),inmet_mm=a.inmet.sum() if len(a) else np.nan,source_mm=a[src].sum() if len(a) else np.nan,bias_mm_day=d.mean(),bias_percent=100*d.sum()/a.inmet.sum() if a.inmet.sum() else np.nan,mae_mm_day=d.abs().mean(),rmse_mm_day=np.sqrt((d*d).mean()),correlation=a.inmet.corr(a[src]) if len(a)>2 and a.inmet.std()>0 and a[src].std()>0 else np.nan,inmet_wet_percent=100*(a.inmet>=1).mean(),source_wet_percent=100*(a[src]>=1).mean())
metrics=[]; monthly=[];dry=[]
for scope,sel in [('Jan-Jun',b.month<=6),('available_context',b.month>6)]:
 c=b[sel].copy();c['triple_valid']=c[['inmet','power','imerg']].notna().all(axis=1)
 for y in sorted(c.year.unique())+['ALL']:
  z=c if y=='ALL' else c[c.year==y];v=z[z.triple_valid]
  for src in ['power','imerg']:
   metrics.append(dict(scope=scope,year=y,source=src,expected_days=len(z),excluded_days=len(z)-len(v),**stats(v,src)))
 for (y,m),z in c.groupby(['year','month']):
  v=z[z.triple_valid];n=len(v)
  monthly.append(dict(year=y,month=m,n=n,expected_days=len(z),coverage=n/len(z),accepted=n/len(z)>=.95,complete=n==len(z),inmet_mm=v.inmet.sum() if n else np.nan,power_mm=v.power.sum() if n else np.nan,imerg_mm=v.imerg.sum() if n else np.nan))
 # Runs cannot cross gaps or season boundaries; exact strings for audit.
 for y,z in c.groupby('year'):
  for src in ['inmet','power','imerg']:
   for threshold in [.1,1.,5.]:
    valid=z.triple_valid.to_numpy(); ds=(z[src]<threshold).to_numpy()&valid;start=None;lengths=[];bounded=[]
    for i in range(len(z)+1):
     active=i<len(z) and ds[i]
     if active and start is None:start=i
     if not active and start is not None:
      length=i-start;left=start==0 or not valid[start-1];right=i==len(z) or not valid[i]
      lengths.append(length)
      if not left and not right:bounded.append(length)
      start=None
    dry.append(dict(year=y,scope=scope,source=src,threshold_mm=threshold,n_valid=int(valid.sum()),wet_days=int(((z[src]>=threshold)&z.triple_valid).sum()),max_observed_run=max(lengths,default=0),max_bounded_run=max(bounded,default=0),n_runs=len(lengths),n_bounded_runs=len(bounded)))
epochs=[]
for (year,epoch),z in b.groupby(['year','epoch']):
 v=z.dropna(subset=['inmet','power','imerg'])
 for src in ['power','imerg']:epochs.append(dict(year=year,epoch=epoch,source=src,**stats(v,src)))
save(pd.DataFrame(epochs),'three_source_epochs')
metrics=pd.DataFrame(metrics);monthly=pd.DataFrame(monthly);save(metrics,'three_source_metrics');save(monthly,'three_source_monthly');save(pd.DataFrame(dry),'three_source_dry_summary')
# Monthly aggregate errors require high coverage; compare paired-date sums, not estimates of totals.
agg=[]
for scope,sel in [('Jan-Jun',monthly.month<=6),('all_available',monthly.month>0)]:
 z=monthly[sel&monthly.accepted]
 for src in ['power','imerg']:
  d=z[src+'_mm']-z.inmet_mm
  agg.append(dict(scope=scope,source=src,n_months=len(z),bias_mm_month=d.mean(),bias_percent=100*d.sum()/z.inmet_mm.sum(),mae_mm_month=d.abs().mean(),rmse_mm_month=np.sqrt((d*d).mean()),correlation=z.inmet_mm.corr(z[src+'_mm'])))
save(pd.DataFrame(agg),'monthly_aggregate_metrics')
seasonal=[]
for src in ['power','imerg']:
 z=metrics[(metrics.scope=='Jan-Jun')&(metrics.year!='ALL')&(metrics.source==src)].copy()
 z=z[z.n/z.expected_days>=.95]; delta=z.source_mm-z.inmet_mm
 seasonal.append(dict(source=src,n_seasons=len(z),years=';'.join(map(str,z.year)),bias_mm_season=delta.mean(),bias_percent=100*delta.sum()/z.inmet_mm.sum(),mae_mm_season=delta.abs().mean(),rmse_mm_season=np.sqrt((delta*delta).mean())))
save(pd.DataFrame(seasonal),'seasonal_aggregate_metrics')

fig,axes=plt.subplots(7,1,figsize=(11,16))
for ax,(y,z) in zip(axes,monthly.groupby('year')):
 for src in ['inmet','power','imerg']:ax.plot(z.month,z[src+'_mm'],'o-',label=src)
 for row in z.itertuples():
  if row.n and not row.accepted:ax.axvspan(row.month-.3,row.month+.3,color='red',alpha=.12)
 ax.set(xticks=range(1,13),ylabel=f'{y}\nmm');ax.grid(alpha=.2)
axes[0].legend();fig.suptitle('Monthly sums: identical valid dates, 3 sources');fig.tight_layout();fig.savefig(F/'three_sources_monthly.png',dpi=150);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(12,4))
z=metrics[(metrics.scope=='Jan-Jun')&(metrics.year!='ALL')]
for src in ['power','imerg']:
 v=z[z.source==src];axes[0].plot(v.year.astype(str),v.bias_percent,'o-',label=src)
d=pd.DataFrame(dry);d=d[(d.scope=='Jan-Jun')&(d.threshold_mm==1)]
for src in ['inmet','power','imerg']:
 v=d[d.source==src];axes[1].plot(v.year.astype(str),v.max_observed_run,'o-',label=src)
axes[0].set(ylabel='Bias (%)',title='January–June, identical valid dates');axes[1].set(ylabel='Days',title='Dry runs <1 mm/day; gaps split runs')
for ax in axes:ax.legend();ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(F/'three_sources_bias_dry.png',dpi=150);plt.close(fig)
# Day-by-day plot for 2025, January–June, showing outages rather than linking them.
z=b[(b.year==2025)&(b.month<=6)].set_index('date');fig,axes=plt.subplots(3,1,figsize=(12,7),sharex=True)
for ax,src in zip(axes,['inmet','power','imerg']):ax.bar(z.index,z[src],width=1);ax.set_ylabel(src+'\nmm/day');ax.grid(alpha=.2)
fig.suptitle('2025 daily precipitation, UTC');fig.tight_layout();fig.savefig(F/'2025_daily.png',dpi=150);plt.close(fig)
# Cell distances, haversine in km.
def distance(lat,lon):
 a1,a2=map(math.radians,[-17.78527777,lat]); da=a2-a1;dl=math.radians(lon+50.965)
 return 6371*2*math.asin(math.sqrt(math.sin(da/2)**2+math.cos(a1)*math.cos(a2)*math.sin(dl/2)**2))
cells={'station':{'lat':-17.78527777,'lon':-50.965,'altitude_m':780.11},'imerg':{'lat':float(a.lat.iloc[0]),'lon':float(a.lon.iloc[0]),'distance_km':distance(a.lat.iloc[0],a.lon.iloc[0]),'indices_zero_based':{'lon':1290,'lat':722}},'power_station_cell':{'lat':-18,'lon':-51.25,'distance_km':distance(-18,-51.25),'status':'January 2025 API values identical at station and this native-grid center'},'power_original_point_cell':{'lat':-18,'lon':-50.625,'distance_km':distance(-18,-50.625),'status':'January 2025 API values identical at original point and this native-grid center'},'original_query_distance_km':distance(-17.8,-50.92)}
for f,g in [('power_station_utc_2008_2025.json','power_center_west.json'),('power_utc_2008_2025.json','power_center_east.json')]:
 x=json.loads((D/f).read_text())['properties']['parameter']['PRECTOTCORR'];y=json.loads((D/g).read_text())['properties']['parameter']['PRECTOTCORR'];assert all(x[k]==v for k,v in y.items())
(O/'cells.json').write_text(json.dumps(cells,indent=2))
print(metrics[metrics.year=='ALL'].to_string(index=False));print('IMERG files',len(a),'rejected quality',int(a.imerg.isna().sum()),'count min/max',a.imerg_count.min(),a.imerg_count.max());print('PASS: NetCDF units, UTC bounds, dates, cell equality, uniqueness, quality counts')
