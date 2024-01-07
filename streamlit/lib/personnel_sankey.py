import streamlit as st
import polars as pl
import plotly.graph_objects as go
import urllib.request

from PIL import Image


@st.cache_data(show_spinner=False)
def download_image(image):
    urllib.request.urlretrieve(image, 'logo') #TODO cache these photos here and in personnel sankey
    Image.open('logo')
    return Image.open('logo')

def coalesce(*args): #TODO get this from lib
    val = args[0]
    for arg in args:
        if val:
            return val
        val = arg
    return val

def get_series_list(df, col, sort_col=None):
    return df.sort(f'{coalesce(sort_col, col)}').select(f'{col}').get_columns()[0].to_list()

def get_unique_series_list(df, col, sort_col=None):
    df = df.select(f'{col}', pl.col(f'{coalesce(sort_col, col)}').alias('sort_col')).unique()
    return get_series_list(df, col)

def show(x):
    try:
        st.write(x.collect().to_pandas())
    except:
        st.write(x)

@st.cache_data(show_spinner=False)
def draw_personnel_sankey(_df, name, color, logo, minimum_snap_threshold, combine_groups):


    cols = ['Personnel', 'FunctionalPersonnel']
    spacing_weight = .7

    count = _df.select(pl.count()).collect()
    minimum_snap_threshold *= count

    _df = _df.groupby(cols).agg(pl.col('UniqueID').n_unique().alias('Count'))

    for col in cols * 3: # need to loop through it multiple times due to iterative nature of filter
        _df = _df.with_columns([pl.col('Count').sum().over(pl.col(f'{col}')).alias(f'{col}Count')])
        _df = _df.with_columns([
            pl.when(pl.col(f'{col}Count')<minimum_snap_threshold).then('Other').otherwise(pl.col(f'{col}')).alias(f'{col}')
        ])
        _df = _df.with_columns([pl.col('Count').sum().over(pl.col(f'{col}')).alias(f'{col}Count')])
        _df = _df.with_columns([pl.col('Count').sum().over(cols).alias('Count')])
        _df = _df.unique(subset=cols)

        if not combine_groups:
            _df = _df.filter(pl.col(f'{col}')!='Other')


    _df = _df.with_columns(pl.sum('Count').alias('Total'))
    # TODO custom tooltip
    # TODO better spacing (make it another filter?)
    # TODO add titles for functional and nominal personnel?

    for i, col in enumerate(cols):
        _df = _df.with_columns([pl.col('Count').sum().over(pl.col(f'{col}')).alias(f'{col}Count')])
        _df = _df.with_columns([(pl.col(f'{col}Count') / pl.col('Total')).alias(f'{col}Pct')])
        
        _ = _df.select([f'{col}', f'{col}Pct']).unique().sort(f'{col}').with_row_count(name=f'{col}Row')
        _ = _.with_columns([(pl.col(f'{col}Pct') * spacing_weight + pl.col(f'{col}Pct').mean() * (1-spacing_weight)).alias(f'{col}Y')])
        _ = _.with_columns(pl.cumsum(f'{col}Y') - (pl.col(f'{col}Y') / 2))
        _ = _.with_columns(pl.lit(i*.94 + .03).alias(f'{col}X'))

        _df = _df.join(_, on=f'{col}')

    _df = _df.with_columns([pl.col('FunctionalPersonnelRow') + pl.col('PersonnelRow').max() + pl.lit(1)]).sort(cols)

    _df = _df.collect()

    source=get_series_list(_df, 'PersonnelRow')
    target=get_series_list(_df, 'FunctionalPersonnelRow', 'PersonnelRow')
    value=get_series_list(_df, 'Count', 'PersonnelRow')
    label=[]
    x=[]
    y=[]
    for col in cols:
        label.extend(get_unique_series_list(_df,col))
        x.extend(get_unique_series_list(_df,f'{col}X', col))
        y.extend(get_unique_series_list(_df,f'{col}Y',col))


    # Generate the Sankey chart
    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=label,
                    x=x,
                    y=y,
                    color=color#px.colors.sequential.Sunset
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=value
                ),
            )
        ]
    )

    icon=logo['logo']
    wordmark=logo['wordmark']
    if wordmark:
        image = download_image(wordmark)
        fig = fig.add_layout_image(
                dict(
                    source=image,
                xref="paper", yref="paper",
                x=.75, y=1.15,
                sizex=0.5, sizey=0.5, opacity=0.95,
            xanchor="right", yanchor="middle")
        )

        
        image = download_image(icon)
        fig = fig.add_layout_image(
                dict(
                    source=image,
                xref="paper", yref="paper",
                x=.75, y=1.15,
                sizex=0.4, sizey=0.4, opacity=0.95,
            xanchor="left", yanchor="middle")
        )

    else:
        
        image = download_image(icon)
        fig = fig.add_layout_image(
                dict(
                    source=image,
                xref="paper", yref="paper",
                x=.5, y=1.18,
                sizex=0.315, sizey=0.315, opacity=0.95,
            xanchor="center", yanchor="middle")
        )
    st.header(name)
    st.plotly_chart(fig, use_container_width=True)
