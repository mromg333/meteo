import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys
import pyet

sys.stdout.reconfigure(encoding='utf-8')

# Φόρτωση δεδομένων
df = pd.read_csv("https://greendigital.uth.gr/data/prediction.csv", encoding='utf-8')

# Μετατροπή χρόνου
df['Date'] = pd.to_datetime(df['DateTime'])

# Μετονομασίες στηλών για ευκολία
df = df.rename(columns={
    'Temp_Out[degC]': 'Temperature',
    'Wind_Speed[m/s]': 'Wind_Speed',
    'TotPrec[mm]': 'Rain[mm]',
    'RelHum[%]': 'Hum_Out[%]'
})

# Μετατροπή σε αριθμητικές τιμές
df['Rain[mm]'] = pd.to_numeric(df['Rain[mm]'], errors='coerce').fillna(0)
df['Hum_Out[%]'] = pd.to_numeric(df['Hum_Out[%]'], errors='coerce').fillna(0)
df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
df['Wind_Speed'] = pd.to_numeric(df['Wind_Speed'], errors='coerce')

# Πίεση σε kPa
df['Pressure[Pa]'] = df['Pressure[Pa]'].fillna(101300)  # συμπλήρωση ελλειπόντων με τυπική πίεση
df['Pressure_kPa'] = df['Pressure[Pa]'] / 1000

# Ημερολογιακές πληροφορίες
df['doy'] = df['Date'].dt.dayofyear  # day of year

# Αφαίρεση σειρών με NaN σε σημαντικά πεδία
df = df.dropna(subset=['Temperature', 'Wind_Speed'])

# Μετατροπή ακτινοβολίας σε MJ/m²/h (από W/m²)
df['Rn'] = df['GHI[W/m2]'] * 3600 / 1e6
df['Rn'] = df['Rn'].fillna(0)

# Ορισμός γεωγραφικών στοιχείων
latitude_deg = 39.63
altitude = 70

# Υπολογισμός PET vectorized με pyet.pm_fao56
df['PET'] = pyet.pm_fao56(
    tmean=df['Temperature'],
    wind=df['Wind_Speed'],
    rn=df['Rn'],
    rh=df['Hum_Out[%]'],
    elevation=altitude,
    pressure=df['Pressure_kPa']
)


# Ορισμός ranges καταλληλότητας PET για ποικιλίες ροδάκινου
varieties_pet = {
    "Red Haven": {
        'PET': [
            (0, 2),   # Unsuitable
            (2.1, 5), # Moderate
            (5.1, 10)  # Suitable
        ]
    },
    "Maria Bianca": {
        'PET': [
            (0, 1.5),
            (1.6, 4.5),
            (4.6, 9)
        ]
    },
    "Honey Dew Hale": {
        'PET': [
            (0, 2.5),
            (2.6, 5.5),
            (5.6, 11)
        ]
    }
}

# Συνάρτηση αξιολόγησης καταλληλότητας PET
def rate_pet(pet_value, pet_ranges):
    for i, (low, high) in enumerate(pet_ranges):
        if low <= pet_value <= high:
            return i
    return 0  # Default to unsuitable

# Υπολογισμός αξιολογήσεων για όλες τις ποικιλίες
def process_pet_conditions(varieties_pet, df):
    variety_results = {}
    for name, pet_ranges in varieties_pet.items():
        pet_ratings = []
        for _, row in df.iterrows():
            pet_rating = rate_pet(row['PET'], pet_ranges['PET'])
            pet_ratings.append(pet_rating)
        variety_results[name] = pet_ratings
    return variety_results

pet_results = process_pet_conditions(varieties_pet, df)

# Σχεδίαση αποτελεσμάτων καταλληλότητας PET
def plot_pet_suitability(variety_results):
    colors = ['#e74c3c', '#f1c40f', '#2ecc71']  # κόκκινο, κίτρινο, πράσινο
    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#1e1e1e')
    ax.set_title('Καταλληλότητα PET για Ροδακινιές', color='white')

    times = df['Date'].dt.strftime('%d\n%H').tolist()
    days = df['Date'].dt.date.tolist()

    for i, (name, pet_list) in enumerate(variety_results.items()):
        for j, pet_rating in enumerate(pet_list):
            ax.barh(y=i, width=1, left=j, color=colors[pet_rating], edgecolor='none')

    # Γραμμές διαχωρισμού ημερών
    for idx in range(1, len(days)):
        if days[idx] != days[idx - 1]:
            ax.axvline(x=idx, color='white', linestyle='--', linewidth=0.8)

    ax.set_yticks(range(len(varieties_pet)))
    ax.set_yticklabels(varieties_pet.keys(), color='white')
    ax.set_xticks(range(0, len(times), 6))
    ax.set_xticklabels([times[i] for i in range(0, len(times), 6)], color='white')

    legend_patches = [
        mpatches.Patch(color=colors[2], label='Κατάλληλο'),
        mpatches.Patch(color=colors[1], label='Μέτριο'),
        mpatches.Patch(color=colors[0], label='Ακατάλληλο'),
    ]
    ax.legend(handles=legend_patches, loc='lower right', facecolor='#1e1e1e', labelcolor='white')
    ax.text(-2, -0.7, "Ημερομηνία", color='white', fontsize=10, ha='right')
    ax.text(-2, -0.9, "Ώρα", color='white', fontsize=10, ha='right')

    plt.tight_layout()
    plt.savefig("pet_pred")

plot_pet_suitability(pet_results)

