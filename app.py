"""Local Streamlit capstone: property exploration and explicit scenario analysis."""
from pathlib import Path
import json
import joblib
import pandas as pd
import streamlit as st
from src.features import enrich

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Real Estate Investment Advisor',layout='wide')
st.title('Real Estate Investment Advisor')
st.caption('Explore the supplied housing dataset and compare five-year price scenarios.')
st.warning('No observed future prices or returns are available. Investment labels are price-based screening rules. Growth rates are assumptions, and model probabilities are not probabilities of earning a return.')

@st.cache_data
def load_data():return pd.read_csv(ROOT/'data/processed/housing_audited.csv')

@st.cache_resource
def load_models(version):
    return joblib.load(ROOT/'models/regression.joblib'),joblib.load(ROOT/'models/classification.joblib')

if not (ROOT/'models/metadata.json').exists():
    st.info('Run the three phase scripts listed in the README to prepare data and models.')
    st.stop()
d=load_data()
meta=json.loads((ROOT/'models/metadata.json').read_text())
reg,clf=load_models(tuple((ROOT/f"models/{task}.joblib").stat().st_mtime_ns for task in ["regression","classification"]))
explore,assess,analytics,quality=st.tabs(['Explore properties','Assess a property','Exploratory analysis','Data and model quality'])
with explore:
    city=st.selectbox('City',['All']+sorted(d.City.unique().tolist()))
    budget=st.slider('Maximum price (INR lakhs)',float(d.Price_in_Lakhs.min()),float(d.Price_in_Lakhs.max()),float(d.Price_in_Lakhs.max()))
    bhk=st.multiselect('BHK',sorted(d.BHK.unique().tolist()))
    area=st.slider('Area range (sq ft)',int(d.Size_in_SqFt.min()),int(d.Size_in_SqFt.max()),(int(d.Size_in_SqFt.min()),int(d.Size_in_SqFt.max())))
    valid_only=st.checkbox('Exclude records with floor inconsistencies',value=True)
    f=d[(d.Price_in_Lakhs<=budget)&d.Size_in_SqFt.between(*area)]
    if city!='All':f=f[f.City==city]
    if bhk:f=f[f.BHK.isin(bhk)]
    if valid_only:f=f[~f.Flag_Floor_Above_Total]
    st.metric('Matching properties',len(f))
    if len(f):
        st.bar_chart(f.groupby('City').Price_in_Lakhs.median(),x_label='City',y_label='Median price (INR lakhs)')
        st.dataframe(f[['ID','State','City','Locality','Property_Type','BHK','Size_in_SqFt','Price_in_Lakhs','Calculated_Price_per_SqFt_INR','Flag_Floor_Above_Total']].head(500),hide_index=True)
    else:st.info('No properties match these filters.')
with assess:
    st.write('Enter property characteristics. Age follows the source reference year of 2025.')
    with st.form('assessment'):
        inputs={}
        left,right=st.columns(2)
        for i,c in enumerate(meta['categorical']):
            with (left if i%2==0 else right):
                inputs[c]=st.selectbox(c.replace('_',' '),sorted(d[c].unique().tolist()),key='input_'+c)
        for i,c in enumerate(meta['numeric']):
            with (left if i%2==0 else right):
                inputs[c]=st.number_input(c.replace('_',' '),min_value=int(d[c].min()),max_value=int(d[c].max()),value=int(d[c].median()),step=1)
        asking=st.number_input('Asking price (INR lakhs)',min_value=.01,value=200.0)
        rate=st.slider('Assumed annual price change (%)',-20.0,20.0,8.0,.5)
        submitted=st.form_submit_button('Assess property')
    if submitted:
        if not ((d.State==inputs['State'])&(d.City==inputs['City'])).any():
            st.error('The selected state and city do not match in the source data.')
        else:
            inputs['Price_in_Lakhs']=asking
            thresholds=pd.read_csv(ROOT/'models/cohort_thresholds.csv')
            x=enrich(pd.DataFrame([inputs]),thresholds,meta['global_ppsf_median'])
            future=float(reg.predict(x[meta['regression_features']])[0])
            probability=float(clf.predict_proba(x[meta['classification_features']])[0,1])
            model_good=bool(clf.predict(x[meta['classification_features']])[0])
            thresholds=pd.read_csv(ROOT/'models/cohort_thresholds.csv')
            cohort=thresholds[(thresholds.City==inputs['City'])&(thresholds.Property_Type==inputs['Property_Type'])]
            threshold=float(cohort.Training_Median_Price_per_SqFt_INR.iloc[0]) if len(cohort) else meta['global_ppsf_median']
            asking_ppsf=asking*100000/inputs['Size_in_SqFt']
            good=asking_ppsf<=threshold
            st.subheader('Model classification')
            st.write('Model predicts Good Investment: '+('Yes' if model_good else 'No'))
            st.subheader('Direct price based investment screen')
            st.write('Good Investment under the defined rule: '+('Yes' if good else 'No'))
            st.write(f'Asking price per sq ft: INR {asking_ppsf:,.0f}. Training city and property-type median: INR {threshold:,.0f}.')
            st.metric('Model probability of proxy label',f'{probability:.1%}')
            st.caption('The classifier imitates the known median-price rule using the price-to-median ratio. High agreement is rule reproduction, not evidence of investment profitability. Probabilities are uncalibrated.')
            st.metric('Regression estimated price after 5 years at assumed 8% (INR lakhs)',f'{future:,.2f}')
            st.caption('Regression was trained against a synthetic 8% annual growth target from the brief. This is not a validated market forecast. The editable scenario below is calculated separately.')
            st.metric('Five-year scenario from asking price (INR lakhs)',f'{asking*(1+rate/100)**5:,.2f}')
            scenarios=pd.DataFrame({'Year':range(6),'User assumption':[asking*(1+rate/100)**t for t in range(6)],'Zero growth':[asking]*6,'Downside at minus 5 percent':[asking*.95**t for t in range(6)]}).set_index('Year')
            st.line_chart(scenarios,y_label='Price (INR lakhs)')
            st.caption('Scenario prices exclude rent, financing, tax, transaction costs, maintenance, and inflation. They do not measure net profitability.')
            st.session_state['assessment_completed']=True
