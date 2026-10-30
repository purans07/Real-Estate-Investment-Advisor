"""Restore trusted exported runs to a local MLflow database without original paths."""
from pathlib import Path
import json
import mlflow
import mlflow.sklearn
ROOT=Path(__file__).resolve().parents[1]
def main():
 manifest=json.loads((ROOT/'experiments/manifest.json').read_text())
 mlflow.set_tracking_uri('sqlite:///'+str(ROOT/'restored_mlflow.db'))
 mlflow.set_experiment(manifest['experiment_name']+' Restored')
 for r in manifest['runs']:
  with mlflow.start_run(run_name=r['name']):
   mlflow.set_tag('original_run_id',r['original_run_id']);mlflow.log_params(r['params']);mlflow.log_metrics(r['metrics'])
   model=mlflow.sklearn.load_model(str(ROOT/'experiments'/r['model_path']))
   info=mlflow.sklearn.log_model(model,name='model',serialization_format='cloudpickle',registered_model_name=r['name'],pip_requirements=['scikit-learn==1.9.1','pandas==3.1.0','numpy==2.5.4'])
   if r['selected']:
    versions=mlflow.MlflowClient().search_model_versions("name='"+r['name']+"'")
    mlflow.MlflowClient().set_registered_model_alias(r['name'],'selected',max(versions,key=lambda v:int(v.version)).version)
 print('Restored six experiment candidates. Open: mlflow ui --backend-store-uri sqlite:///restored_mlflow.db')
if __name__=='__main__':main()
