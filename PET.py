import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pyeto
from datetime import datetime

# --- ΣΤΑΘΕΡΕΣ ---
LATITUDE = 39.64
ALTITUDE = 85
T_BASE = 7
CSV_FILE = "2022_2025.csv"
COVERAGE_THRESHOLD = 0.7

# --- ΑΝΑΓΝΩΣΗ & ΠΡΟΕΤΟΙΜΑΣΙΑ ΔΕΔΟΜΕΝΩΝ ---
df = pd.read_csv(CSV_FILE, sep=',', encoding='utf-8', low_memory=False)

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
df['DOY'] = df['Date'].dt.dayofyear

numeric_cols = ['Temperature', 'Max_Temperature', 'Min_Temperature', 'Solar_Rad', 'Humidity', 'Wind_Speed', 'Pressure']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
df.dropna(subset=numeric_cols, inplace=True)

# --- GDD ---
df['GDD'] = np.maximum(0, (df['Max_Temperature'] + df['Min_Temperature']) / 2 - T_BASE)








def compute_pet_pyeto(row):
    try:
        tmean = row['Temperature']
        tmax = row['Max_Temperature']
        tmin = row['Min_Temperature']
        rh_mean = row['Humidity']
        wind = max(row['Wind_Speed'], 0.1)
        pressure = max(row['Pressure'] / 10.0, 9.0)
        doy = row['DOY']
        temp_diff = max(tmax - tmin, 0.1)

        delta = max(pyeto.delta_svp(tmean), 1e-6)
        psy = max(pyeto.psy_const(pressure), 1e-6)

        lat_rad = pyeto.deg2rad(LATITUDE)
        dr = 1 + 0.033 * np.cos(2 * np.pi / 365 * doy)
        solar_decl = 0.409 * np.sin(2 * np.pi / 365 * doy - 1.39)
        ws = np.arccos(-np.tan(lat_rad) * np.tan(solar_decl))
        ra = (24 * 60 / np.pi) * 0.0820 * dr * (
        ws * np.sin(lat_rad) * np.sin(solar_decl) +
        np.cos(lat_rad) * np.cos(solar_decl) * np.sin(ws)
        )

        if pd.notnull(row['Solar_Rad']) and row['Solar_Rad'] > 0:
            rs = float(row['Solar_Rad']) * 0.0864
        else:
            rs = 0.16 * np.sqrt(temp_diff) * ra

        rs = row['Solar_Rad'] * 0.0864 if pd.notnull(row['Solar_Rad']) and row['Solar_Rad'] > 0 else 0.16 * np.sqrt(temp_diff) * ra
        rns = pyeto.net_in_sol_rad(rs)
        es_tmax = pyeto.svp_from_t(tmax)
        es_tmin = pyeto.svp_from_t(tmin)
        es = (es_tmax + es_tmin) / 2
        ea = pyeto.avp_from_rhmean(es_tmin, es_tmax, rh_mean)
        rnl = pyeto.net_out_lw_rad(tmin, tmax, rs, ra, ea)
        rn = pyeto.net_rad(rns, rnl)

        return pyeto.fao56_penman_monteith(rn, tmean, wind, es, ea, delta, psy)

    except Exception as e:
        return np.nan


df['PET'] = df.apply(compute_pet_pyeto, axis=1)

df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month

# --- ΦΙΛΤΡΑΡΙΣΜΑ ΜΕ ΒΑΣΗ ΚΑΛΥΨΗ ---
def filter_by_coverage(data, group_cols, target_col, threshold):
    counts = data.groupby(group_cols).size()
    valid_counts = data.groupby(group_cols)[target_col].count()
    ratios = valid_counts / counts
    valid_keys = ratios[ratios >= threshold].index
    return data.set_index(group_cols).loc[valid_keys].reset_index()

df_valid_years = filter_by_coverage(df, ['Year'], 'PET', COVERAGE_THRESHOLD)
df_valid_months = filter_by_coverage(df, ['Year', 'Month'], 'PET', COVERAGE_THRESHOLD)

# --- ΟΜΑΔΟΠΟΙΗΣΗ ΔΕΔΟΜΕΝΩΝ ---
annual_data = df_valid_years.groupby('Year')[['GDD', 'PET']].mean().reset_index()
monthly_data = df_valid_months.groupby('Month')[['GDD', 'PET']].mean().reset_index()

# --- ΟΠΤΙΚΟΠΟΙΗΣΗ ---
def plot_bar_comparison(x_labels, data1, data2, label1, label2, title, xlabel):
    width = 0.4
    x = np.arange(len(x_labels))
    plt.figure(figsize=(10, 5))
    bars1 = plt.bar(x - width/2, data1, width=width, color='orange', label=label1)
    bars2 = plt.bar(x + width/2, data2, width=width, color='dodgerblue', label=label2)

    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if not np.isnan(height):
                plt.annotate(f'{height:.1f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom', fontsize=9)

    plt.xlabel(xlabel)
    plt.title(title)
    plt.xticks(x, x_labels)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

# Ετήσιο γράφημα
plot_bar_comparison(
    annual_data['Year'], 
    annual_data['GDD'], 
    annual_data['PET'], 
    'GDD', 'PET',
    "Ετήσια Μέση Τιμή GDD και PET (φίλτρο κάλυψης 70%)", 
    "Έτος"
)

# Μηνιαίο γράφημα
plot_bar_comparison(
    monthly_data['Month'], 
    monthly_data['GDD'], 
    monthly_data['PET'], 
    'GDD', 'PET',
    "Μηνιαία Μέση Τιμή GDD και PET (μέσος valid ετών, φίλτρο 70%)", 
    "Μήνας"
)