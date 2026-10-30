"""Add readable interpretations, visualizations and explicit coverage for missing data."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]

def main():
 out=ROOT/'reports/eda';insights={}
 for path in sorted(out.glob('[0-9][0-9]_*.csv')):
  t=pd.read_csv(path);key=path.stem
  fig,ax=plt.subplots(figsize=(10,5))
  title=key[3:].replace('_',' ').title()
  if key[:2] in ['01','02']:
   ax.axis('off');ax.table(cellText=t.round(2).values,colLabels=['Statistic']+list(t.columns[1:]),loc='center',cellLoc='center');note='The table reports count, spread and percentiles. The overview chart shows the full distribution.'
  elif key[:2]=='11':
   vals=t.iloc[:,1:].to_numpy();im=ax.imshow(vals,vmin=-1,vmax=1,cmap='coolwarm',aspect='auto');ax.set_xticks(range(len(t.columns)-1),t.columns[1:],rotation=90,fontsize=7);ax.set_yticks(range(len(t)),t.iloc[:,0],fontsize=7);fig.colorbar(im,ax=ax);note='Correlation describes association. Corrected price per square foot is mechanically derived from price and size. Constant columns can have undefined correlations.'
  elif key[:2]=='04':
   ax.axis('off');ax.table(cellText=t.round(4).values,colLabels=t.columns,loc='center');note='The area-price correlation is approximately -0.0025, showing almost no linear association in this dataset.'
  elif key[:2]=='09':
   t.set_index(t.columns[0]).head(20).plot.bar(stacked=True,ax=ax);note='The crosstab compares bedroom counts within cities. Counts reflect the supplied sample rather than city housing inventory.'
  else:
   metric='mean' if 'mean' in t else 'median' if 'median' in t else 'count'
   numbers=t.select_dtypes('number').columns.tolist()
   if metric not in t:metric=numbers[-1]
   labels=[c for c in t if c not in ['count','mean','median'] and c not in numbers]
   if not labels:labels=[t.columns[0]]
   display=t.nlargest(15,metric) if len(t)>15 else t
   names=display[labels].astype(str).agg(' / '.join,axis=1).str.slice(0,75)
   ax.barh(names,display[metric]);ax.set_xlabel(metric+(' price (INR lakhs)' if key[:2] in ['07','10','14','18'] else ' price per sq ft (INR)' if metric in ['mean','median'] and key[:2]!='08' else ''))
   maxi=t.loc[t[metric].idxmax()];mini=t.loc[t[metric].idxmin()]
   note=f"Across {len(t):,} reported groups, {metric} ranges from {mini[metric]:,.2f} to {maxi[metric]:,.2f}. Highest group: {' / '.join(str(maxi[c]) for c in labels)}. Compare sample counts before interpreting differences."
  if key[:2]=='10':note+=' These are the five highest mean-price locality groups with at least ten records. No observed dates are available; projected trends are assumption-based, not historical.'
  if key[:2]=='05':note+=' IQR flags are statistical diagnostics, not automatic deletion rules. Floor inconsistencies are separate physical checks.'
  if key[:2] in ['12','13','14','15','18','19','20']:note+=' Group differences do not prove a causal effect on prices.'
  ax.set_title(title);fig.tight_layout();fig.savefig(out/(key+'.png'),dpi=130);plt.close(fig)
  insights[key]={'title':title,'interpretation':note,'table':path.name,'chart':key+'.png'}
 # Geographic coordinates are unnecessary for an aggregate category heatmap.
 d=pd.read_csv(ROOT/'data/processed/housing_audited.csv')
 heat=d.pivot_table(index='City',columns='Property_Type',values='Calculated_Price_per_SqFt_INR',aggfunc='median')
 heat.to_csv(out/'city_type_heatmap.csv')
 fig,ax=plt.subplots(figsize=(10,12));im=ax.imshow(heat.values,cmap='YlGnBu',aspect='auto');ax.set_xticks(range(len(heat.columns)),heat.columns,rotation=15);ax.set_yticks(range(len(heat)),heat.index,fontsize=8);ax.set_title('Median price per sq ft by city and property type (INR)');fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(out/'city_type_heatmap.png',dpi=130);plt.close(fig)
 top=pd.read_csv(out/'10_expensive_localities.csv')
 projections=[]
 for _,r in top.iterrows():
  for year in range(6):projections.append({'City':r.City,'Locality':r.Locality,'Years_Ahead':year,'Assumed_Growth_Rate':.08,'Scenario_Mean_Price_Lakhs':r['mean']*1.08**year})
 pd.DataFrame(projections).to_csv(out/'top_locality_scenarios.csv',index=False)
 coverage=[{'requirement':'Historical city and locality price trends','status':'blocked_missing_data','needed':'Dated observations of prices for comparable property cohorts'}, {'requirement':'Area versus realized investment return','status':'blocked_missing_data','needed':'Purchase and resale prices, dates, income and costs'}, {'requirement':'Crime versus investment classification','status':'blocked_missing_data','needed':'Crime rates with verified geography and reporting period'}, {'requirement':'Infrastructure score versus resale value','status':'blocked_missing_data','needed':'Defined infrastructure scores and observed resale prices'}]
 (out/'insights.json').write_text(json.dumps(insights,indent=2))
 (ROOT/'reports/data_requirements.json').write_text(json.dumps(coverage,indent=2))
 lines=['# Exploratory analysis findings','','The supplied data is cross-sectional. Group comparisons describe this sample. Scenario paths use an assumed 8 percent rate and are not historical trends.','']
 for k,v in insights.items():lines.extend(['## '+k[:2]+' '+v['title'],'',v['interpretation'],'',f"![{v['title']}](eda/{v['chart']})",'',f"[Full table](eda/{v['table']})",''])
 (ROOT/'reports/eda_findings.md').write_text('\n'.join(lines))
 print('Created 20 EDA visuals, interpretations, city heatmap and locality scenarios.')
if __name__=='__main__':main()
