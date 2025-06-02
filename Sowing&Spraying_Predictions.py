import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys
import pyeto
LATITUDE = 39.64


sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv("https://greendigital.uth.gr/data/prediction.csv", encoding='utf-8')

df['Date'] = pd.to_datetime(df['DateTime'])

df = df.rename(columns={
    'Temp_Out[degC]': 'Temperature',
    'Wind_Speed[m/s]': 'Wind_Speed',
    'TotPrec[mm]': 'Rain[mm]',
    'RelHum[%]': 'Hum_Out[%]'
})

df['Rain[mm]'] = pd.to_numeric(df['Rain[mm]'], errors='coerce').fillna(0)
df['Hum_Out[%]'] = pd.to_numeric(df['Hum_Out[%]'], errors='coerce').fillna(0)
df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
df['Wind_Speed'] = pd.to_numeric(df['Wind_Speed'], errors='coerce')
df = df.dropna(subset=['Temperature', 'Wind_Speed'])

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
    
def calculate_soil_moisture(df):
   
    df['PET'] = df.apply(compute_pet_pyeto, axis=1)
    



    df['Soil_Moisture'] = np.maximum(df['Rain[mm]'] - df['PET'], 0) # Prevents negative values
    
    return df


df = calculate_soil_moisture(df)

varieties = {
    "Red Haven": {
        'sowing': {
            'temp': [(0, 17), (18, 21), (22, 24)],
            'moisture': [(0, 39), (40, 49), (50, 60)],
            'wind': [(5.1, 20), (4, 5), (0, 3.9)],
            'humidity': [(30, 50), (51, 70), (71, 90)] 
        },
        'spraying': {
            'temp': [(0, 23), (24, 25), (26, 29)],
            'moisture': [(0, 39), (40, 49), (50, 60)],
            'wind': [(5.1, 20), (4, 5), (0, 3.9)],
            'humidity': [(50, 70), (40, 49), (71, 95)] 
        }
    },
    "Maria Bianca": {
        'sowing': {
            'temp': [(0, 13), (14, 17), (18, 24)],
            'moisture': [(0, 49), (50, 59), (60, 70)],
            'wind': [(4.6, 20), (3.6, 4.5), (0, 3.5)],
            'humidity': [(35, 55), (56, 75), (76, 90)]
        },
        'spraying': {
            'temp': [(0, 19), (20, 23), (24, 28)],
            'moisture': [(0, 49), (50, 59), (60, 70)],
            'wind': [(4.6, 20), (3.6, 4.5), (0, 3.5)],
            'humidity': [(55, 75), (45, 54), (76, 95)] 
        }
    },
    "Honey Dew Hale": {
        'sowing': {
            'temp': [(0, 15), (16, 19), (20, 28)],
            'moisture': [(0, 54), (55, 64), (65, 75)],
            'wind': [(4.1, 20), (3.1, 4), (0, 3)],
            'humidity': [(40, 60), (61, 80), (81, 90)] 
        },
        'spraying': {
            'temp': [(0, 21), (22, 25), (26, 30)],
            'moisture': [(0, 54), (55, 64), (65, 75)],
            'wind': [(4.1, 20), (3.1, 4), (0, 3)],
            'humidity': [(60, 80), (50, 59), (81, 95)] 
        }
    }
}


def rate_value(value, low_range, mid_range, high_range):
    if low_range[0] <= value <= low_range[1]:
        return 0
    elif mid_range[0] <= value <= mid_range[1]:
        return 1
    elif high_range[0] <= value <= high_range[1]:
        return 2
    return 0

def rate_condition(temp, moist, wind, hum, variety_name, condition_type):
    prefs = varieties[variety_name][condition_type]

    temp_score = rate_value(temp, *prefs['temp'])
    moist_score = rate_value(moist, *prefs['moisture'])
    wind_score = rate_value(wind, *prefs['wind'])
    humidity_score = rate_value(hum, *prefs['humidity'])

    if condition_type == 'sowing':
        weights = {'temp': 1, 'moisture': 3, 'wind': 1, 'humidity': 1.5}
    elif condition_type == 'spraying':
        weights = {'temp': 1, 'moisture': 1, 'wind': 1.5, 'humidity': 3}

    weighted_sum = (temp_score * weights['temp'] +
                    moist_score * weights['moisture'] +
                    wind_score * weights['wind'] +
                    humidity_score * weights['humidity'])

    total_weight = sum(weights.values())
    avg_score = round(weighted_sum / total_weight)

    return avg_score

def process_conditions(condition_dict, condition_type):
    variety_results = {}
    for name in varieties:
        condition = []
        for _, row in df.iterrows():
            rating = rate_condition(
                row['Temperature'],
                row['Soil_Moisture'],
                row['Wind_Speed'],
                row['Hum_Out[%]'],
                name,
                condition_type
            )
            condition.append(rating)
        variety_results[name] = condition
    return variety_results

def plot_conditions(variety_results, condition_type):
    colors = ['#e74c3c', '#f1c40f', '#2ecc71']
    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#1e1e1e')
    title_map = {
        'sowing': 'Καταλληλότητα Συνθηκών για Σπορά Ροδακινιών',
        'spraying': 'Καταλληλότητα Συνθηκών για Ψεκασμό Ροδακινιών'
    }
    ax.set_title(title_map[condition_type], color='white')

    times = df['Date'].dt.strftime('%d\n%H').tolist()
    days = df['Date'].dt.date.tolist()

    for i, (name, cond_list) in enumerate(variety_results.items()):
        for j, cond in enumerate(cond_list):
            ax.barh(y=i, width=1, left=j, color=colors[cond], edgecolor='none')

    for idx in range(1, len(days)):
        if days[idx] != days[idx - 1] and days[idx] in days[idx+1:]:
            ax.axvline(x=idx, color='white', linestyle='--', linewidth=0.8)


    # Άξονες και ετικέτες
    ax.set_yticks(range(len(varieties)))
    ax.set_yticklabels(varieties.keys(), color='white')

    ax.set_xticks(range(0, len(times), 6))
    ax.set_xticklabels([times[i] for i in range(0, len(times), 6)], color='white')
    ax.text(-2, -0.7, "Ημερομηνία", color='white', fontsize=10, ha='right')
    ax.text(-2, -0.9, "Ώρα", color='white', fontsize=10, ha='right')

    # Υπόμνημα
    legend_patches = [
        mpatches.Patch(color=colors[2], label='Κατάλληλο'),
        mpatches.Patch(color=colors[1], label='Μέτριο'),
        mpatches.Patch(color=colors[0], label='Ακατάλληλο'),
    ]
    ax.legend(handles=legend_patches, loc='lower right', facecolor='#1e1e1e', labelcolor='white')

    plt.tight_layout()
    plt.show()
    plt.savefig(f"{condition_type}_pred.png", dpi=300)
    plt.close()



sowing_results = process_conditions(varieties, 'sowing')
plot_conditions(sowing_results, 'sowing')

spraying_results = process_conditions(varieties, 'spraying')
plot_conditions(spraying_results, 'spraying')
