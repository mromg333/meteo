import matplotlib.pyplot as plt
import pandas as pd
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
df['Week'] = df['Date'].dt.to_period('W').dt.start_time



# Υποθέτω ότι η στήλη 'Date' είναι σε μορφή datetime, αν όχι, μετατρέπουμε:
df['Date'] = pd.to_datetime(df['Date'])

# Φιλτράρισμα θερμοκρασιών μεταξύ 0°C και 7.2°C για τον υπολογισμό των Ώρων Ψύχους
df['Chilling_Hours'] = df['Temperature'].apply(lambda x: 1 if 0 <= x <= 7.2 else 0)

# Ομαδοποίηση ανά μήνα (σύνολο και για τα 3 έτη)
chilling_hours_monthly = df.groupby(df['Date'].dt.month)['Chilling_Hours'].sum()

# Ομαδοποίηση ανά έτος
chilling_hours_yearly = df.groupby(df['Date'].dt.year)['Chilling_Hours'].sum()

# --- ΠΛΟΤ Ώρες Ψύχους ανά ΜΗΝΑ ---
plt.figure(figsize=(10, 5))
bars1 = plt.bar(chilling_hours_monthly.index, chilling_hours_monthly.values, color='blue')

# Προσθήκη τιμών πάνω από τις μπάρες
for bar in bars1:
    height = bar.get_height()
    if not np.isnan(height):
        plt.annotate(f'{height:.1f}',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3),
                     textcoords="offset points",
                     ha='center', va='bottom', fontsize=9)

plt.xlabel("Μήνας")
plt.ylabel("Συνολικές Ώρες Ψύχους")
plt.title("Chilling Hours Ανά Μήνα (Σύνολο για 2022-2024)")
plt.xticks(range(1, 13), ["Ιαν", "Φεβ", "Μαρ", "Απρ", "Μάι", "Ιουν", "Ιουλ", "Αυγ", "Σεπ", "Οκτ", "Νοε", "Δεκ"])
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# --- ΠΛΟΤ Ώρες Ψύχους ανά ΕΤΟΣ ---
plt.figure(figsize=(7, 5))
bars2 = plt.bar(chilling_hours_yearly.index, chilling_hours_yearly.values, color='blue')

# Προσθήκη τιμών πάνω από τις μπάρες
for bar in bars2:
    height = bar.get_height()
    if not np.isnan(height):
        plt.annotate(f'{height:.1f}',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3),
                     textcoords="offset points",
                     ha='center', va='bottom', fontsize=9)

plt.xlabel("Έτος")
plt.ylabel("Συνολικές Ώρες Ψύχους")
plt.title("Chilling Hours Ανά Έτος")
plt.xticks(chilling_hours_yearly.index)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()
