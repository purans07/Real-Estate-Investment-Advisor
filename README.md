# Real Estate Investment Advisor

Streamlit application for exploring the supplied housing data, applying a price-based investment screen and comparing assumed five-year price scenarios.

## Run locally

Use Python 3.12 and install `requirements.txt`, then run `streamlit run app.py`.

## Deployment

Choose this repository in Streamlit Community Cloud, use `app.py` as the entrypoint and select Python 3.12. The data and fitted models are included; training is not required for launch. Cloud installation and resource compatibility must be verified during deployment.

## Interpretation

The classifier evaluates a median-price proxy, not actual profitability. Test accuracy was approximately 71.3%. Regression did not beat a median-price baseline. Five-year values are calculated from an editable assumed growth rate, not observed future prices. Source fields contain physical inconsistencies documented in the app. No historical return, calibrated profit probability or net investment return is claimed.

This repository contains the running app assets. The complete project submission separately includes the original briefs, raw CSV, analysis scripts and experiment records. No data license is invented by this project.
