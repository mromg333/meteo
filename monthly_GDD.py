import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

LATITUDE, ALTITUDE, T_BASE = 39.64, 85, 7
csv_file = "2022_2025.csv"
df = pd.read_csv(csv_file, sep=',', encoding='utf-8', low_memory=False)

df.rename(columns={
    'Timestamp[s]': 'Unix_time', 'Temp_Out[degC]': 'Temperature',
    'Hi_Temp[degC]': 'Max_Temperature', 'Low_Temp[degC]': 'Min_Temperature',
    'Hum_Out[%]': 'Humidity', 'Solar_Rad[W/m2]': 'Solar_Rad',
    'Wind_Speed[m/s]': 'Wind_Speed', 'Pressure[mbar]': 'Pressure'
}, inplace=True)

df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute']])
df['Year'], df['Month'] = df['Date'].dt.year, df['Date'].dt.month
numeric_cols = ['Max_Temperature', 'Min_Temperature', 'Solar_Rad', 'Wind_Speed', 'Humidity', 'Pressure']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
df.dropna(subset=numeric_cols, inplace=True)

df['GDD'] = np.maximum(0, (df['Max_Temperature'] + df['Min_Temperature']) / 2 - T_BASE)

def calculate_pet(row):
    if pd.isna(row['Temperature']) or pd.isna(row['Solar_Rad']) or pd.isna(row['Wind_Speed']) or pd.isna(row['Humidity']):
        return np.nan
    return max(0, 0.408 * row['Solar_Rad'])

df['PET'] = df.apply(calculate_pet, axis=1)

annual_data = df.groupby('Year')[['GDD', 'PET']].mean().reset_index()
monthly_data = df.groupby('Month')[['GDD', 'PET']].mean().reset_index()

x = np.arange(len(annual_data['Year']))
width = 0.4

plt.figure(figsize=(10, 5))
bars1 = plt.bar(x - width/2, annual_data['GDD'], width=width, color='orange', label='GDD')
bars2 = plt.bar(x + width/2, annual_data['PET'], width=width, color='dodgerblue', label='PET')

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        if not np.isnan(height):
            plt.annotate(f'{height:.1f}', xy=(bar.get_x() + bar.get_width() / 2, height), 
                         xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

plt.xlabel("Έτος")
plt.ylabel("Μέσες Τιμές")
plt.title("Ετήσια Συσσώρευση GDD και PET")
plt.xticks(x, annual_data['Year'])
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

x = np.arange(len(monthly_data['Month']))
width = 0.4

plt.figure(figsize=(10, 5))
bars3 = plt.bar(x - width/2, monthly_data['GDD'], width=width, color='orange', label='GDD')
bars4 = plt.bar(x + width/2, monthly_data['PET'], width=width, color='dodgerblue', label='PET')

for bars in [bars3, bars4]:
    for bar in bars:
        height = bar.get_height()
        if not np.isnan(height):
            plt.annotate(f'{height:.1f}', xy=(bar.get_x() + bar.get_width() / 2, height), 
                         xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

plt.xlabel("Μήνας")
plt.ylabel("Μέσες Τιμές")
plt.title("Μηνιαία Συσσώρευση GDD και PET")
plt.xticks(x, [f'{m}' for m in monthly_data['Month']], rotation=45)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()
