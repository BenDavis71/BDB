import streamlit as st

# Original script credit goes to Hunter Kempf
# https://www.kaggle.com/code/huntingdata11/plotly-animated-and-interactive-nfl-plays/input

import numpy as np
import pandas as pd
import polars as pl
import glob

import seaborn as sns 
import matplotlib.pyplot as plt 
import plotly.graph_objects as go

#from lib.filterwidget import MyFilter

# for mpl animation
import matplotlib.animation as animation
from matplotlib import rc
rc('animation', html='html5')

@st.cache_data(persist=True, show_spinner=False)
def get_data():
    # read all data
    players = pd.read_csv('./nfl-big-data-bowl-2024/players.csv')
    plays = pd.read_csv('./nfl-big-data-bowl-2024/plays.csv')
    games = pd.read_csv('./nfl-big-data-bowl-2024/games.csv')

    tracking_files = glob.glob('./nfl-big-data-bowl-2024/tracking_week*.csv')

    tracking =  pd.concat([pd.read_csv(file) for file in tracking_files], ignore_index=True)

    tracking['adjustedO'] = np.where(tracking['playDirection'] == 'right',
                                tracking['o'].astype(float),
                                (180 + tracking['o'].astype(float)) % 360)

    conditions = [tracking['adjustedO'] <= 180]
    choices = [180 - tracking['adjustedO']]
    default = 540 - tracking['adjustedO']

    tracking['adjustedO'] = np.select(conditions, choices, default=default)

    tracking['adjustedX'] = np.where(tracking['playDirection'] == 'right', 53.3 - tracking['y'], tracking['y'])
    tracking['adjustedY'] = np.where(tracking['playDirection'] == 'right', tracking['x'], 120 - tracking['x'])

    tracking['x'] = tracking['adjustedX']
    tracking['y'] = tracking['adjustedY']

    return players, plays, games, tracking

players, plays, games, tracking = get_data()

def draw_sidebar():
    with st.sidebar:
        options = ['Option 1', 'Option 2', 'Option 3']
        selected_option = st.selectbox('Select an option:', options)



if __name__ == "__main__":
    # st.session_state.filters = (
    #     MyFilter(
    #         human_name='Offense',
    #         df_column='OffensiveTeam',
    #         suffix=' O',
    #         widget_type=st.multiselect,
    #         widget_options={'options': ['1', '2']},
    #     )
    # )

    draw_sidebar()