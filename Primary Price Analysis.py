import pandas as pd
import matplotlib.pyplot as plt
import sys

sys.stdout.reconfigure(encoding='utf-8')

csv_file = "z1Score.csv"
df = pd.read_csv(csv_file, sep=',', encoding='utf-8', low_memory=False)

df['Temp_Out[degC]'] = pd.to_numeric(df['Temp_Out[degC]'], errors='coerce')
df['Hum_Out[%]'] = pd.to_numeric(df['Hum_Out[%]'], errors='coerce')
df['Wind_Speed[m/s]'] = pd.to_numeric(df['Wind_Speed[m/s]'], errors='coerce')

fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(14, 12), sharex=True)

colors = ['tomato', 'dodgerblue', 'seagreen']
metrics = {
    'Temp_Out[degC]': ('Θερμοκρασία (°C)', colors[0]),
    'Hum_Out[%]': ('Υγρασία (%)', colors[1]),
    'Wind_Speed[m/s]': ('Ταχύτητα Άνεμου (m/s)', colors[2]),
}

for idx, (column, (ylabel, color)) in enumerate(metrics.items()):
    ax = axes[idx]
    for year in [2022, 2023, 2024]:
        year_data = df[df['Year'] == year]
        filtered_data = year_data[(year_data[column].notna()) & (year_data[column] != 0)]
        
        if not filtered_data.empty:
            monthly_avg = filtered_data.groupby('Month')[column].mean()
            ax.plot(monthly_avg.index, monthly_avg.values, label=str(year), color=colors[year-2022], linestyle=['-', '--', ':'][year % 3])
    
    ax.set_ylabel(ylabel, fontsize=12)
    ax.legend(title='Έτος')
    ax.grid(True)

plt.suptitle('Ανάλυση Πρωτογενή Τιμών')
axes[-1].set_xlabel('Μέσος Όρος Ανά Μήνα', fontsize=12)
plt.xticks(range(1, 13))
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
fig.subplots_adjust(hspace=0.01)
# plt.savefig('data.png')
plt.show()
