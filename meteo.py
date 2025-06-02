import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


df = pd.read_csv("2022_2025.csv", sep=',', encoding='utf-8', low_memory=False)


df.rename(columns={
    'Timestamp[s]': 'Unix_time',
    'Temp_Out[degC]': 'Temperature',
    'Hum_Out[%]': 'RH'
}, inplace=True)


df = df[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Temperature', 'RH']].dropna()
df[['Temperature', 'RH']] = df[['Temperature', 'RH']].apply(pd.to_numeric, errors='coerce')
df.dropna(inplace=True)


df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute']])
df['Day_Date'] = df['Date'].dt.floor('D')
df['Month_Period'] = df['Date'].dt.to_period('M')

# Median
daily_avg_temp = df.groupby('Day_Date')['Temperature'].mean().rename('T_mean')
daily_avg_rh = df.groupby('Day_Date')['RH'].mean().rename('RH_mean')

# Creates new columns in dataset
daily_stats = pd.merge(daily_avg_temp.reset_index(), daily_avg_rh.reset_index(), on='Day_Date')
df = df.merge(daily_avg_temp.reset_index(), on='Day_Date', how='left')
df = df.merge(daily_avg_rh.reset_index(), on='Day_Date', how='left')

# Discomfort index formula
df['DI'] = df['T_mean'] - (0.55 * (1 - 0.01 * df['RH_mean']) * (df['T_mean'] - 14.5))


daily_di = daily_stats.copy()
daily_di['DI'] = daily_di['T_mean'] - (0.55 * (1 - 0.01 * daily_di['RH_mean']) * (daily_di['T_mean'] - 14.5))
daily_di['Year'] = daily_di['Day_Date'].dt.year
daily_di['Month_Period'] = daily_di['Day_Date'].dt.to_period('M')


worst_days = daily_di.loc[daily_di.groupby(['Year', 'Month_Period'])['DI'].idxmax()]

# Main Graph
fig = go.Figure()
years = sorted(daily_di['Year'].unique())
colors = px.colors.qualitative.Set3

for i, year in enumerate(years):
    data = daily_di[daily_di['Year'] == year]
    fig.add_trace(go.Scatter(
        x=data['Day_Date'],
        y=data['DI'],
        mode='markers',
        name=f'Δείκτης Δυσφορίας όλης της ημέρας {year}',
        marker=dict(color=colors[i % len(colors)]),
        hovertext=(
            "Ημερομηνία: " + data['Day_Date'].astype(str) +
            "<br>Μέση Θερμοκρασία: " + data['T_mean'].round(1).astype(str) + " °C" +
            "<br>Μέση Υγρασία: " + data['RH_mean'].round(1).astype(str) + " %" +
            "<br>Τιμή DI : " + data['DI'].round(2).astype(str) + " °C"
        ),
        hoverinfo='text'
    ))

    worst = worst_days[worst_days['Year'] == year]
    fig.add_trace(go.Scatter(
        x=worst['Day_Date'],
        y=worst['DI'],
        mode='markers',
        name='Χειρότερη Ημέρα του μήνα',
        showlegend=(i == 0),
        marker=dict(symbol='circle-open', size=12, color='red'),
        hovertext=(
            "Ημερομηνία: " + worst['Day_Date'].astype(str) +
            "<br>Μέση Θερμοκρασία: " + worst['T_mean'].round(1).astype(str) + " °C" +
            "<br>Μέση Υγρασία: " + worst['RH_mean'].round(1).astype(str) + " %" +
            "<br> Τιμή DI : " + worst['DI'].round(2).astype(str) + " °C"
        ),
        hoverinfo='text'
    ))


fig.update_layout(
    title="Χειρότερη ημέρα του μήνα (Βάσει Δείκτη Δυσφορίας -  Τιμή DI)",
    xaxis_title="Ημερομηνία",
    yaxis_title="Δείκτης Δυσφορίας (Discomfort Index - DI) [°C]",
    height=600,
    width=1000
)

# Levels of DI in the graph
d_levels = {21: 'D1', 24: 'D2', 27: 'D3', 29: 'D4', 32: 'D5'}

for y, label in d_levels.items():
    fig.add_hline(
        y=y,
        line=dict(color='blue', width=1, dash='dot'),
        opacity=0.3
    )
    fig.add_annotation(
        x=0.01,
        y=y,
        text=label,
        xref='paper',
        yref='y',
        showarrow=False,
        font=dict(color='blue', size=14),
        bgcolor='white',
        bordercolor='blue',
        borderwidth=1,
        xanchor='left'
    )


fig.add_annotation(
    x=1.67,
    y=0.01,
    width=400,
    xref="paper",
    yref="paper",
    text=(
        "<b>Εύρος Δείκτη Δυσφορίας(DI) </b><br>"
        "DI < 21: Καμία δυσφορία<br>"
        "21 ≤ DI < 24: Λιγότερο από το 50% του πληθυσμού νιώθει δυσφορία<br>"
        "24 ≤ DI < 27: Περισσότερο από το 50% του πληθυσμού νιώθει δυσφορία<br>"
        "27 ≤ DI < 29: Όλοι νιώθουν δυσφορία<br>"
        "29 ≤ DI < 32: Όλοι νιώθουν δυσφορία και στρες<br>"
        "DI ≥ 32: Επείγουσα ανάγκη ιατρικής περίθαλψης"
    ),
    showarrow=False,
    align="left",
    bordercolor="gray",
    borderwidth=1,
    bgcolor="white",
    font=dict(size=8.5)
)


fig.show()
fig.write_html("diagrama_di.html")

