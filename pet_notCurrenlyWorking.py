import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pyet

LATITUDE = 39.64
ALTITUDE = 85
T_BASE = 7

csv_file = "2022_2025.csv"
df = pd.read_csv(csv_file, sep=',', encoding='utf-8', low_memory=False)

# Μετονομασία στηλών για ευκολία
df.rename(columns={
    'Temp_Out[degC]': 'Temperature',
    'Hi_Temp[degC]': 'Max_Temperature',
    'Low_Temp[degC]': 'Min_Temperature',
    'Hum_Out[%]': 'Humidity',
    'Solar_Rad[W/m2]': 'Solar_Rad',
    'Wind_Speed[m/s]': 'Wind_Speed',
    'Pressure[mbar]': 'Pressure'
}, inplace=True)

df.drop(columns=['Date'], inplace=True)  
df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute']])

numeric_cols = ['Temperature', 'Max_Temperature', 'Min_Temperature', 'Solar_Rad', 'Humidity', 'Wind_Speed', 'Pressure']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

df.dropna(subset=numeric_cols, inplace=True)

# Υπολογισμός GDD
df['GDD'] = np.maximum(0, (df['Max_Temperature'] + df['Min_Temperature']) / 2 - T_BASE)

def compute_pet(row):
    try:
        Rs = 0 if pd.isnull(row['Solar_Rad']) or row['Solar_Rad'] == 0 else row['Solar_Rad'] * 0.0864
        print(f"Computing PET for row at {row['Date']}")
        print(f"tmean={row['Temperature']}, tmax={row['Max_Temperature']}, tmin={row['Min_Temperature']}, rs={Rs}, rh={row['Humidity']}, wind={row['Wind_Speed']}, pressure={row['Pressure'] / 10}")
        PET = pyet.pm_fao56(
            tmean=row['Temperature'],
            tmax=row['Max_Temperature'],
            tmin=row['Min_Temperature'],
            rs=Rs,
            rh=row['Humidity'],
            wind=row['Wind_Speed'],
            elevation=ALTITUDE,
            pressure=row['Pressure'] / 10  # mbar -> kPa
        )
        return PET
    except Exception as e:
        print(f"Error at {row['Date']}: {e}")
        return np.nan


df['PET'] = df.apply(compute_pet, axis=1)

df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month

annual_data = df.groupby('Year')[['GDD', 'PET']].mean().reset_index()
monthly_data = df.groupby(['Year', 'Month'])[['GDD', 'PET']].mean().reset_index()

# Γράφημα Ετήσιο
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
plt.title("Ετήσια Μέση Τιμή GDD και PET")
plt.xticks(x, annual_data['Year'])
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# Γράφημα Μηνιαίο
x = np.arange(len(monthly_data['Month']))
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
plt.title("Μηνιαία Μέση Τιμή GDD και PET")
plt.xticks(x, [f'{m}' for m in monthly_data['Month']], rotation=45)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

print(df[['Date', 'Temperature', 'Max_Temperature', 'Min_Temperature', 'Solar_Rad', 'Humidity', 'Wind_Speed', 'Pressure', 'PET']].head(20))
