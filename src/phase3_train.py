"""Train assumption-based Future_Price_5Y regression and investment rule imitation."""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression,LogisticRegression
from sklearn.ensemble import RandomForestRegressor,RandomForestClassifier
from sklearn.dummy import DummyRegressor,DummyClassifier
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score,accuracy_score,f1_score,confusion_matrix,roc_auc_score,precision_score,recall_score
from features import BASE_NUM,CAT,REG_NUM,CLF_NUM,RATE,FACTOR,enrich
ROOT=Path(__file__).resolve().parents[1]

def preprocess(numeric):
    return ColumnTransformer([('numeric',make_pipeline(SimpleImputer(strategy='median'),StandardScaler()),numeric),('category',make_pipeline(SimpleImputer(strategy='most_frequent'),OneHotEncoder(handle_unknown='ignore')),CAT)])

def main():
    raw=pd.read_csv(ROOT/'data/processed/housing_audited.csv')
    dev,test=train_test_split(raw,test_size=.2,random_state=42)
    train,val=train_test_split(dev,test_size=.25,random_state=42)
    thresholds=train.groupby(['City','Property_Type']).Calculated_Price_per_SqFt_INR.median()
    fallback=float(train.Calculated_Price_per_SqFt_INR.median())
    data=enrich(raw,thresholds,fallback)
    data['Good_Investment']=(data.Price_to_Cohort_Median<=1).astype(int)
    data['Future_Price_5Y']=data.Price_in_Lakhs*FACTOR
    data['Assumed_Annual_Growth_Rate']=RATE
    data['Split']='train';data.loc[val.index,'Split']='validation';data.loc[test.index,'Split']='test'
    data[['ID','Split','Good_Investment','Future_Price_5Y','Assumed_Annual_Growth_Rate','Cohort_Median_Price_per_SqFt_INR','Price_to_Cohort_Median']].to_csv(ROOT/'data/processed/model_targets.csv',index=False)
    train,val,test=(data.loc[x.index] for x in [train,val,test])
    mlflow.set_tracking_uri('sqlite:///'+str(ROOT/'mlflow.db'))
    mlflow.set_experiment('Real Estate Brief Aligned Assumed Targets')
    out=ROOT/'models';out.mkdir(exist_ok=True)
    reports=[];best={}
    candidates={'regression':{'median_baseline':DummyRegressor(strategy='median'),'linear':LinearRegression(tol=1e-10),'forest':RandomForestRegressor(n_estimators=40,max_depth=12,min_samples_leaf=10,n_jobs=2,random_state=42)},'classification':{'majority_baseline':DummyClassifier(strategy='most_frequent'),'logistic':LogisticRegression(max_iter=500,C=100),'forest':RandomForestClassifier(n_estimators=40,max_depth=10,min_samples_leaf=3,n_jobs=2,random_state=42)}}
    for task,models in candidates.items():
        nums=REG_NUM if task=='regression' else CLF_NUM
        features=nums+CAT;target='Future_Price_5Y' if task=='regression' else 'Good_Investment'
        for name,estimator in models.items():
            pipe=make_pipeline(preprocess(nums),estimator)
            with mlflow.start_run(run_name=f'{task}_{name}') as run:
                pipe.fit(train[features],train[target]);vp=pipe.predict(val[features]);p=pipe.predict(test[features])
                if task=='regression':
                    scores={'mae':float(mean_absolute_error(test[target],p)),'rmse':float(np.sqrt(mean_squared_error(test[target],p))),'r2':float(r2_score(test[target],p))}
                    rank=-float(np.sqrt(mean_squared_error(val[target],vp)))
                else:
                    scores={'accuracy':float(accuracy_score(test[target],p)),'precision':float(precision_score(test[target],p,zero_division=0)),'recall':float(recall_score(test[target],p)),'f1':float(f1_score(test[target],p)),'roc_auc':float(roc_auc_score(test[target],pipe.predict_proba(test[features])[:,1]))}
                    rank=float(f1_score(val[target],vp))
                params={'task':task,'model':name,'seed':42,'train_rows':len(train),'validation_rows':len(val),'test_rows':len(test),'target':target,'target_kind':'assumption_based' if task=='regression' else 'rule_imitation','annual_rate':RATE}
                params.update({k:v for k,v in estimator.get_params().items() if isinstance(v,(str,int,float,bool)) or v is None})
                mlflow.log_params(params);mlflow.log_metrics(scores);mlflow.log_metric('validation_selection_score',rank)
                info=mlflow.sklearn.log_model(pipe,name='model',serialization_format='cloudpickle',registered_model_name=f'brief_aligned_{task}_{name}',input_example=train[features].head(3),pip_requirements=['scikit-learn==1.9.1','pandas==3.1.0','numpy==2.5.4'])
                record={'task':task,'model':name,'target':target,'evaluation_kind':params['target_kind'],**scores,'validation_selection_score':rank,'run_id':run.info.run_id}
                if task=='classification':record['confusion_matrix']=confusion_matrix(test[target],p).tolist()
                reports.append(record)
                if task not in best or rank>best[task][0]:best[task]=(rank,name,pipe)
                print(record,flush=True)
    metadata={'features':BASE_NUM+CAT,'numeric':BASE_NUM,'categorical':CAT,'regression_features':REG_NUM+CAT,'classification_features':CLF_NUM+CAT,'global_ppsf_median':fallback,'training_rows':len(train),'validation_rows':len(val),'test_rows':len(test),'scenario_default_rate':RATE,'regression_target':'Future_Price_5Y','regression_target_kind':'synthetic fixed-rate scenario','classification_target':'Good_Investment','classification_target_kind':'imitation of the known price-to-cohort-median rule','experiment_name':'Real Estate Brief Aligned Assumed Targets','model_selection':'60/20/20 training validation test; thresholds and preprocessing fitted on training; validation selects models'}
    thresholds.rename('Training_Median_Price_per_SqFt_INR').reset_index().to_csv(out/'cohort_thresholds.csv',index=False)
    client=mlflow.MlflowClient()
    for task,(_,name,pipe) in best.items():
        joblib.dump(pipe,out/f'{task}.joblib');metadata[f'selected_{task}']=name
        model=pipe.steps[-1][1];names=pipe.steps[0][1].get_feature_names_out()
        imp=model.feature_importances_ if hasattr(model,'feature_importances_') else np.abs(np.asarray(model.coef_).ravel()) if hasattr(model,'coef_') else np.zeros(len(names))
        pd.DataFrame({'feature':names,'importance':imp}).sort_values('importance',ascending=False).to_csv(out/f'{task}_importance.csv',index=False)
        versions=client.search_model_versions(f"name='brief_aligned_{task}_{name}'")
        client.set_registered_model_alias(f'brief_aligned_{task}_{name}','selected',max(versions,key=lambda x:int(x.version)).version)
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2))
    (ROOT/'reports/model_metrics.json').write_text(json.dumps(reports,indent=2))
    print('Saved assumed targets, selected models and MLflow aliases.',flush=True)
if __name__=='__main__':main()