with quality:
    audit=json.loads((ROOT/'reports/phase1_audit.json').read_text())
    st.write({'Source rows':audit['rows'],'Floor inconsistencies':audit['floor_above_total'],'Price per sqft IQR flags':audit['price_per_sqft_iqr_flags']})
    st.write('Identifiers, unreliable floor fields and locality are excluded from modeling. Future-price regression legitimately uses current price. Classification deliberately uses the known rule ratio to imitate that rule. Outliers remain flagged.')
    metrics=pd.DataFrame(json.loads((ROOT/'reports/model_metrics.json').read_text()))
    st.dataframe(metrics.drop(columns=['confusion_matrix','run_id'],errors='ignore'),hide_index=True)
    st.caption('Regression evaluates synthetic Future_Price_5Y targets. Low error measures reproduction of the assumed growth formula. Classification evaluates rule imitation, not realized profit.')
    selected=[r for r in json.loads((ROOT/'reports/model_metrics.json').read_text()) if r['task']=='classification' and r['model']==meta['selected_classification']][0]
    st.write('Selected classifier confusion matrix: actual rows and predicted columns')
    st.dataframe(pd.DataFrame(selected['confusion_matrix'],index=['Actual No','Actual Yes'],columns=['Predicted No','Predicted Yes']))
    for task in ['regression','classification']:
        path=ROOT/f'models/{task}_importance.csv'
        if path.exists():
            st.write(task.title()+' feature weights')
            st.bar_chart(pd.read_csv(path).head(12).set_index('feature'))
    st.write('No observation dates, crime rates, RERA status, actual rents, realized returns, or geographic coordinates were supplied. Time trends, crime effects, investment returns and geographic heatmaps cannot be established.')

with analytics:
    insight_path=ROOT/'reports/eda/insights.json'
    if insight_path.exists():
        insights=json.loads(insight_path.read_text())
        question=st.selectbox('EDA question',list(insights),format_func=lambda k:k[:2]+' '+insights[k]['title'])
        item=insights[question]
        st.write(item['interpretation'])
        st.image(str(ROOT/'reports/eda'/item['chart']))
        table=pd.read_csv(ROOT/'reports/eda'/item['table'])
        st.dataframe(table.head(500),hide_index=True)
        st.download_button('Download full EDA table',(ROOT/'reports/eda'/item['table']).read_bytes(),file_name=item['table'],mime='text/csv')
        st.subheader('Location heatmap')
        st.image(str(ROOT/'reports/eda/city_type_heatmap.png'))
        st.subheader('Top locality five year scenarios')
        projections=pd.read_csv(ROOT/'reports/eda/top_locality_scenarios.csv')
        projections['Location']=projections.City+' '+projections.Locality
        st.line_chart(projections.pivot(index='Years_Ahead',columns='Location',values='Scenario_Mean_Price_Lakhs'),y_label='Scenario mean price (INR lakhs)')
        st.caption('These are projected paths at an assumed 8% annual rate; historical locality trends are unavailable.')
    if (ROOT/'reports/data_requirements.json').exists():
        st.subheader('Analyses requiring additional data')
        st.dataframe(pd.DataFrame(json.loads((ROOT/'reports/data_requirements.json').read_text())),hide_index=True)
