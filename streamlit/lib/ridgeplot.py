import streamlit as st
import pandas as pd
import plotly.graph_objects as go

@st.cache_data
def draw_ridgeplot(dfs, names, colors, group_count):
    fig = go.Figure()
    for df, name, color in zip(dfs, names, colors):
        name = name + ': ' + str(len(df)) + ' plays'
        #TODO allow sorting
        #TODO allow width adjustment? and bandwidth?
        #TODO later; allow yards (have to adjust the span if so)
        #TODO allow sequential colors
        # from plotly.colors import n_colors
        # colors = n_colors('rgb(5, 200, 200)', 'rgb(200, 10, 10)', 12, colortype='rgb')

        fig.add_trace(go.Violin(x=df['Metric'], line=dict(color='white', width=6), fillcolor=color, name=name))
        fig.add_trace(go.Violin(x=df['Metric'], line=dict(color=color, width=1), fillcolor=color, name=name))

    fig.update_traces(orientation='h', side='negative', width=2.8, points=False, bandwidth=.2, 
        meanline_visible=True, meanline=dict(color='white'), hoveron='kde', spanmode='manual',span=[-7,7])
    fig.update_layout(xaxis_showgrid=False, xaxis_zeroline=False, showlegend=False,  yaxis_autorange='reversed', height=(280+40*group_count))
    fig.add_vline(x=0, line_width=2, line_dash='dash', line_color='white')
    st.plotly_chart(fig, use_container_width=True)