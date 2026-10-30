# Deploy the Real Estate Investment Advisor

The app has been extended to the briefs’ assumed Future_Price_5Y target. Public hosting remains pending sign-in and verification. The submission ZIP includes source data, analysis outputs, trained models, experiment records and the application. Extract it before running commands.

## Run the submitted app

Use Python 3.12, which matches the training environment. In the extracted project folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

The saved data and models are included, so training is not required to launch the app. The full requirements file records the tested environment. This is a complete source submission, including src/, EDA outputs, labeled targets, and portable experiments/. Model files must come from this trusted project package.

## Publish with Streamlit Community Cloud

1. Create a GitHub repository in your account and upload the extracted project files. Include `app.py`, `requirements.txt`, `data/processed/housing_audited.csv`, `models/`, and `reports/`. The raw CSV and source scripts are needed for retraining, but the supplied Word briefs are not needed for the running app.
2. Keep `.venv/`, temporary files, local caches, the ZIP itself and local experiment storage out of the repository. The included `.gitignore` already excludes the environment and experiment storage.
3. Sign in to Streamlit Community Cloud with the account that can access that repository.
4. Choose **Create app**, select the repository and branch, and set the entrypoint to `app.py`.
5. In advanced settings select Python 3.12 if available. Keep the saved model's scikit-learn and NumPy versions aligned with the included requirements. If that Python version is unavailable, validate a new environment and retrain before publishing.
6. Deploy and inspect the build logs. Test the published version using the demonstration below. Hosting compatibility and available resources still need to be checked on the actual platform.

No account credentials or secrets are required by this app. Uploading a public repository or deploying the app makes its included data accessible; select repository access appropriate to your permission to share the supplied dataset.

Official instructions: [Deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [Declare dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

## Experiment records after moving the project

The portable experiments/ export contains the current six runs and models. Run src/restore_experiments.py to recreate them in restored_mlflow.db with paths for the current machine. The ZIP also includes a snapshot of mlflow.db and mlruns/ for historical context. MLflow records can contain absolute paths from the original workspace. After extracting elsewhere, the app still loads the independent models in `models/`; some historical MLflow artifact links may point to the original workspace. To create experiments with paths for the new machine, run `src/phase3_train.py` there using the setup in the README. This produces new runs and registered versions rather than rewriting the historical records.

## Submission demonstration

1. Explain the problem: explore listings, apply a price-based investment screen and compare five-year scenarios.
2. Show the data-quality results: 250,000 rows and 116,304 floor inconsistencies, with raw values preserved.
3. In **Explore properties**, choose Chennai, adjust the budget and BHK filters, and show the matching listings.
4. In **Assess a property**, select Tamil Nadu and Chennai, enter property details and an asking price, then assess it.
5. Explain that the direct investment screen compares asking price per square foot with a training-cohort median. The classifier predicts this proxy using the known rule ratio, not realized profit. Its Yes/No and probability are distinct from the exact screening rule.
6. Change the annual scenario rate from 8% to 0% and reassess. At 0%, the five-year price equals the asking price. This is a scenario calculation, not evidence of future appreciation.
7. In **Data and model quality**, show the baseline comparison. Regression did not beat the median baseline; classification accuracy was about 71.3% on the defined proxy.
8. Show the report and MLflow records. State that observed future prices and returns would be required to validate a real investment forecasting model.

## Submission contents

- `README.md` and this guide: setup, phases and demonstration.
- `app.py` and `src/`: application and reproducible analysis scripts.
- Original source files and `data/processed/`: source and audited dataset.
- `models/`: saved pipelines, thresholds, feature weights and metadata.
- `reports/`: findings, EDA tables, chart and verification outcomes.
- `mlflow.db` and `mlruns/`: local experiment snapshot.
- `MANIFEST.json`: packaged file sizes and SHA-256 hashes.

Local tests do not establish cloud deployment success. The public URL is available only after deployment in a hosting account.
