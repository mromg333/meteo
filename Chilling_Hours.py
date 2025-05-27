import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
sys.stdout.reconfigure(encoding='utf-8')

csv_file = "2022_2025.csv"
df = pd.read_csv(csv_file, sep=',', encoding='utf-8', header=0, low_memory=False, na_values=["", " ", "N/A", "null", "-", "missing"])

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
df['Hour'] = df['Date'].dt.floor('h')

hourly_avg_temp = df.groupby('Hour')['Temperature'].mean()
hourly_avg_temp = hourly_avg_temp.dropna()
print(f"Αγνοήθηκαν {hourly_avg_temp.isna().sum()} NaN τιμές στη μέση ωριαία θερμοκρασία.")


chilling_hours = hourly_avg_temp.apply(lambda x: 1 if 0 <= x <= 7.2 else 0)
chilling_hours = chilling_hours.to_frame(name='Chilling_Hour')
chilling_hours['Date'] = chilling_hours.index

chilling_hours['Month'] = chilling_hours['Date'].dt.month
chilling_hours_monthly = chilling_hours.groupby('Month')['Chilling_Hour'].sum()

plt.figure(figsize=(10, 5))
bars_month = plt.bar(chilling_hours_monthly.index, chilling_hours_monthly.values, color='teal')

for bar in bars_month:
    height = bar.get_height()
    plt.annotate(f'{height:.0f}',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3),
                 textcoords="offset points",
                 ha='center', va='bottom', fontsize=9)

plt.xlabel("Μήνας")
plt.ylabel("Συνολικές Ώρες Ψύχους")
plt.title("Ώρες Ψύχους Ανά Μήνα (Σύνολο για όλα τα έτη)")
plt.xticks(range(1, 13), ["Ιαν", "Φεβ", "Μαρ", "Απρ", "Μάι", "Ιουν", "Ιουλ", "Αυγ", "Σεπ", "Οκτ", "Νοε", "Δεκ"])
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

def assign_season_year(date):
    if date.month >= 9:
        return f"{date.year}-{date.year + 1}"
    else:
        return f"{date.year - 1}-{date.year}"

chilling_hours['Season'] = chilling_hours['Date'].apply(assign_season_year)
chilling_hours_by_season = chilling_hours.groupby('Season')['Chilling_Hour'].sum()
chilling_hours_by_season = chilling_hours_by_season[chilling_hours_by_season >= 500]


plt.figure(figsize=(8, 5))
bars_season = plt.bar(chilling_hours_by_season.index, chilling_hours_by_season.values, color='blue')

for bar in bars_season:
    height = bar.get_height()
    plt.annotate(f'{height:.0f}',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3),
                 textcoords="offset points",
                 ha='center', va='bottom', fontsize=9)


vars = {
    "Maria Bianca": 908,
    "Lolita": 559,
    "Plagold10": 446
}


for name, chill_req in vars.items():
    plt.axhline(y=chill_req, linestyle='--', linewidth=1.2, color='black')
    plt.text(
        x=len(chilling_hours_by_season.index) - 0.5,
        y=chill_req + 10,
        s=f"{name}: {chill_req} ώρες",
        color='black',
        fontsize=9,
        ha='right',
        va='bottom',
        alpha=0.7
    )

plt.xlabel("Σύνολο Ώρων Ψύχους για κάθε Χειμερινή Περίοδο ")
plt.ylabel("Συνολικές Ώρες Ψύχους")
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.title("Χειμερινoί Περίοδοι")
plt.tight_layout()
plt.show()

