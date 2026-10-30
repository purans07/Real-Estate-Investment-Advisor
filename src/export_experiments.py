"""Export portable MLflow experiment records and candidate model artifacts."""
from pathlib import Path
import json,shutil
import mlflow
ROOT=Path(__file__).resolve().parents[1]

def main():
 m=json.loads((ROOT/'models/metadata.json').read_text());mlflow.set_tracking_uri('sqlite:///'+str(ROOT/'mlflow.db'));client=mlflow.MlflowClient()
 out=ROOT/'experiments';out.mkdir(exist_ok=True)
 records=[]
 for row in json.loads((ROOT/'reports/model_metrics.json').read_text()):
  run=client.get_run(row['run_id']);name=f"brief_aligned_{row['task']}_{row['model']}"
  versions=[v for v in client.search_model_versions(f"name='{name}'") if v.run_id==row['run_id']]
  version=max(versions,key=lambda v:int(v.version))
  local=Path(mlflow.artifacts.download_artifacts(artifact_uri=version.source))
  target=out/(row['task']+'_'+row['model']);shutil.copytree(local,target,dirs_exist_ok=True)
  records.append({'original_run_id':row['run_id'],'name':name,'params':run.data.params,'metrics':run.data.metrics,'model_path':str(target.relative_to(out)),'selected':m['selected_'+row['task']]==row['model']})
 (out/'manifest.json').write_text(json.dumps({'experiment_name':m['experiment_name'],'target_warning':'Synthetic future prices and rule labels; scores are not real investment accuracy.','runs':records},indent=2))
 print('Exported',len(records),'portable experiment records and model artifacts.')
if __name__=='__main__':main()
