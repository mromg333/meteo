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
df['Day_Date'] = df['Date'].dt.floor('D')  # Κόβουμε ώρα για να έχουμε ημερομηνία μόνο
df['Month_Period'] = df['Date'].dt.to_period('M')


daily_avg_temp = df.groupby('Day_Date')['Temperature'].mean().rename('T_mean')
daily_avg_rh = df.groupby('Day_Date')['RH'].mean().rename('RH_mean')


daily_stats = pd.merge(daily_avg_temp.reset_index(), daily_avg_rh.reset_index(), on='Day_Date')
df = df.merge(daily_avg_temp.reset_index(), on='Day_Date', how='left')
# Discomfort Index 
df['DI'] = df['T_mean'] - (0.55 * (1 - 0.01 * df['RH']) * (df['T_mean'] - 14.5))
#Based on real time Humitidy and median temp

def mode_di(series):
    modes = series.mode()
    return modes.iloc[0] if not modes.empty else None


daily_mode_di = df.groupby('Day_Date')['DI'].apply(mode_di).rename('DI_mode').reset_index()


daily_di = pd.merge(daily_stats, daily_mode_di, on='Day_Date')
daily_di['Year'] = daily_di['Day_Date'].dt.year
daily_di['Month_Period'] = daily_di['Day_Date'].dt.to_period('M')


best_days = daily_di.loc[daily_di.groupby(['Year', 'Month_Period'])['DI_mode'].idxmin()]


fig = go.Figure()
years = sorted(daily_di['Year'].unique())
colors = px.colors.qualitative.Set3

for i, year in enumerate(years):
    data = daily_di[daily_di['Year'] == year]
    fig.add_trace(go.Scatter(
        x=data['Day_Date'],
        y=data['DI_mode'],
        mode='lines+markers',
        name=f'Επικρατούσα Τιμή DI όλης της ημέρας {year}',
        marker=dict(color=colors[i % len(colors)]),
        hovertext=(
            "Ημερομηνία: " + data['Day_Date'].astype(str) +
            "<br>Μέση Θερμοκρασία: " + data['T_mean'].round(1).astype(str) + " °C" +
            "<br>Μέση Υγρασία: " + data['RH_mean'].round(1).astype(str) + " %" +
            "<br>Επικρατούσα Τιμή DI : " + data['DI_mode'].round(2).astype(str) + " °C"
        ),
        hoverinfo='text'
    ))

    best = best_days[best_days['Year'] == year]
    fig.add_trace(go.Scatter(
        x=best['Day_Date'],
        y=best['DI_mode'],
        mode='markers',
        name=f'Καλύτερη Ημέρα {year}',
        marker=dict(symbol='circle-open', size=12, color='red'),
        hovertext=(
            "Ημερομηνία: " + best['Day_Date'].astype(str) +
            "<br>Μέση Θερμοκρασία: " + best['T_mean'].round(1).astype(str) + " °C" +
            "<br>Μέση Υγρασία: " + best['RH_mean'].round(1).astype(str) + " %" +
            "<br>Επικρατούσα Τιμή DI : " + best['DI_mode'].round(2).astype(str) + " °C"
        ),
        hoverinfo='text'
    ))

fig.update_layout(
    title="Καλύτερη ημέρα του μήνα (Βάσει Δείκτη Δυσφορίας - Επικρατούσα Τιμή DI)",
    xaxis_title="Ημερομηνία",
    yaxis_title="Δείκτης Δυσφορίας (Discomfort Index - DI) [°C]",
    height=600,
    width=1000
    
)

# WORKING SOLUTION - RUNS WITHOUT ERRORS

# 1. First make sure we have a figure
if 'fig' not in locals():
    fig = go.Figure()  # Creates figure if one doesn't exist

# 2. Add D labels INSIDE the plot area
d_levels = {21: 'D1', 24: 'D2', 27: 'D3', 29: 'D4', 32: 'D5'}

for y, label in d_levels.items():
    # Add horizontal line
    fig.add_hline(
        y=y,
        line=dict(color='blue', width=1, dash='dot'),
        opacity=0.3
    )
    
    # Add label inside plot
    fig.add_annotation(
        x=0.01,  # 1% from left edge (0-1 range)
        y=y,
        text=label,
        xref='paper',  # Use relative coordinates
        yref='y',     # Use actual y-values
        showarrow=False,
        font=dict(color='blue', size=14),
        bgcolor='white',
        bordercolor='blue',
        borderwidth=1,
        xanchor='left'
    )

# Add the DI legend box (keeps all existing plot elements intact)
fig.add_annotation(
    x=1.69,  # Right side outside plot
    y=0.01,   # Vertical center
    width=400,
    xref="paper",
    yref="paper",
    text=(
        "<b> Range of Discomfort Index(DI) </b><br>"
        "DI < 21: No discomfort<br>"
        "21 ≤ DI < 24: Less than 50% of the population feels discomfort<br>"
        "24 ≤ DI < 27: More than 50% of the population feels discomfort<br>"
        "27 ≤ DI < 29: All feel discomfort<br>"
        "29 ≤ DI < 32: All feel discomfort and stress<br>"
        "DI ≥ 32: Emergency medical state"
    ),
    showarrow=False,
    align="left",
    bordercolor="gray",
    borderwidth=1,
    bgcolor="white",
    font=dict(size=9)
)

 

fig.show()
fig.write_html("diagrama_di.html")

