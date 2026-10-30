"""Answer the 20 brief questions using cross-sectional data, not time trends."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

def main():
    d = pd.read_csv(ROOT/'data/processed/housing_audited.csv')
    out = ROOT/'reports/eda'
    out.mkdir(parents=True, exist_ok=True)
    p = 'Calculated_Price_per_SqFt_INR'
    q1,q3=d.Size_in_SqFt.quantile([.25,.75])
    d['Flag_Size_IQR']=(d.Size_in_SqFt<q1-1.5*(q3-q1))|(d.Size_in_SqFt>q3+1.5*(q3-q1))
    tables = {
        '01_price_distribution': d.Price_in_Lakhs.describe(percentiles=[.01,.25,.5,.75,.99]).to_frame(),
        '02_size_distribution': d.Size_in_SqFt.describe(percentiles=[.01,.25,.5,.75,.99]).to_frame(),
        '03_price_per_sqft_by_type': d.groupby('Property_Type')[p].agg(['count','mean','median']),
        '04_size_price_correlation': d[['Size_in_SqFt','Price_in_Lakhs']].corr(),
        '05_outliers': d[['Flag_Price_per_SqFt_IQR','Flag_Size_IQR','Flag_Floor_Above_Total']].sum().to_frame('count'),
        '06_state_price_per_sqft': d.groupby('State')[p].agg(['count','mean','median']),
        '07_city_price': d.groupby('City').Price_in_Lakhs.agg(['count','mean','median']),
        '08_locality_age': d.groupby(['State','City','Locality']).Age_of_Property.agg(['count','median']),
        '09_city_bhk': pd.crosstab(d.City,d.BHK),
        '10_expensive_localities': d.groupby(['State','City','Locality']).Price_in_Lakhs.agg(['count','mean','median']).query('count >= 10').nlargest(5,'mean'),
        '11_numeric_correlations': d.drop(columns=['ID','Price_per_SqFt','Year_Built','Implied_Reference_Year']).select_dtypes('number').corr(),
        '12_schools': d.groupby('Nearby_Schools')[p].agg(['count','mean','median']),
        '13_hospitals': d.groupby('Nearby_Hospitals')[p].agg(['count','mean','median']),
        '14_furnishing': d.groupby('Furnished_Status').Price_in_Lakhs.agg(['count','mean','median']),
        '15_facing': d.groupby('Facing')[p].agg(['count','mean','median']),
        '16_owner': d.Owner_Type.value_counts().to_frame('count'),
        '17_availability': d.Availability_Status.value_counts().to_frame('count'),
        '18_parking': d.groupby('Parking_Space').Price_in_Lakhs.agg(['count','mean','median']),
        '19_amenities': d.groupby('Amenities_Normalized')[p].agg(['count','mean','median']),
        '20_transport': d.groupby('Public_Transport_Accessibility')[p].agg(['count','mean','median']),
    }
    for name, table in tables.items():
        table.to_csv(out/f'{name}.csv')
    fig, axes = plt.subplots(2,2,figsize=(12,8))
    d.Price_in_Lakhs.hist(bins=40,ax=axes[0,0],color='#176b87')
    axes[0,0].set(xlabel='Price (INR lakhs)',ylabel='Properties',title='Price distribution')
    d.Size_in_SqFt.hist(bins=40,ax=axes[0,1],color='#176b87')
    axes[0,1].set(xlabel='Area (sq ft)',ylabel='Properties',title='Area distribution')
    sample=d.sample(min(3000,len(d)),random_state=42)
    axes[1,0].scatter(sample.Size_in_SqFt,sample.Price_in_Lakhs,s=3,alpha=.2)
    axes[1,0].set(xlabel='Area (sq ft)',ylabel='Price (INR lakhs)',title='Area and price')
    tables['07_city_price']['mean'].nlargest(10).sort_values().plot.barh(ax=axes[1,1],color='#176b87')
    axes[1,1].set(xlabel='Mean price (INR lakhs)',title='Cities with highest mean prices')
    fig.tight_layout()
    fig.savefig(out/'overview.png',dpi=160)
    plt.close(fig)
    print('Saved 20 EDA tables and overview chart.')

if __name__=='__main__':
    main()
