# Department submission guide

Project: Real Estate Investment Advisor

Submission prepared: 5 November 2026

## Submit these links and files

- Live application: https://real-estate-investment-advisor-purans07.streamlit.app/
- Complete source repository: https://github.com/purans07/Real-Estate-Investment-Advisor
- Complete project archive: real_estate_investment_advisor.zip
- Methodology and results: reports/project_report.md
- Twenty EDA analyses: reports/eda_findings.md
- Requirement coverage: reports/requirements_status.json
- Automated verification: reports/verification.json

The archive includes the original briefs, source data, processed data, split assignments, saved models, scripts, UI assets, dependency versions, reports and portable MLflow experiments. It excludes the local Python environment and credentials. Install the dependencies using Python 3.12 and launch app.py as described in README.md.

## Explain the project accurately

This is an educational capstone with an interactive property explorer, saved comparisons, a guided assessment, twenty EDA analyses and tracked classification/regression experiments.

Five-year regression learns the brief's permitted synthetic target: current price multiplied by 1.08 to the fifth power. Its small errors measure reproduction of an assumed formula. They do not validate future market prices.

Classification imitates the permitted rule that price per square foot at or below the training city/property-type median is a Good Investment. The model receives the corresponding price ratio. High accuracy measures agreement with that known rule, not independent evidence of profitability. The app shows the learned decision, exact screen and uncalibrated probability separately.

Historical transaction dates, crime rates, defined infrastructure scores and observed returns are absent from the supplied dataset. The linked Drive file was verified identical to the local CSV. These analyses remain explicitly data-limited. Do not claim full compliance with unavailable analyses without evaluator acceptance.

## Five minute demonstration

1. Open Discover and filter by city, price, property type, bedrooms and area.
2. Save two listings and compare their price and size.
3. Open a listing in Property desk. Confirm that the details are prefilled and city options follow the selected state.
4. Build an assessment. Explain the model screen, direct rule, probability and synthetic five-year regression.
5. Change the scenario rate to zero and rebuild. The separate five-year scenario equals the asking price.
6. Open Market atlas and inspect a question, its supporting table, location heatmap and assumed locality paths.
7. Open Method & evidence. Explain the test metrics, confusion matrix, model importance and missing-data limitations.

## Before uploading to the department portal

- Add your own name, student ID, department, guide and institution only where the department's form or report template requires them. These details have not been invented.
- Follow any department-specific cover sheet, report format, declaration or plagiarism-report requirements. No separate departmental template was supplied.
- Submit the current archive and links together. Confirm the live app opens before your demonstration; hosted apps may require startup time.
- Obtain the evaluator's acceptance of the stated data limitations if every literal brief item is mandatory.

The project is prepared for academic review and demonstration. It is not a validated commercial investment advisor, and department acceptance is determined by the evaluator.
