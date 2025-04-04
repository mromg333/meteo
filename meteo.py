import numpy as np
import pandas as pd
import plotly.express as px

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

weekly = df.groupby('Week').agg({
    'Temperature': 'mean',
    'Wind_Speed': 'mean'
}).reset_index()

weekly['Month'] = weekly['Week'].dt.to_period('M').astype(str)

ideal_temp = 20

weekly['Score'] = abs(weekly['Temperature'] - ideal_temp) + weekly['Wind_Speed']


def best_week_temp(group):
    group = group.copy()
    group['Temp_Diff'] = abs(group['Temperature'] - ideal_temp)
    best = group.loc[group['Temp_Diff'].idxmin()]
    return best

best_week_by_month = weekly.groupby('Month', group_keys=False).apply(best_week_temp).reset_index(drop=True)



weekly['Hover_Info'] = "Εβδομάδα: " + weekly['Week'].astype(str) + \
                       "<br>Temp: " + weekly['Temperature'].round(1).astype(str) + "°C" + \
                       "<br>Wind: " + weekly['Wind_Speed'].round(1).astype(str) + " m/s" + \
                       "<br>Score: " + weekly['Score'].round(1).astype(str)

best_week_by_month['Hover_Info'] = "Καλύτερη εβδομάδα του μήνα " + best_week_by_month['Month'] + \
                                   "<br>Εβδομάδα: " + best_week_by_month['Week'].astype(str) + \
                                   "<br>Temp: " + best_week_by_month['Temperature'].round(1).astype(str) + "°C" + \
                                   "<br>Wind: " + best_week_by_month['Wind_Speed'].round(1).astype(str) + " m/s" + \
                                   "<br>Score: " + best_week_by_month['Score'].round(1).astype(str)


fig = px.scatter(weekly, x='Week', y='Score',
                 hover_data=['Hover_Info'],
                 title='Καλύτερες Εβδομάδες (Βάσει Θερμοκρασίας και Ανέμου)',
                 labels={'Score': 'Score (|Temp-20| + Wind_Speed)', 'Week': 'Εβδομάδα'},
                 color_discrete_sequence=['gray'])

fig.add_scatter(x=best_week_by_month['Week'], y=best_week_by_month['Score'],
                mode='lines+markers',
                marker=dict(color='red', size=12, symbol='circle'),
                name='Καλύτερη εβδομάδα ανά μήνα',
                hovertext=best_week_by_month['Hover_Info'],
                hoverinfo='text')

fig.update_layout(hovermode='closest')
fig.show()

