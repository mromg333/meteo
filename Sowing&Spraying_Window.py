import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
sys.stdout.reconfigure(encoding='utf-8')
csv_file = "2022_2025.csv"
df = pd.read_csv(csv_file, sep=',', encoding='utf-8', header=0, low_memory=False)

columns_map = {
    'Timestamp[s]': 'Unix_time',
    'Temp_Out[degC]': 'Temperature',
    'THWS_Index[degC]': 'Feels_Like',
    'Wind_Speed[m/s]': 'Wind_Speed'
}
df.rename(columns=columns_map, inplace=True)

cols_to_convert = ['Unix_time', 'Temperature', 'Feels_Like', 'Wind_Speed']
for col in cols_to_convert:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna(subset=cols_to_convert)

df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute']])
df.sort_values('Date', inplace=True)
df.reset_index(drop=True, inplace=True)

df['Rain[mm]'] = pd.to_numeric(df['Rain[mm]'], errors='coerce').fillna(0)
df['Hum_Out[%]'] = pd.to_numeric(df['Hum_Out[%]'], errors='coerce').fillna(0)

def calculate_soil_moisture(df):
    soil_moisture = np.full(len(df), 50.0)
    increase_factor = 3      
    decrease_factor = 0.98 
    temp_factor = 0.08       
    wind_factor = 0.04     
    hum_factor = 0.03       

    for i in range(1, len(df)):
        rain_value = df.at[i-1, "Rain[mm]"]
        hum_value = df.at[i-1, "Hum_Out[%]"]
        rain_effect = min(100, soil_moisture[i-1] + rain_value * increase_factor)
        temp_effect = df.at[i-1, "Temperature"] * temp_factor
        wind_effect = df.at[i-1, "Wind_Speed"] * wind_factor
        hum_effect = hum_value * hum_factor
        decay_effect = max(5, soil_moisture[i-1] * (decrease_factor - temp_effect - wind_effect + hum_effect))
        soil_moisture[i] = min(100, max(0, rain_effect if rain_value > 0 else decay_effect))
    df["Soil_Moisture"] = soil_moisture
    return df

def determine_sowing_spraying_periods(df):
    df['Sowing_Condition'] = np.where(
        (df['Soil_Moisture'] >= 40) &
        (df['Soil_Moisture'] <= 75) &
        (df['Temperature'] >= 10) &
        (df['Temperature'] <= 28) &
        (df['Hum_Out[%]'] > 35),
        'Κατάλληλο', 'Ακατάλληλο'
    )
    df['Spraying_Condition'] = np.where(
        (df['Soil_Moisture'] < 70) &
        (df['Wind_Speed'] < 6) &
        (df['Hum_Out[%]'] > 35),
        'Κατάλληλο', 'Ακατάλληλο'
    )
    return df

df = calculate_soil_moisture(df)
df = determine_sowing_spraying_periods(df)

df['Date_only'] = pd.to_datetime(df['Date'].dt.date)

df['Valid_Sowing'] = (df['Sowing_Condition'] == 'Κατάλληλο').astype(int)
df['Valid_Spraying'] = (df['Spraying_Condition'] == 'Κατάλληλο').astype(int)


valid_sowing_days_year = df[df['Sowing_Condition'] == 'Κατάλληλο'].groupby(df['Date_only'].dt.year)['Date_only'].nunique()
valid_spraying_days_year = df[df['Spraying_Condition'] == 'Κατάλληλο'].groupby(df['Date_only'].dt.year)['Date_only'].nunique()


sowing_valid_days_month = {m: 0 for m in range(1, 13)}
spraying_valid_days_month = {m: 0 for m in range(1, 13)}

for _, group in df.groupby(['Year', 'Month']):
    unique_sowing_days = group[group['Valid_Sowing'] == 1]['Date_only'].nunique()
    unique_spraying_days = group[group['Valid_Spraying'] == 1]['Date_only'].nunique()
    month = group['Month'].iloc[0]
    max_days_in_month = pd.to_datetime(f"{group['Year'].iloc[0]}-{month}-01").days_in_month
    sowing_valid_days_month[month] = min(unique_sowing_days, max_days_in_month)
    spraying_valid_days_month[month] = min(unique_spraying_days, max_days_in_month)

months_labels = ['Ιαν', 'Φεβ', 'Μαρ', 'Απρ', 'Μαϊ', 'Ιουν', 'Ιουλ', 'Αυγ', 'Σεπ', 'Οκτ', 'Νοε', 'Δεκ']
x = np.arange(12)
width = 0.35

plt.figure(figsize=(10,6))
plt.bar(x - width/2, [sowing_valid_days_month[m] for m in range(1,13)], width,
        label='Σπορά', color='skyblue')
plt.bar(x + width/2, [spraying_valid_days_month[m] for m in range(1,13)], width,
        label='Ψεκασμός', color='lightcoral')
plt.xticks(x, months_labels)
plt.xlabel('Μήνας')
plt.ylabel('Αριθμός Ημερών')
plt.title('Κατάλληλες ημέρες ανά μήνα')
plt.legend()
plt.tight_layout()
plt.show()

years = valid_sowing_days_year.index.tolist()
x_year = np.arange(len(years))

plt.figure(figsize=(10,6))
plt.bar(x_year - width/2, valid_sowing_days_year.values, width,
        label='Σπορά', color='skyblue')
plt.bar(x_year + width/2, valid_spraying_days_year.values, width,
        label='Ψεκασμός', color='lightcoral')
plt.xticks(x_year, years)
plt.xlabel('Έτος')
plt.ylabel('Αριθμός Ημερών')
plt.title('Κατάλληλες ημέρες ανά έτος')
plt.legend()
plt.tight_layout()
plt.show()
