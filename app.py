"""An editorial property studio over the verified capstone models and source data."""
from pathlib import Path
from html import escape
import json
import joblib
import pandas as pd
import altair as alt
import streamlit as st
from src.features import enrich
from src.studio_ui import architecture,eyebrow,heading,chart_style,bar_chart,money

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Property Studio | Real Estate Investment Advisor',page_icon='◧',layout='wide')
st.markdown('<style>'+ (ROOT/'assets/studio.css').read_text()+'</style>',unsafe_allow_html=True)

@st.cache_data
def load_data():return pd.read_csv(ROOT/'data/processed/housing_audited.csv')

@st.cache_resource
def load_models(version):return joblib.load(ROOT/'models/regression.joblib'),joblib.load(ROOT/'models/classification.joblib')

@st.cache_data
def read_table(name):return pd.read_csv(ROOT/name)

if not (ROOT/'models/metadata.json').exists():
    st.info('The property data and models are being prepared. Please check back shortly.')
    st.stop()
d=load_data();meta=json.loads((ROOT/'models/metadata.json').read_text())
reg,clf=load_models(tuple((ROOT/f'models/{task}.joblib').stat().st_mtime_ns for task in ['regression','classification']))
thresholds=read_table('models/cohort_thresholds.csv')
metrics=json.loads((ROOT/'reports/model_metrics.json').read_text())
insights=json.loads((ROOT/'reports/eda/insights.json').read_text())
ss=st.session_state
ss.setdefault('saved_ids',[]);ss.setdefault('draft',{});ss.setdefault('workspace','Discover')
ss.setdefault('assessment_result',None);ss.setdefault('page',1)


def go(page):ss['workspace']=page

def select_property(property_id):
    row=d.loc[d.ID==property_id].iloc[0]
    draft={c:(int(row[c]) if c in meta['numeric'] else str(row[c])) for c in meta['features']}
    draft['asking']=float(row.Price_in_Lakhs);draft['rate']=8.0;draft['property_id']=int(property_id)
    ss['draft']=draft
    for c in meta['features']:ss['input_'+c]=draft[c]
    ss['asking_price']=draft['asking'];ss['scenario_rate']=8.0
    ss['assessment_result']=None;ss['workspace']='Property desk'

def toggle_saved(property_id):
    saved=list(ss['saved_ids'])
    if property_id in saved:saved.remove(property_id)
    else:saved.append(property_id)
    ss['saved_ids']=saved

def reset_city():
    options=sorted(d.loc[d.State==ss['input_State'],'City'].unique().tolist())
    if ss.get('input_City') not in options:ss['input_City']=options[0]

def page_header(kicker,title,description):
    eyebrow(kicker);st.title(title);st.write(description)

def render_listing(row,position):
    pid=int(row.ID)
    with st.container(key=f'property_card_{position}'):
        st.markdown('<div class="property-art">'+architecture(row.Property_Type)+'</div>',unsafe_allow_html=True)
        st.markdown(f'<div class="property-type">{escape(row.Property_Type)} · Listing {pid}</div><div class="property-title">{int(row.BHK)} BHK in {escape(row.City)}</div><div class="property-location">{escape(row.Locality)} · {escape(row.State)}</div><div class="property-price">{money(float(row.Price_in_Lakhs))}</div><div class="property-meta">{int(row.Size_in_SqFt):,} sq ft &nbsp; / &nbsp; ₹{row.Calculated_Price_per_SqFt_INR:,.0f} per sq ft</div>',unsafe_allow_html=True)
        if bool(row.Flag_Floor_Above_Total):st.caption('Source floor information needs review.')
        st.button('Assess this property',key=f'assess_{pid}',type='primary',width='stretch',on_click=select_property,args=(pid,))
        st.button('Remove from saved' if pid in ss['saved_ids'] else 'Save for comparison',key=f'save_{pid}',width='stretch',on_click=toggle_saved,args=(pid,))

