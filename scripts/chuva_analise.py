"""Daily rainfall audit. Offline run: python scripts/chuva_analise.py."""
from pathlib import Path
import json, hashlib, calendar, math, os
os.environ.setdefault('MPLCONFIGDIR','/tmp/nasa26-matplotlib')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; O=R/'data/processed/pesquisa_chuva'; F=R/'docs/pesquisa_chuva'
O.mkdir(parents=True,exist_ok=True); F.mkdir(parents=True,exist_ok=True)
YEARS=[2008,2012,2016,2019,2022,2024,2025]
def save(df,name): df.to_csv(O/(name+'.csv'),index=False,float_format='%.6f')
parts=[]; audits=[]; inputs=[]
for y in YEARS:
 p=next((R/'data/raw/conferencia').glob(f'*01-01-{y}*.CSV')); inputs.append(p)
 a=pd.read_csv(p,sep=';',encoding='latin1',skiprows=8,dtype=str)
 t=pd.to_datetime(a.iloc[:,0].str.replace('/','-')+' '+a.iloc[:,1].str.replace(':','',regex=False).str[:4],format='%Y-%m-%d %H%M')
 v=pd.to_numeric(a.iloc[:,2].str.replace(',','.'),errors='coerce')
 assert pd.DatetimeIndex(t).equals(pd.date_range(f'{y}-01-01',f'{y+1}-01-01',freq='h',inclusive='left')), f'Unexpected hourly grid: {p}'
 duplicates=int(t.duplicated().sum()); assert duplicates==0, f'Duplicate hours: {p}'
 audits.append(dict(year=y,rows=len(a),expected_hours=(366 if calendar.isleap(y) else 365)*24,missing_hours=int(v.isna().sum()),negative_fill_hours=int((v<0).sum()),duplicate_hours=duplicates,above_100mm_hours=int((v>100).sum()),max_hour_mm=v.max()))
 parts.append(pd.Series(v.mask(v<0).to_numpy(),index=t))
h=pd.concat(parts).sort_index(); assert h.index.is_unique
# INMET values are preceding-hour accumulations. Shift ending stamp back 1 hour.
# Main day 00:00--24:00 UTC therefore contains stamps 01:00--next 00:00.
def daily(offset):
 z=h.copy(); z.index=z.index-pd.Timedelta(hours=offset)
 g=z.resample('D'); out=pd.DataFrame({'hours':g.count(),'inmet':g.sum(min_count=24)})
 return out
base=daily(1); label=daily(0)
p=R/'data/raw/pesquisa_chuva/power_station_utc_2008_2025.json'; inputs.append(p); j=json.loads(p.read_text())
assert j['header']['time_standard']=='UTC'; assert j['parameters']['PRECTOTCORR']['units']=='mm/day'
power=pd.Series(j['properties']['parameter']['PRECTOTCORR'],dtype=float); power.index=pd.to_datetime(power.index,format='%Y%m%d'); assert power.index.is_unique
power=power.mask(power<0); base['power']=power; base['inmet_label_utc']=label.inmet
base=base[base.index.year.isin(YEARS)].copy(); base.index.name='date'; base['paired']=base[['inmet','power']].notna().all(axis=1)
old=json.loads((R/'data/raw/pesquisa_chuva/power_utc_2008_2025.json').read_text())['properties']['parameter']['PRECTOTCORR']
old=pd.Series(old,dtype=float); old.index=pd.to_datetime(old.index,format='%Y%m%d'); base['power_original_point']=old.mask(old<0)
base['year']=base.index.year; base['month']=base.index.month
base['epoch']=pd.cut(base.month,[0,2,4,6,12],labels=['Jan-Feb','Mar-Apr','May-Jun','Jul-Dec']).astype(str)
# 95% permits reporting paired sums, NEVER completion or gap filling.
month=[]
for (y,m),a in base.groupby(['year','month']):
 b=a[a.paired]; n=len(b); expected=calendar.monthrange(y,m)[1]
 month.append(dict(year=y,month=m,expected_days=expected,paired_days=n,excluded_days=expected-n,coverage=n/expected,accepted=n/expected>=.95,inmet_paired_mm=b.inmet.sum() if n else np.nan,power_paired_mm=b.power.sum() if n else np.nan,inmet_complete_mm=b.inmet.sum() if n==expected else np.nan,power_complete_mm=a.power.sum() if a.power.count()==expected else np.nan))
