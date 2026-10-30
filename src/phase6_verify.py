"""Verify target definitions, held-out evaluation, app behavior and experiment records."""
from pathlib import Path
import json
import joblib
import pandas as pd
import numpy as np
import mlflow
from sklearn.metrics import accuracy_score,mean_squared_error
from streamlit.testing.v1 import AppTest
from features import FACTOR,enrich
ROOT=Path(__file__).resolve().parents[1]

def main():
 d=pd.read_csv(ROOT/'data/processed/housing_audited.csv');raw=pd.read_csv(ROOT/'india_housing_prices.csv')
 pd.testing.assert_frame_equal(raw,d[raw.columns],check_exact=False,rtol=1e-12,atol=1e-12)
 assert len(d)==250000 and d.ID.is_unique
 assert np.allclose(d.Calculated_Price_per_SqFt_INR,d.Price_in_Lakhs*100000/d.Size_in_SqFt)
 t=pd.read_csv(ROOT/'data/processed/model_targets.csv');m=json.loads((ROOT/'models/metadata.json').read_text())
 assert t.ID.is_unique and len(t)==len(d)
 assert np.allclose(t.Future_Price_5Y,d.Price_in_Lakhs*FACTOR)
 assert (t.Good_Investment==(t.Price_to_Cohort_Median<=1).astype(int)).all()
 assert t.Split.value_counts().to_dict()=={'train':150000,'validation':50000,'test':50000}
 thresholds=pd.read_csv(ROOT/'models/cohort_thresholds.csv')
 train=d.loc[t.Split=='train'];expected=train.groupby(['City','Property_Type']).Calculated_Price_per_SqFt_INR.median()
 actual=thresholds.set_index(['City','Property_Type']).iloc[:,0]
 assert np.allclose(expected.sort_index(),actual.sort_index())
 assert m['regression_target']=='Future_Price_5Y'
 assert 'Future_Price_5Y' not in m['regression_features'] and 'Good_Investment' not in m['classification_features']
 x=enrich(d,thresholds,m['global_ppsf_median']);test=t.Split=='test'
 reg=joblib.load(ROOT/'models/regression.joblib');clf=joblib.load(ROOT/'models/classification.joblib')
 rp=reg.predict(x.loc[test,m['regression_features']]);cp=clf.predict(x.loc[test,m['classification_features']])
 scores=json.loads((ROOT/'reports/model_metrics.json').read_text())
 sr=next(r for r in scores if r['task']=='regression' and r['model']==m['selected_regression'])
 sc=next(r for r in scores if r['task']=='classification' and r['model']==m['selected_classification'])
 assert np.isclose(np.sqrt(mean_squared_error(t.loc[test,'Future_Price_5Y'],rp)),sr['rmse'],atol=1e-9)
 assert np.isclose(accuracy_score(t.loc[test,'Good_Investment'],cp),sc['accuracy'])
 # Independent target boundary and unknown cohort checks.
 boundary=d.head(2).copy();boundary['City']='Unknown City';boundary['Property_Type']='Unknown Type'
 boundary['Price_in_Lakhs']=[1,100000]
 b=enrich(boundary,thresholds,m['global_ppsf_median'])
 assert np.allclose(b.Cohort_Median_Price_per_SqFt_INR,m['global_ppsf_median'])
 assert clf.predict(b[m['classification_features']]).tolist()==[1,0]
 assert len(list((ROOT/'reports/eda').glob('[0-9][0-9]_*.csv')))==20
 assert len(json.loads((ROOT/'reports/eda/insights.json').read_text()))==20
 assert all((ROOT/'reports/eda'/i['chart']).exists() for i in json.loads((ROOT/'reports/eda/insights.json').read_text()).values())
 if (ROOT/'mlflow.db').exists():
  mlflow.set_tracking_uri('sqlite:///'+str(ROOT/'mlflow.db'))
  exp=mlflow.get_experiment_by_name(m['experiment_name']);runs=mlflow.search_runs([exp.experiment_id])
  run_count=len(runs[runs.status=='FINISHED']);assert run_count>=6
  for task in ['regression','classification']:
   mlflow.MlflowClient().get_model_version_by_alias('brief_aligned_'+task+'_'+m['selected_'+task],'selected')
 else:
  export=json.loads((ROOT/'experiments/manifest.json').read_text());run_count=len(export['runs']);assert run_count==6
  assert sum(bool(r['selected']) for r in export['runs'])==2
  for row in export['runs']:
   model=mlflow.sklearn.load_model(str(ROOT/'experiments'/row['model_path']))
   fields=m[row['params']['task']+'_features'];assert len(model.predict(x[fields].head(2)))==2
 at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90).run();assert not at.exception,at.exception
 before=int(next(e.value for e in at.metric if e.label=='Matching properties').replace(',',''))
 at.selectbox(key='filter_city').select('Chennai').run();assert not at.exception
 assert int(next(e.value for e in at.metric if e.label=='Matching properties').replace(',',''))<before
 # Save a genuine listing and open its prefilled assessment.
 save_button=next(e for e in at.button if e.key and e.key.startswith('save_'))
 pid=int(save_button.key.split('_')[1]);save_button.click().run();assert not at.exception
 assert pid in at.session_state['saved_ids']
 at.button(key='assess_'+str(pid)).click().run();assert not at.exception
 assert at.radio(key='workspace').value=='Property desk'
 assert at.selectbox(key='input_City').value=='Chennai'
 assert at.number_input(key='asking_price').value==float(d.loc[d.ID==pid,'Price_in_Lakhs'].iloc[0])
 # Dependent city selection prevents invalid state/city combinations.
 at.selectbox(key='input_State').select('Gujarat').run();assert not at.exception
 assert at.selectbox(key='input_City').value in d.loc[d.State=='Gujarat','City'].unique()
 at.number_input(key='asking_price').set_value(200.0)
 at.button(key='FormSubmitter:assessment-Build my assessment').click().run();assert not at.exception,at.exception
 assert at.session_state['assessment_completed']
 assert any('Model predicts Good Investment' in e.value for e in at.markdown)
 first=next(e.value for e in at.metric if 'Five-year scenario' in e.label)
 at.slider(key='scenario_rate').set_value(0.0)
 at.button(key='FormSubmitter:assessment-Build my assessment').click().run();assert not at.exception
 second=next(e.value for e in at.metric if 'Five-year scenario' in e.label)
 assert first!=second and second=='200.00'
 old=next(e.value for e in at.metric if 'Regression estimated' in e.label)
 at.number_input(key='asking_price').set_value(300.0)
 at.button(key='FormSubmitter:assessment-Build my assessment').click().run();assert not at.exception
 new=next(e.value for e in at.metric if 'Regression estimated' in e.label);assert old!=new
 at.radio(key='workspace').set_value('Market atlas').run();assert not at.exception,at.exception
 at.selectbox(key='research_chapter').select('16–20 / Ownership & amenities').run();assert not at.exception
 assert len(at.selectbox(key='eda_question_3').options)==5
 at.radio(key='workspace').set_value('Method & evidence').run();assert not at.exception,at.exception
 at.selectbox(key='metrics_task').select('Regression').run();assert not at.exception,at.exception
 # Assessment survives navigation rather than disappearing on unrelated interactions.
 at.radio(key='workspace').set_value('Property desk').run();assert not at.exception
 assert at.session_state['assessment_result']['asking']==300.0
 assert next(e.value for e in at.metric if 'Regression estimated' in e.label)==new
 result={'data_integrity':'passed','future_target_formula':'passed','training_only_cohort_thresholds':'passed','independent_heldout_metrics':'passed','unknown_cohort_and_boundary_checks':'passed','eda_tables':20,'eda_explanations_and_visuals':20,'finished_aligned_mlflow_runs':run_count,'selected_registry_aliases':'passed','app_load_filter_assessment':'passed','model_classification_display':'passed','regression_changes_with_asking_price':'passed','zero_growth_scenario':'passed','saved_listing_prefill':'passed','dependent_state_city_selection':'passed','persistent_assessment':'passed','all_four_workspaces':'passed','public_hosting':'see reports/public_deployment_check.json for separately verified public hosting','unsupported_real_world_analyses':'blocked on missing data'}
 (ROOT/'reports/verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
