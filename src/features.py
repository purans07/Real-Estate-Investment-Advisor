"""Feature and target definitions shared by training, evaluation and the app."""
import pandas as pd
BASE_NUM=['BHK','Size_in_SqFt','Age_of_Property','Nearby_Schools','Nearby_Hospitals','Amenity_Count']
CAT=['State','City','Property_Type','Furnished_Status','Public_Transport_Accessibility','Parking_Space','Security','Facing','Owner_Type','Availability_Status']
RATE=.08
FACTOR=(1+RATE)**5
REG_NUM=BASE_NUM+['Price_in_Lakhs']
CLF_NUM=BASE_NUM+['Price_to_Cohort_Median']

def enrich(frame,thresholds,fallback):
    f=frame.copy()
    if isinstance(thresholds,pd.DataFrame):
        thresholds=thresholds.set_index(['City','Property_Type']).Training_Median_Price_per_SqFt_INR
    med=pd.Series(f.set_index(['City','Property_Type']).index.map(thresholds),index=f.index).fillna(fallback).astype(float)
    f['Cohort_Median_Price_per_SqFt_INR']=med
    f['Calculated_Price_per_SqFt_INR']=f.Price_in_Lakhs*100000/f.Size_in_SqFt
    f['Price_to_Cohort_Median']=f.Calculated_Price_per_SqFt_INR/med
    return f
