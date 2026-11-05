"""Build and inspect a self-contained ZIP without copying the local environment."""
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    output=ROOT/'submission'
    output.mkdir(exist_ok=True)
    files=[]
    for name in ['README.md','SUBMISSION.md','DEPLOYMENT.md','.gitignore','requirements.txt','assets','.streamlit/config.toml','app.py','india_housing_prices.csv','Project Title - Data Analyst, BA, FA.docx','Project Title-DS_AI_ML.docx','src','experiments','data/processed','models','reports','mlruns']:
        p=ROOT/name
        files.extend([p] if p.is_file() else [f for f in p.rglob('*') if f.is_file() and '__pycache__' not in f.parts])
    target=output/'real_estate_investment_advisor.zip'
    with tempfile.TemporaryDirectory() as temp:
        # SQLite backup provides a consistent snapshot even if a viewer is open.
        snapshot=Path(temp)/'mlflow.db'
        has_database=(ROOT/'mlflow.db').exists()
        if has_database:
            with sqlite3.connect('file:'+str(ROOT/'mlflow.db')+'?mode=ro',uri=True) as source, sqlite3.connect(snapshot) as dest:
                source.backup(dest)
        records=[{'path':str(f.relative_to(ROOT)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(files)]
        if has_database:records.append({'path':'mlflow.db','bytes':snapshot.stat().st_size,'sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest()})
        manifest={'format_version':1,'files':records,'notes':'The Python environment and caches are excluded. Historical MLflow artifacts may contain original workspace paths; see DEPLOYMENT.md.'}
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for f in files:z.write(f,'real_estate_investment_advisor/'+str(f.relative_to(ROOT)))
            if has_database:z.write(snapshot,'real_estate_investment_advisor/mlflow.db')
            z.writestr('real_estate_investment_advisor/MANIFEST.json',json.dumps(manifest,indent=2))
        with zipfile.ZipFile(target) as z:
            assert z.testzip() is None
            for r in records:
                data=z.read('real_estate_investment_advisor/'+r['path'])
                assert len(data)==r['bytes']
                assert hashlib.sha256(data).hexdigest()==r['sha256']
        summary={'archive':target.name,'files_with_verified_hashes':len(records),'archive_bytes':target.stat().st_size,'crc_check':'passed','sha256_check':'passed','archive_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
        (output/'package_verification.json').write_text(json.dumps(summary,indent=2))
        print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