st.markdown('<div class="brand"><div class="brand-mark">P</div><div><div class="brand-name">Property Studio</div><div class="brand-caption">REAL ESTATE INVESTMENT ADVISOR</div></div></div>',unsafe_allow_html=True)
view=st.radio('Workspace',['Discover','Property desk','Market atlas','Method & evidence'],key='workspace',horizontal=True,label_visibility='collapsed')

if view=='Discover':
    for key,value in ss.get('search_memory',{}).items():
        if key not in ['filter_budget','filter_area','filter_quality']:ss.setdefault(key,value)
    left,right=st.columns([1.25,1],gap='large',vertical_alignment='center')
    with left:
        eyebrow('A considered approach to property')
        st.markdown('<h1>Find a place.<br>See the possibilities.</h1>',unsafe_allow_html=True)
        st.markdown('<div class="hero-copy">Explore Indian property listings, compare asking prices, and put your own assumptions to work. A clear starting point for a closer look.</div>',unsafe_allow_html=True)
        st.button('Start with a property assessment',key='start_assessment',type='primary',on_click=go,args=('Property desk',))
    with right:st.markdown('<div class="hero-art">'+architecture()+'</div>',unsafe_allow_html=True)
    st.caption('Illustrative architecture. Listing cards use supplied records; drawings are not property photographs.')
    a,b,c=st.columns(3)
    a.metric('Properties in the dataset',f'{len(d):,}');b.metric('Cities to explore',d.City.nunique());c.metric('Saved for comparison',len(ss['saved_ids']))
    st.markdown('')
    filters,results=st.columns([1,3],gap='large')
    with filters:
        with st.container(key='filter_panel'):
            eyebrow('Make it yours');st.subheader('Your search')
            city=st.selectbox('City',['All cities']+sorted(d.City.unique().tolist()),key='filter_city')
            kind=st.selectbox('Property type',['All types']+sorted(d.Property_Type.unique().tolist()),key='filter_type')
            budget=st.slider('Maximum price (INR lakhs)',float(d.Price_in_Lakhs.min()),float(d.Price_in_Lakhs.max()),ss.get('search_memory',{}).get('filter_budget',float(d.Price_in_Lakhs.max())),key='filter_budget')
            bhk=st.multiselect('Bedrooms (BHK)',sorted(d.BHK.unique().tolist()),key='filter_bhk')
            area=st.slider('Area range (sq ft)',int(d.Size_in_SqFt.min()),int(d.Size_in_SqFt.max()),ss.get('search_memory',{}).get('filter_area',(int(d.Size_in_SqFt.min()),int(d.Size_in_SqFt.max()))),key='filter_area')
            valid=st.checkbox('Exclude inconsistent floor records',value=ss.get('search_memory',{}).get('filter_quality',True),key='filter_quality')
            st.caption('The dataset contains source inconsistencies. This filter excludes records where the floor exceeds the building total.')
    with results:
        heading('The property edit','Browse a shortlist, then open a listing in the property desk.')
        f=d[(d.Price_in_Lakhs<=budget)&d.Size_in_SqFt.between(*area)]
        if city!='All cities':f=f[f.City==city]
        if kind!='All types':f=f[f.Property_Type==kind]
        if bhk:f=f[f.BHK.isin(bhk)]
        if valid:f=f[~f.Flag_Floor_Above_Total]
        st.metric('Matching properties',f'{len(f):,}')
        sort=st.selectbox('Sort listings',['Price: low to high','Price: high to low','Area: largest first'],key='listing_sort')
        sort_col='Size_in_SqFt' if sort=='Area: largest first' else 'Price_in_Lakhs'
        f=f.sort_values([sort_col,'ID'],ascending=[sort=='Price: low to high',True])
        total_pages=max(1,(len(f)+5)//6)
        if ss['page']>total_pages:ss['page']=1
        page=int(st.number_input('Page',min_value=1,max_value=total_pages,step=1,key='page'))
        ss['search_memory']={key:ss[key] for key in ['filter_city','filter_type','filter_budget','filter_bhk','filter_area','filter_quality','listing_sort','page']}
        st.caption(f'Page {page:,} of {total_pages:,}. Six listings per page; all matching records are available below.')
        visible=f.iloc[(page-1)*6:page*6]
        if visible.empty:st.info('No listings match this search. Increase your budget or broaden the location and bedroom filters.')
        for offset in range(0,len(visible),2):
            cols=st.columns(2,gap='medium')
            for j,(_,row) in enumerate(visible.iloc[offset:offset+2].iterrows()):
                with cols[j]:render_listing(row,offset+j)
        with st.expander('Browse the matching data'):
            st.dataframe(f[['ID','City','Locality','Property_Type','BHK','Size_in_SqFt','Price_in_Lakhs','Calculated_Price_per_SqFt_INR']].head(500),hide_index=True,width='stretch')
            st.caption('Table preview is limited to 500 rows. Download contains every matching record.')
            st.download_button('Download matching listings',f.to_csv(index=False).encode(),file_name='matching_properties.csv',mime='text/csv')
    if ss['saved_ids']:
        heading('Keep them in view','Saved listings remain in this browser session. Compare values before opening an assessment.')
        saved=d[d.ID.isin(ss['saved_ids'])]
        st.dataframe(saved[['ID','City','Property_Type','BHK','Size_in_SqFt','Price_in_Lakhs','Calculated_Price_per_SqFt_INR']],hide_index=True,width='stretch')
        selected=st.selectbox('Choose a saved listing',saved.ID.tolist(),format_func=lambda pid:f'Listing {pid} · '+str(saved.set_index('ID').loc[pid,'City']),key='saved_choice')
        st.button('Open saved listing',key='open_saved',on_click=select_property,args=(selected,))

elif view=='Property desk':
    page_header('From asking price to a clearer picture','A closer look at your property.','Start with the essentials. Add property details, then compare the model screen and your five-year assumptions.')
    draft=ss['draft']
    default_city=str(draft.get('City','Ahmedabad'))
    default_state=str(draft.get('State',d.loc[d.City==default_city,'State'].iloc[0]))
    for c in meta['features']:
        default=draft.get(c,int(d[c].median()) if c in meta['numeric'] else str(sorted(d[c].unique())[0]))
        ss.setdefault('input_'+c,default)
    # Cold-start defaults must form a valid pair, and city choices follow the selected state.
    if not draft and 'desk_initialized' not in ss:
        ss['input_State']=default_state;ss['input_City']=default_city;ss['desk_initialized']=True
    ss.setdefault('asking_price',float(draft.get('asking',200.0)));ss.setdefault('scenario_rate',float(draft.get('rate',8.0)))
    editor,summary=st.columns([1.2,1],gap='large')
    with editor:
        eyebrow('01 / Location')
        loc=st.columns(2)
        with loc[0]:state=st.selectbox('State',sorted(d.State.unique().tolist()),key='input_State',on_change=reset_city)
        city_options=sorted(d.loc[d.State==state,'City'].unique().tolist())
        if ss.get('input_City') not in city_options:ss['input_City']=city_options[0]
        with loc[1]:city=st.selectbox('City',city_options,key='input_City')
        with st.form('assessment'):
            eyebrow('02 / The essentials')
            core=st.columns(2)
            with core[0]:
                property_type=st.selectbox('Property type',sorted(d.Property_Type.unique().tolist()),key='input_Property_Type')
                size=st.number_input('Area (sq ft)',min_value=int(d.Size_in_SqFt.min()),max_value=int(d.Size_in_SqFt.max()),step=1,key='input_Size_in_SqFt')
                asking=st.number_input('Asking price (INR lakhs)',min_value=.01,step=5.0,key='asking_price')
            with core[1]:
                bedrooms=st.number_input('Bedrooms (BHK)',min_value=int(d.BHK.min()),max_value=int(d.BHK.max()),step=1,key='input_BHK')
                age=st.number_input('Property age in the source year',min_value=int(d.Age_of_Property.min()),max_value=int(d.Age_of_Property.max()),step=1,key='input_Age_of_Property')
                st.caption('Age uses the dataset reference year, 2025. Prices are in INR lakhs: 100 lakhs = 1 crore.')
            with st.expander('Add furnishing, services and amenities',expanded=False):
                detail_cols=st.columns(2)
                detail_cats=[c for c in meta['categorical'] if c not in ['State','City','Property_Type']]
                for i,c in enumerate(detail_cats):
                    with detail_cols[i%2]:st.selectbox(c.replace('_',' '),sorted(d[c].unique().tolist()),key='input_'+c)
                for i,c in enumerate(['Nearby_Schools','Nearby_Hospitals','Amenity_Count']):
                    with detail_cols[i%2]:st.number_input(c.replace('_',' '),min_value=int(d[c].min()),max_value=int(d[c].max()),step=1,key='input_'+c)
                st.caption('When left unchanged, these fields use the displayed defaults. They are model inputs, not verified facts about a new property.')
            eyebrow('03 / Your scenario')
            rate=st.slider('Assumed annual price change (%)',-20.0,20.0,step=.5,key='scenario_rate')
            st.caption('Choose a hypothetical growth rate. The regression model uses the separate fixed 8% target specified for this project.')
            submitted=st.form_submit_button('Build my assessment',type='primary',width='stretch')
        inputs={c:ss['input_'+c] for c in meta['features']};inputs['State']=state;inputs['City']=city
        ss['draft']={**inputs,'asking':asking,'rate':rate}
        if submitted:
            inputs['Price_in_Lakhs']=asking
            x=enrich(pd.DataFrame([inputs]),thresholds,meta['global_ppsf_median'])
            result={'inputs':inputs,'asking':asking,'rate':rate,'future':float(reg.predict(x[meta['regression_features']])[0]),'probability':float(clf.predict_proba(x[meta['classification_features']])[0,1]),'model_good':bool(clf.predict(x[meta['classification_features']])[0]),'threshold':float(x.Cohort_Median_Price_per_SqFt_INR.iloc[0]),'ppsf':float(x.Calculated_Price_per_SqFt_INR.iloc[0])}
            result['good']=result['ppsf']<=result['threshold'];ss['assessment_result']=result;ss['assessment_completed']=True
    with summary:
        with st.container(key='assessment_results'):
            eyebrow('Your assessment')
            r=ss['assessment_result']
            if r is None:
                st.markdown('<div class="hero-art">'+architecture(draft.get('Property_Type','Apartment'))+'</div>',unsafe_allow_html=True)
                st.subheader('Give the numbers a little context.')
                st.write('Your assessment will compare the asking price with its city and property-type cohort, then show the five-year model estimate and your own scenario.')
                st.caption('Complete the essentials and select Build my assessment.')
            else:
                st.subheader(f"{int(r['inputs']['BHK'])} BHK · {r['inputs']['City']}")
                st.caption(f"Assessment for {r['inputs']['Size_in_SqFt']:,} sq ft at {money(r['asking'])}.")
                if any(r['inputs'].get(c)!=inputs.get(c) for c in meta['features']) or r['asking']!=asking or r['rate']!=rate:
                    st.info('Details have changed. Build the assessment again to update these results.')
                st.markdown('<div class="result-label">Model classification</div><div class="result-value">'+('Meets the investment screen' if r['model_good'] else 'Above the investment screen')+'</div>',unsafe_allow_html=True)
                st.write('Model predicts Good Investment: '+('Yes' if r['model_good'] else 'No'))
                st.metric('Model probability of proxy label',f"{r['probability']:.1%}")
                st.caption('Uncalibrated agreement with a known pricing rule. This is not a probability of earning a return.')
                st.divider()
                st.write('**Direct price screen:** '+('At or below cohort median' if r['good'] else 'Above cohort median'))
                st.write(f"₹{r['ppsf']:,.0f} per sq ft asking · ₹{r['threshold']:,.0f} cohort median")
                st.metric('Regression estimated price after 5 years at assumed 8% (INR lakhs)',f"{r['future']:,.2f}")
                st.metric('Five-year scenario from asking price (INR lakhs)',f"{r['asking']*(1+r['rate']/100)**5:,.2f}")
                st.caption('The regression reproduces a synthetic 8% growth target. Your scenario is calculated separately. Neither is a validated market forecast.')
                st.download_button('Download this assessment',json.dumps(r,indent=2),file_name='property_assessment.json',mime='application/json')
    if ss['assessment_result']:
        r=ss['assessment_result'];heading('Three ways the next five years could look.','Hypothetical paths from the asking price, not historical price trends.')
        rows=[]
        for label,rate_value in [('Your assumption',r['rate']/100),('No growth',0),('Downside −5%',-.05)]:
            rows.extend({'Year':year,'Price (INR lakhs)':r['asking']*(1+rate_value)**year,'Scenario':label} for year in range(6))
        chart=alt.Chart(pd.DataFrame(rows)).mark_line(point=True,strokeWidth=2.5).encode(x=alt.X('Year:Q',axis=alt.Axis(tickMinStep=1)),y=alt.Y('Price (INR lakhs):Q',scale=alt.Scale(zero=False)),color=alt.Color('Scenario:N',scale=alt.Scale(range=['#b58857','#9baba2','#245749'])),tooltip=['Scenario','Year',alt.Tooltip('Price (INR lakhs):Q',format=',.2f')]).properties(height=310)
        st.altair_chart(chart_style(chart),width='stretch')
        st.caption('Scenarios exclude rent, financing, tax, maintenance, transaction costs and inflation. They do not quantify net profitability.')

elif view=='Market atlas':
    page_header('Patterns, places and perspective','Read the market in context.','Twenty questions about the supplied housing sample. Explore the evidence behind each comparison.')
    topics=['01–05 / Price & space','06–10 / Location','11–15 / Property relationships','16–20 / Ownership & amenities']
    topic=st.selectbox('Research chapter',topics,key='research_chapter')
    chapter=topics.index(topic)
    keys=list(insights)[chapter*5:(chapter+1)*5]
    question=st.selectbox('EDA question',keys,format_func=lambda k:k[:2]+' · '+insights[k]['title'],key=f'eda_question_{chapter}')
    item=insights[question];heading(item['title']);st.write(item['interpretation'])
    st.image(str(ROOT/'reports/eda'/item['chart']),width='stretch')
    with st.expander('Inspect and download the supporting data'):
        table=read_table('reports/eda/'+item['table']);st.dataframe(table.head(500),hide_index=True,width='stretch')
        st.caption('Preview shows up to 500 rows. Download contains the complete table.')
        st.download_button('Download full EDA table',(ROOT/'reports/eda'/item['table']).read_bytes(),file_name=item['table'],mime='text/csv')
    st.divider();heading('A different view of location.','Median asking price per sq ft by city and property type. An aggregate heatmap, without invented coordinates.')
    heat=read_table('reports/eda/city_type_heatmap.csv').melt(id_vars='City',var_name='Property type',value_name='INR per sq ft')
    heat_chart=alt.Chart(heat).mark_rect().encode(x=alt.X('Property type:N',title=None),y=alt.Y('City:N',title=None),color=alt.Color('INR per sq ft:Q',scale=alt.Scale(range=['#eef0e6','#9db39f','#245749'])),tooltip=['City','Property type',alt.Tooltip('INR per sq ft:Q',format=',.0f')]).properties(height=700)
    st.altair_chart(chart_style(heat_chart),width='stretch')
    heading('Localities, looking ahead.','Five high mean-price locality groups with at least ten records. Paths assume 8% annual growth.')
    projection=read_table('reports/eda/top_locality_scenarios.csv').copy();projection['Location']=projection.City+' · '+projection.Locality
    st.line_chart(projection.pivot(index='Years_Ahead',columns='Location',values='Scenario_Mean_Price_Lakhs'),y_label='Scenario mean price (INR lakhs)',color=['#245749','#b58857','#6d8e79','#74776f','#b4a48d'])
    st.caption('These are hypothetical projections. No historical locality price series was supplied.')

else:
    page_header('Know what sits behind the numbers','Evidence before expectation.','The data, model definitions, measured performance and limits of this educational project.')
    audit=json.loads((ROOT/'reports/phase1_audit.json').read_text())
    a,b,c=st.columns(3);a.metric('Source properties',f"{audit['rows']:,}");b.metric('Floor inconsistencies',f"{audit['floor_above_total']:,}");c.metric('Statistical price flags',f"{audit['price_per_sqft_iqr_flags']:,}")
    st.markdown('<div class="method-note">Five-year prices are assumption-based. Investment labels come from a relative-price screening rule. The project does not establish actual investment profitability or future market forecasting skill.</div>',unsafe_allow_html=True)
    heading('What the models learn.')
    left,right=st.columns(2,gap='large')
    with left:
        st.subheader('01 / The price screen')
        st.write('Good Investment means price per sq ft at or below the training city/property-type median. The classifier uses the price-to-median ratio to imitate that rule. Its probability is uncalibrated.')
    with right:
        st.subheader('02 / The five-year estimate')
        st.write('Future_Price_5Y = current price × 1.08⁵. Regression learns this synthetic target from the brief. Low errors measure formula reproduction, not observed appreciation.')
    st.caption('150,000 training records · 50,000 validation records · 50,000 test records. Thresholds and preprocessing are fitted only on training data. Validation selects models; test data supplies reported metrics.')
    heading('Performance, with its definition attached.')
    task=st.selectbox('Model task',['Classification','Regression'],key='metrics_task')
    chosen=[r for r in metrics if r['task']==task.lower()]
    fields=['model','accuracy','precision','recall','f1','roc_auc'] if task=='Classification' else ['model','mae','rmse','r2']
    st.dataframe(pd.DataFrame(chosen)[fields],hide_index=True,width='stretch')
    st.caption('Classification evaluates rule imitation. Regression errors are INR lakhs against synthetic five-year targets.')
    if task=='Classification':
        selected=next(r for r in chosen if r['model']==meta['selected_classification'])
        st.write('**Selected classifier confusion matrix** · actual rows, predicted columns')
        st.dataframe(pd.DataFrame(selected['confusion_matrix'],index=['Actual No','Actual Yes'],columns=['Predicted No','Predicted Yes']),width='stretch')
    importance=read_table(f'models/{task.lower()}_importance.csv').head(10).copy()
    importance['feature']=importance.feature.str.replace('numeric__','',regex=False).str.replace('category__','',regex=False)
    bar_chart(importance,'feature','importance','Relative model weight')
    st.caption('Feature weights reflect model behavior, not causal drivers of appreciation. Linear-model coefficient magnitudes and forest importance use different scales.')
    with st.expander('Data preparation and reproducibility'):
        st.write('Original values are preserved. INR price per sq ft is recomputed. Invalid floor relationships and outliers are flagged, not silently repaired. Identifiers, floor fields and generic locality labels are excluded from prediction. Age follows the dataset reference year 2025.')
        st.write('The repository includes complete training scripts, target definitions, split assignments, reports and six portable MLflow experiments with selected model aliases.')
        st.link_button('Open the complete project on GitHub','https://github.com/purans07/Real-Estate-Investment-Advisor')
    heading('What additional data would unlock.')
    st.dataframe(pd.DataFrame(json.loads((ROOT/'reports/data_requirements.json').read_text())).rename(columns={'requirement':'Analysis','status':'Status','needed':'Required data'}),hide_index=True,width='stretch')
    st.caption('Observation dates, crime rates, defined infrastructure scores, realized returns and verified coordinates were not supplied. These outcomes are not invented or substituted with unrelated fields.')

st.markdown('<div class="footnote">PROPERTY STUDIO &nbsp; / &nbsp; Real Estate Investment Advisor<br>Educational analysis of the supplied housing dataset. Price scenarios use explicit assumptions; investment labels are screening rules, not verified returns.</div>',unsafe_allow_html=True)
