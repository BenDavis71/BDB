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

#TODO clean all this crap up
@st.cache_data(show_spinner=False)
def draw_heatmap(_dfs, names, colors, logos, comparison_mode):
    if comparison_mode == 'Personnel Usage of Individual Groups': #TODO turn to function
        for df,name,color,logo in zip(_dfs,names,colors,logos):
            df = (df.unique(subset='UniqueID').groupby('Personnel').agg(pl.count())
            .filter(~pl.col('Personnel').str.contains('\+',)).sort(by='Personnel') #TODO better way to handle extra linemen
                .with_columns(
                    pl.format(
                        '{}%',
                        (pl.col('count') * 100 // pl.sum('count'))
                    ).alias('%')
                ).collect())

            z=[]
            text=[]
            for tes in range(0,4):
                z_=[]
                text_=[]
                for backs in range(0,3):
                    personnel = f'{backs}{tes}'
                    try:
                        _ = df.filter(pl.col('Personnel')==personnel)
                        z_.append(_[0,1])
                        text_.append(f'{personnel} Pers<br>{_[0,2]}')
                    except:
                        z_.append(None)
                        text_.append('')
                z.append(z_)
                text.append(text_)


            #plot
            fig = go.Figure(data=go.Heatmap(
                                z=z,
                                colorscale = [[0, 'rgba(0,0,0,0)'],  [1, f'{color}']],
                                text=text,
                                texttemplate='%{text}',
                                hovertemplate='%{z} snaps<extra></extra>',
                                hoverongaps = False
                                ))
                                
            fig.update_traces(showscale=False)
            fig.update_xaxes(showgrid=False, zeroline = False, visible=False)
            fig.update_yaxes(showgrid=False, zeroline = False, visible=False)
            # fig.add_layout_image(
            #         dict(
            #             source=logos[0],
            #         xref="paper", yref="paper",
            #         x=1, y=0.8,
            #         sizex=0.5, sizey=0.5, opacity=0.95,
            #         xanchor="right", yanchor="bottom")


            
            # a = team_info.filter(pl.col('team_nick')==teams[0]).select('team_wordmark').collect()[0,0]
            # urllib.request.urlretrieve(a, 'a')
            # a = Image.open('a')
            # fig.add_layout_image(
            #         dict(
            #             source=a,
            #         xref="paper", yref="paper",
            #         x=.75, y=1.15,
            #         sizex=0.5, sizey=0.5, opacity=0.95,
            #         xanchor="right", yanchor="middle")
            # )
            # fig.add_layout_image(
            #         dict(
            #             source=logos[0],
            #         xref="paper", yref="paper",
            #         x=.75, y=1.15,
            #         sizex=0.5, sizey=0.5, opacity=0.95,
            #         xanchor="left", yanchor="middle")
            # )
            # st.write(logo)
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
            
                

            # wordmark=logo['wordmark']
            # if wordmark:
            #     urllib.request.urlretrieve(wordmark, 'logo')
            #     image = Image.open('logo')
            #     fig = fig.add_layout_image(
            #             dict(
            #                 source=image,
            #             xref="paper", yref="paper",
            #             x=.5, y=1,
            #             sizex=0.5, sizey=0.5, opacity=0.95,
            #             xanchor="center", yanchor="bottom")
            #     )


            st.header(name)
            
            st.plotly_chart(fig, config= dict(
                        displayModeBar = False))


    elif comparison_mode == 'Compare Personnel Usage Between Groups':
        comp_df, comp_name, comp_color, comp_logo=_dfs[0], names[0], colors[0], logos[0]
        comp_df=comp_df.with_columns(pl.lit(comp_name).alias('Group')) #TODO to function
        for df,name,color,logo in zip(_dfs[1:],names[1:],colors[1:],logos[1:]): #TODO more elegant
            df=df.with_columns(pl.lit(name).alias('Group'))
            df = pl.concat([comp_df, df], how='vertical')

            df = (df.unique(subset=['UniqueID', 'Group']).groupby('Personnel', 'Group').agg(pl.count())
            .filter(~pl.col('Personnel').str.contains('\+',)).sort(by='Personnel') #TODO better way to handle extra linemen
                .with_columns(
                    
                        (pl.col('count') * 100 // pl.sum('count').over(pl.col(('Group')))
                    ).alias('%').cast(pl.Int8))
                )

            # df = (filtered_df.groupby('Personnel', 'Group').agg(pl.count()).filter(~pl.col('Personnel').str.contains('\+',)).sort(by='Personnel')
            #     .with_columns([
            #         (pl.col('count') * 100 / pl.sum('count').over('Group')).alias('pct'),
            #         pl.format(
            #             '{}%',
            #             (pl.col('count') * 100 // pl.sum('count'))
            #         ).alias('%')
            #     ]))
                
            df = df.filter(pl.col('Group')==comp_name).join(df.filter(pl.col('Group')==name),on='Personnel',how='outer').with_columns(pl.all().fill_null(0)) #TODO outer join seems to be messing up in cardinals vs cardinals comparison
            df = df.with_columns((pl.col('%') - pl.col('%_right')).alias('pct_diff')).collect()

            z=[]
            snaps=[]
            text=[]
            
            for tes in range(0,4):
                z_=[]
                snaps_=[]
                text_=[]
                for backs in range(0,3):
                    personnel = f'{backs}{tes}'
                    try:
                        _ = df.filter(pl.col('Personnel')==personnel)
                        z_.append(_[0,'pct_diff']) ##dividing by 6 because 6 skill players on each play #TODO use distinct on the uid after filters; not good #TODO fix this above; select by column name
                        snaps_.append(f"{_[0,'%']}% of {comp_name} snaps<br>{_[0,'%_right']}% of {name} snaps")
                        text_.append(f'{personnel} Pers<br>{_[0,"pct_diff"]:.{0}f}%') #TODO fix text; make it read out the team if they're different, but if not then just go on down the line of differences til one is found
                    except:
                        z_.append(None)
                        snaps_.append(f'')
                        text_.append('')
                z.append(z_)
                snaps.append(snaps_)
                text.append(text_)


            #plot
            fig = go.Figure(data=go.Heatmap(
                                z=z,
                                colorscale = [[0, f'{color}'], [.5, 'rgba(0,0,0,0)'], [1, f'{comp_color}']],
                                text=text,
                                texttemplate='%{text}',
                                customdata=snaps,
                                hovertemplate='%{customdata}<extra></extra>',
                                hoverongaps = False
                                ))
                                
            fig.update_traces(showscale=False)
            fig.update_xaxes(showgrid=False, zeroline = False, visible=False)
            fig.update_yaxes(showgrid=False, zeroline = False, visible=False)

            # for x, logo in zip([.2,1],logos): #TODO take account of (didn't finish my thought and forgot what I was gonna say; maybe avoid magic numbers? eh)
            #     fig.add_layout_image(
            #             dict(
            #                 source=logo,
            #             xref="paper", yref="paper",
            #             x=x, y=0.8,
            #             sizex=0.5, sizey=0.5, opacity=0.95,
            #             xanchor="right", yanchor="bottom")
            # )

            if comp_logo != logo:
                for i, logo, direction in zip([0,1],[comp_logo,logo], ['left','right']): #TODO more elegant
                    wordmark=logo['wordmark']
                    icon=logo['logo']
                    if wordmark:
                        image = download_image(wordmark)
                        fig = fig.add_layout_image(
                                dict(
                                    source=image,
                                xref="paper", yref="paper",
                                x=i, y=1.15,
                                sizex=0.4, sizey=0.4, opacity=0.95,
                            xanchor=direction, yanchor="middle")
                        )
                    else:
                        x=.12
                        if direction=='right':
                            x=-x
                        
                        image = download_image(icon)
                        fig = fig.add_layout_image(
                                dict(
                                    source=image,
                                xref="paper", yref="paper",
                                x=i+x, y=1.18,
                                sizex=0.315, sizey=0.315, opacity=0.95,
                            xanchor=direction, yanchor="middle")
                        )
            else:
                wordmark=logo['wordmark']
                icon=logo['logo']
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
                        xanchor="left", yanchor="middle")
                    )

            st.header(comp_name + ' vs ' + name)
            st.plotly_chart(fig, config= dict(
                        displayModeBar = False)) #TODO disable zoom in?


