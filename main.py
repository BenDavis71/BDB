import pandas as pd
import numpy as np
import polars as pl
import plotly.express as px
import streamlit as st

# df_source =  '/Users/bendavis/Documents/GitHub/FootballAnalysis/players.parquet'
# df_team_info_source = '/Users/bendavis/Documents/GitHub/FootballAnalysis/teams_colors_logos.csv'

@st.cache_data(show_spinner=False)
def get_data():
    games = pl.read_csv('nfl-big-data-bowl-2024/games.csv')
    games = games.select(pl.col('week','gameId'))

    players = pl.read_csv('nfl-big-data-bowl-2024/players.csv')
    players = players.filter(pl.col('position').is_in(['NT','DT','DE','MLB','ILB','OLB','SS','FS','CB','DB']))
    players=players.with_columns([
        pl.col('nflId').cast(str).alias('nflId')
    ])

    unique_players = sorted(players.select('displayName').get_columns()[0].to_pandas().to_list())

    tackles = pl.read_csv('nfl-big-data-bowl-2024/tackles.csv')
    tracking = pl.read_csv('nfl-big-data-bowl-2024/tracking_week_*.csv', infer_schema_length=10000)
    tackles=tackles.with_columns([
        (pl.col('gameId').cast(str) + '-' + pl.col('playId').cast(str)).alias('playId'),
        pl.col('nflId').cast(str).alias('nflId')
    ])
    tracking=tracking.with_columns([
        (pl.col('gameId').cast(str) + '-' + pl.col('playId').cast(str)).alias('playId')
    ])

    tackles = tackles.join(games,on='gameId')

    photos = pl.read_csv('https://github.com/nflverse/nflverse-data/releases/download/players/players.csv')

    return players, unique_players, tackles, tracking, photos

def coalesce(*args):
    val = args[0]
    for arg in args:
        if val:
            return val
        val = arg
    return val

# get data and lazyframes
players, unique_players, tackles, tracking, photos = get_data()
players, tackles, tracking = players.lazy(), tackles.lazy(), tracking.lazy()


# center based around plotly
left, middle = st.columns((.28, 5))

# Week filter
with middle:
    week = st.slider('Week',min_value=1,max_value=9, value=[1,9])
tackles = tackles.filter(pl.col('week').is_between(*week))


# Player filter
with middle:
    tackler = st.selectbox('Player',unique_players)
tacklerId = players.filter(pl.col('displayName')==tackler).select('nflId').collect().item()
tackles = tackles.filter(pl.col('nflId')==tacklerId)
# st.write('tackles')
# st.write(tackles.collect().to_pandas())



ball = tracking.filter(pl.col('nflId')=='NA').filter(pl.col('frameId')==1)
# ball = tracking.filter(pl.col('nflId')=='NA').filter(pl.col('playId')=='2022090800-2648')
# tackles=tackles.filter(pl.col('playId')=='2022090800-617')
# tracking=tracking.filter(pl.col('playId')=='2022090800-617').filter(pl.col('nflId')==tacklerId)
# st.write(tracking.collect().to_pandas())
# st.write('ball')
# st.write(ball.collect().to_pandas())
tracking = tracking.join(tackles, on=['nflId','playId'], how="inner")
# st.write('tracking after tackle join')
# st.write(tracking.collect().to_pandas())

# tackles = tackles.filter(pl.col('playId')=='2022090800-101')
# tracking = tracking.filter(pl.col('playId')=='2022090800-101')
# tracking = tracking.filter(pl.col('nflId')=='42816')
tracking = tracking.join(ball, on='playId', how="inner",suffix='_origin')
# st.write('tracking after ball join')
# st.write(tracking.collect().to_pandas())
# x_origin = ball.select('x').collect().item()
# y_origin = ball.select('y').collect().item()

#TODO refactor to do absolute value instead?
tracking = tracking.with_columns([
    pl.when(pl.col('playDirection')=='right').then(pl.col('x') - pl.col('x_origin')).otherwise(pl.col('x_origin') - pl.col('x') ).alias('relative_x'),
    pl.when(pl.col('playDirection')=='right').then( pl.lit(53.3/2) - pl.col('y')).otherwise(pl.col('y') - pl.lit(53.3/2)).alias('relative_y'),
    pl.when(pl.col('tackle')==1).then('tackle').when(pl.col('assist')==1).then('assist').otherwise('missed').alias('result'),
])


# 2022090800-101
# st.write(tracking.collect().to_pandas())
# st.write('brah')
# st.write(tackles.collect().to_pandas())
# st.write(tracking.collect().to_pandas())

tracking = tracking.with_columns(pl.col('frameId').max().over('playId').alias('maxFrame'))
tracking = tracking.collect().to_pandas()
fig = px.line(
    tracking,
    x='relative_y',
    y='relative_x', 
    line_group='playId',
    color='result',
    color_discrete_map={'tackle':'green','assist':'blue','missed':'grey'},
    )

origin_plot = px.scatter(
    tracking[tracking['frameId']==1],
    x='relative_y',
    y='relative_x',
    opacity=0.6,
    color_discrete_sequence=['white'],
    # color='result',
    # color_discrete_map={'tackle':'green','assist':'blue','missed':'grey'}
    )
origin_plot.update_traces(marker=dict(size=9))

end_plot = px.scatter(
    tracking[tracking['frameId']==tracking['maxFrame']],
    x='relative_y',
    y='relative_x',
    # opacity=0.7,
    color_discrete_sequence=['white'],
    color='result',
    color_discrete_map={'tackle':'green','assist':'blue','missed':'grey'}
    )
end_plot.update_traces(marker=dict(size=10,symbol='diamond'))
fig.update_layout(
    showlegend=False,
    xaxis=dict(range=[-63/2, 63/2], autorange=False,showgrid=False,showticklabels=False,title=''),
    yaxis=dict(range=[-14,38],nticks=6,tickangle=270,tickfont=dict(family='Rockwell', size=20),title=''),
    margin=dict(t=0, b=0),
    )

# Get and display kicker headshot in the center
photos = photos.to_pandas()
try:
    left, middle = st.columns((2.88, 5))
    with middle:
        st.image(photos[photos['display_name'] == tackler]['headshot'].reset_index(drop=True)[0], width=250)
except:
    pass  # If headshot not available


# fig.add_traces(list(origin_plot.select_traces()))
fig.add_traces(list(end_plot.select_traces()))
fig.update_traces(opacity=.7)
st.write(fig)


#TODO glob all weeks
