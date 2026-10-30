"""Read the full source, preserve raw fields, and produce a reproducible quality audit."""
from pathlib import Path
import json
import pandas as pd
import numpy as np
ROOT = Path(__file__).resolve().parents[1]

def main():
    df = pd.read_csv(ROOT / "india_housing_prices.csv")
    source_columns = list(df.columns)
    expected = df.Price_in_Lakhs * 100000 / df.Size_in_SqFt
    df["Calculated_Price_per_SqFt_INR"] = expected
    df["Flag_Floor_Above_Total"] = df.Floor_No > df.Total_Floors
    df["Implied_Reference_Year"] = df.Year_Built + df.Age_of_Property
    # Original units and ages are preserved. There is no verified observation date.
    df["Amenities_Normalized"] = df.Amenities.fillna("").map(lambda x: ", ".join(sorted(set(a.strip() for a in x.split(",") if a.strip()))))
    df["Amenity_Count"] = df.Amenities_Normalized.map(lambda x: len(x.split(", ")) if x else 0)
    df["Schools_per_1000_SqFt"] = df.Nearby_Schools / df.Size_in_SqFt * 1000
    q1, q3 = expected.quantile([.25, .75])
    df["Flag_Price_per_SqFt_IQR"] = (expected < q1 - 1.5*(q3-q1)) | (expected > q3 + 1.5*(q3-q1))
    metrics = {
        "rows":len(df), "source_columns":len(source_columns),
        "missing_by_column":df[source_columns].isna().sum().to_dict(),
        "duplicate_rows":int(df[source_columns].duplicated().sum()),
        "duplicate_ids":int(df.ID.duplicated().sum()),
        "duplicate_rows_excluding_id":int(df[[c for c in source_columns if c != "ID"]].duplicated().sum()),
        "floor_above_total":int(df.Flag_Floor_Above_Total.sum()),
        "implied_reference_year_counts":{str(k):int(v) for k,v in df.Implied_Reference_Year.value_counts().items()},
        "provided_price_matches_lakhs_per_sqft_rounded":int(np.isclose(df.Price_per_SqFt, (df.Price_in_Lakhs/df.Size_in_SqFt).round(2)).sum()),
        "nonpositive_size_or_price":int(((df.Size_in_SqFt<=0)|(df.Price_in_Lakhs<=0)).sum()),
        "price_per_sqft_iqr_flags":int(df.Flag_Price_per_SqFt_IQR.sum()),
        "states":int(df.State.nunique()), "cities":int(df.City.nunique()),
        "locality_labels":int(df.Locality.nunique()),
        "price_size_correlation":float(df.Price_in_Lakhs.corr(df.Size_in_SqFt)),
        "numeric_summary":df.select_dtypes(include="number").describe().to_dict(),
        "categories":{c:df[c].value_counts().to_dict() for c in df.select_dtypes(include="object") if df[c].nunique()<30},
    }
    (ROOT/"reports").mkdir(exist_ok=True)
    (ROOT/"data/processed").mkdir(parents=True, exist_ok=True)
    (ROOT/"reports/phase1_audit.json").write_text(json.dumps(metrics,indent=2))
    df.to_csv(ROOT/"data/processed/housing_audited.csv",index=False)
    pd.DataFrame({"column":source_columns,"dtype":[str(df[c].dtype) for c in source_columns],"missing":[int(df[c].isna().sum()) for c in source_columns],"unique":[int(df[c].nunique()) for c in source_columns]}).to_csv(ROOT/"reports/data_dictionary.csv",index=False)
    print(json.dumps({k:v for k,v in metrics.items() if k not in ("numeric_summary","categories","missing_by_column")},indent=2))

if __name__ == "__main__":
    main()
