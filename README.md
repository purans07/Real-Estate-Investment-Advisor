# Real Estate Investment Advisor

A capstone implementation based on both supplied Real Estate Investment Advisor briefs. It includes full data preparation, twenty EDA analyses, investment classification, five-year price regression, MLflow tracking and registration, and a Streamlit app.

Five-year targets are synthetic fixed-rate scenarios at the brief's example 8 percent annual growth. Classification imitates the allowed training-cohort median price rule. Strong scores measure agreement with these formula-based labels, not observed market forecasts or realized profits.

## Property Studio interface

The app uses an editorial ivory and forest-green design with four workspaces: Discover, Property desk, Market atlas, and Method & evidence. Discover provides listing cards, saved comparisons and full-data downloads. Opening a listing prefills the assessment. State and city choices stay consistent, advanced details are collapsible, and results persist across navigation. All 20 EDA analyses and the original methodological disclosures remain available. Architectural drawings are illustrations, not actual listing photos. Saved listings are held only in the current browser session.

Design assets are in `assets/` and the Streamlit theme is in `.streamlit/config.toml`. Both must be included when deploying.

## Run the included app

Use Python 3.12, matching the verified environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Data and models are included; retraining is not needed to launch. Use only trusted model artifacts from this project.

## Reproduce all phases

```sh
.venv/bin/python src/phase1_audit.py
.venv/bin/python src/phase2_eda.py
.venv/bin/python src/phase2_enrich.py
.venv/bin/python src/phase3_train.py
.venv/bin/python src/phase6_verify.py
.venv/bin/python src/export_experiments.py
.venv/bin/python src/write_report.py
.venv/bin/python src/package_submission.py
```

The 60/20/20 split uses seed 42. Preprocessing and city/type medians are fitted only on training rows. Validation selects candidates and test data supplies final metrics. All original source values remain unchanged; inconsistent floors and outliers are flagged. Price per square foot is recomputed in rupees, and ages retain the source reference year 2025.

## Targets

`Future_Price_5Y = Price_in_Lakhs * 1.08 ** 5`. Regression legitimately includes current price when learning this assumed future-price formula. No historical price appreciation is inferred. The app shows the learned eight-percent prediction and a separate editable-rate scenario.

`Good_Investment = asking_price_per_sqft <= training_city_type_median`. The classifier receives the price-to-median ratio and deliberately imitates this rule. It displays its own Yes/No result and probability separately from the directly computed rule. The probability is uncalibrated and is not the chance of a profitable investment. These target definitions are permitted alternatives in the DS AI ML brief; they do not constitute independent financial validation.

## Analysis and experiment records

- [Current methodology and findings](reports/project_report.md)
- [All twenty EDA questions with explanations and visuals](reports/eda_findings.md)
- [Requirement status and outstanding dependencies](reports/requirements_status.json)
- [Verification results](reports/verification.json)
- [Deployment and demonstration](DEPLOYMENT.md)
- `data/processed/model_targets.csv`: split assignment and labeled targets for every property.
- `experiments/manifest.json`: portable run parameters, metrics, original IDs and model locations.

Restore the exported current experiments on any compatible machine:

```sh
.venv/bin/python src/restore_experiments.py
.venv/bin/python -m mlflow ui --backend-store-uri sqlite:///restored_mlflow.db
```

Or inspect newly trained local experiments with `mlflow ui --backend-store-uri sqlite:///mlflow.db`. The original machine's database is not required by the app or the portable restoration.

## Data dependencies and completion status

No transaction dates, observed returns, crime rates, defined infrastructure scores or geographic coordinates were supplied. Historical trends, crime effects and actual infrastructure/resale relationships remain blocked on additional data. The top-locality chart is an assumed projection and the location heatmap aggregates categories rather than inventing coordinates. No geographic school density is claimed. The documents provide no numerical cutoff for high accuracy or low RMSE. Synthetic-target scores must not be presented as proof of investment forecasting skill.

Public deployment is verified at [https://real-estate-investment-advisor-purans07.streamlit.app/](https://real-estate-investment-advisor-purans07.streamlit.app/). A live property assessment returned classification and five-year regression successfully; see reports/public_deployment_check.json. Missing real-world input data still prevents a 100 percent claim.

## Ten day delivery plan

| Day | Work |
|---|---|
| 1 | Read briefs and audit schema and units |
| 2 | Prepare data, flags and features |
| 3 | EDA price, size and location questions |
| 4 | EDA amenities, services, ownership and limitations |
| 5 | Define assumed targets and split data |
| 6 | Train and evaluate classification and regression |
| 7 | MLflow tracking, registry and portable exports |
| 8 | Streamlit inputs, filters and analysis views |
| 9 | Verify calculations, app interactions and artifacts |
| 10 | Complete GitHub handover, hosting and demonstration |

This is the briefs' requested planning framework, not a fabricated record of ten elapsed days. No dataset redistribution license is invented.