months=pd.DataFrame(month); save(months,'monthly')
def metrics(a,pcol='power'):
 b=a[['inmet',pcol]].dropna(); obs=b.inmet; pred=b[pcol]; d=pred-obs
 return dict(n=len(b),inmet_paired_mm=obs.sum(),power_paired_mm=pred.sum(),bias_mm_day=d.mean(),bias_percent=100*d.sum()/obs.sum() if obs.sum() else np.nan,mae_mm_day=d.abs().mean(),rmse_mm_day=np.sqrt((d*d).mean()),correlation=obs.corr(pred) if len(b)>2 and obs.std()>0 and pred.std()>0 else np.nan,inmet_wet_percent=100*(obs>=1).mean(),power_wet_percent=100*(pred>=1).mean())
rows=[]
for y,a in base.groupby('year'):
 for scope,b in [('year',a),('Jan-Jun',a[a.month<=6])]:
  rows.append(dict(year=y,scope=scope,expected_days=len(b),excluded_days=int((~b.paired).sum()),coverage=b.paired.mean(),complete=bool(b.paired.all()),**metrics(b)))
annual=pd.DataFrame(rows); save(annual,'annual_seasonal')
save(pd.DataFrame([dict(year=y,epoch=e,**metrics(a)) for (y,e),a in base.groupby(['year','epoch'])]),'epochs')
# Contiguous observed dry runs only; missing records split runs, with censor flags.
runs=[]
for y,a in base.groupby('year'):
 for src in ['inmet','power']:
  valid=a.paired; dry=(a[src]<1)&valid; start=None
  for i in range(len(a)+1):
   active=i<len(a) and bool(dry.iloc[i])
   if active and start is None: start=i
   if not active and start is not None:
    runs.append(dict(year=y,source=src,start=a.index[start],end=a.index[i-1],days=i-start,left_censored=start==0 or not bool(valid.iloc[start-1]),right_censored=i==len(a) or not bool(valid.iloc[i]),start_month=a.index[start].month))
    start=None
runs=pd.DataFrame(runs); save(runs,'dry_runs')
# Monthly factors, older years for fit, later years untouched evaluation.
train_years=[2008,2012,2016,2019]; test_years=[2022,2024,2025]
factors=[]
for m in range(1,13):
 eligible=months[(months.month==m)&months.year.isin(train_years)&months.accepted]
 a=base[(base.month==m)&base.year.isin(eligible.year)&base.paired]
 f=a.inmet.sum()/a.power.sum() if len(eligible)>=3 and a.power.sum()>0 else np.nan
 factors.append(dict(month=m,training_years=';'.join(map(str,eligible.year)),n_months=len(eligible),n_days=len(a),factor=f))
factors=pd.DataFrame(factors); save(factors,'correction_factors'); base['power_corrected']=base.power*base.month.map(factors.set_index('month').factor)
evalrows=[]
for y in test_years+['ALL']:
 a=base[base.year.isin(test_years) if y=='ALL' else base.year==y]
 for scope in ['year','Jan-Jun']:
  b=a if scope=='year' else a[a.month<=6]
  # Exactly same days for original and corrected, only accepted validation months.
  eligible=set(map(tuple,months[months.accepted][['year','month']].to_numpy()))
  b=b[[ (int(z.year),int(z.month)) in eligible for z in b.itertuples()]].dropna(subset=['inmet','power','power_corrected'])
  for src in ['power','power_corrected']: evalrows.append(dict(year=y,scope=scope,source=src,**metrics(b,src)))
evaluation=pd.DataFrame(evalrows); save(evaluation,'correction_evaluation')
sens=[]
variants={off:daily(off).inmet.reindex(base.index) for off in [0,1]}
common=variants[0].notna()&variants[1].notna()&base.power.notna()
for off in [0,1]:
 a=base.loc[common,['power']].copy(); a['inmet']=variants[off][common]
 sens.append(dict(inmet_timestamp_shift_hours=off,**metrics(a)))
save(pd.DataFrame([dict(year=y,scope=scope,**metrics(b,'power_original_point')) for y,a in base.groupby('year') for scope,b in [('year',a),('Jan-Jun',a[a.month<=6])]]),'original_point_comparison');
save(pd.DataFrame(sens),'time_sensitivity'); save(pd.DataFrame(audits),'hourly_audit'); save(base.reset_index(),'daily')
summary={'all':metrics(base),'jan_jun':metrics(base[base.month<=6]),'n_days':len(base),'excluded_days':int((~base.paired).sum()),'accepted_months_95pct':int(months.accepted.sum()),'complete_months':int((months.coverage==1).sum()),'inmet_negative_after_cleaning':int((base.inmet<0).sum()),'power_missing_days':int(base.power.isna().sum()),'train_years':train_years,'test_years':test_years,'model_present':False}
(O/'summary.json').write_text(json.dumps(summary,indent=2))
# Provenance of all numerical inputs. Existing download dates remain in source metadata.
(O/'inputs.json').write_text(json.dumps([{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs],indent=2))
plt.rcParams.update({'font.size':9})
fig,axes=plt.subplots(7,1,figsize=(11,16),sharex=True)
for ax,(y,a) in zip(axes,months.groupby('year')):
 ax.plot(a.month,a.inmet_paired_mm,'o-',label='INMET'); ax.plot(a.month,a.power_paired_mm,'s-',label='POWER UTC'); ax.set_ylabel(f'{y}\nmm'); ax.grid(alpha=.2)
 for row in a.itertuples():
  if not row.accepted: ax.axvspan(row.month-.3,row.month+.3,color='red',alpha=.12)
axes[0].legend(); axes[-1].set_xticks(range(1,13)); axes[-1].set_xlabel('Month; red shade: <95% paired days'); fig.suptitle('Monthly sums on paired dates only'); fig.tight_layout(); fig.savefig(F/'monthly.png',dpi=150); plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(12,4)); jan=annual[annual.scope=='Jan-Jun']; axes[0].bar(jan.year.astype(str),jan.power_paired_mm-jan.inmet_paired_mm); axes[0].set_ylabel('POWER minus INMET, mm'); axes[0].set_title('January–June: paired dates');
for src in ['inmet','power']:
 r=runs[runs.source==src].groupby('year').days.max(); axes[1].plot(r.index.astype(str),r.values,'o-',label=src)
axes[1].set_title('Longest observed dry run (<1 mm/day)'); axes[1].set_ylabel('Days; gaps split runs'); axes[1].legend(); fig.tight_layout(); fig.savefig(F/'differences_dry_runs.png',dpi=150);plt.close(fig)
a=months[months.year==2025];fig,ax=plt.subplots(figsize=(10,4));ax.bar(a.month-.18,a.inmet_paired_mm,.36,label='INMET');ax.bar(a.month+.18,a.power_paired_mm,.36,label='POWER');ax.set(xticks=range(1,13),ylabel='mm',title='2025: monthly sums on paired dates');ax.legend();fig.tight_layout();fig.savefig(F/'2025.png',dpi=150);plt.close(fig)
# Arithmetic and missing-data invariants.
assert base.loc[base.hours<24,'inmet'].isna().all()
assert len(base)==sum(366 if calendar.isleap(y) else 365 for y in YEARS)
assert np.isclose(months.inmet_paired_mm.sum(),base.loc[base.paired,'inmet'].sum())
assert np.isclose(months.power_paired_mm.sum(),base.loc[base.paired,'power'].sum())
assert not set(train_years)&set(test_years)
assert (factors.factor.dropna()>0).all()
assert summary['power_missing_days']==0
print(json.dumps(summary,indent=2)); print(annual.to_string(index=False)); print(evaluation.to_string(index=False)); print('PASS: dates, units, missing data, sums, disjoint split')
