import streamlit as st

# Original script credit goes to Hunter Kempf
# https://www.kaggle.com/code/huntingdata11/plotly-animated-and-interactive-nfl-plays/input

import numpy as np
import pandas as pd
import polars as pl

import seaborn as sns 
import matplotlib.pyplot as plt 
import plotly.graph_objects as go
from toolz.itertoolz import pluck
from typing import Iterable
from streamlit_option_menu import option_menu

from lib.filterwidget import MyFilter
from lib.ridgeplot import draw_ridgeplot
from lib.heatmap import draw_heatmap
from lib.personnel_sankey import draw_personnel_sankey

# for mpl animation
import matplotlib.animation as animation
from matplotlib import rc
rc('animation', html='html5')

@st.cache_data(persist=True, show_spinner=False)
def get_data():
    # read all data
    players = pl.scan_parquet('Data/players.parquet')
    plays = pl.scan_parquet('Data/plays.parquet')
    games = pl.scan_parquet('Data/games.parquet')
    tracking = pl.scan_parquet('Data/tracking_week_*.parquet')
    play_results = pl.scan_parquet('Data/results.parquet')

    return players, plays, games, tracking, play_results

def get_active_filters() -> filter:
    return filter(lambda _: _.is_enabled, st.session_state.filters)


def is_any_filter_enabled() -> bool:
    return any(pluck("is_enabled", st.session_state.filters))


def get_human_filter_names(iter: Iterable) -> Iterable:
    return pluck("human_name", iter)


team_colors = {
    'ARI':["#97233F","#000000","#FFB612"], 
    'ATL':["#A71930","#000000","#A5ACAF"], 
    'BAL':["#241773","#000000"], 
    'BUF':["#00338D","#C60C30"], 
    'CAR':["#0085CA","#101820","#BFC0BF"], 
    'CHI':["#0B162A","#C83803"], 
    'CIN':["#FB4F14","#000000"], 
    'CLE':["#311D00","#FF3C00"], 
    'DAL':["#003594","#041E42","#869397"],
    'DEN':["#FB4F14","#002244"], 
    'DET':["#0076B6","#B0B7BC","#000000"], 
    'GB' :["#203731","#FFB612"], 
    'HOU':["#03202F","#A71930"], 
    'IND':["#002C5F","#A2AAAD"], 
    'JAX':["#101820","#D7A22A","#9F792C"], 
    'KC' :["#E31837","#FFB81C"], 
    'LA' :["#003594","#FFA300","#FF8200"], 
    'LAC':["#0080C6","#FFC20E","#FFFFFF"], 
    'LV' :["#000000","#A5ACAF"],
    'MIA':["#008E97","#FC4C02","#005778"], 
    'MIN':["#4F2683","#FFC62F"], 
    'NE' :["#002244","#C60C30","#B0B7BC"], 
    'NO' :["#101820","#D3BC8D"], 
    'NYG':["#0B2265","#A71930","#A5ACAF"], 
    'NYJ':["#125740","#000000","#FFFFFF"], 
    'PHI':["#004C54","#A5ACAF","#ACC0C6"], 
    'PIT':["#FFB612","#101820"], 
    'SEA':["#002244","#69BE28","#A5ACAF"], 
    'SF' :["#AA0000","#B3995D"],
    'TB' :["#D50A0A","#FF7900","#0A0A08"], 
    'TEN':["#0C2340","#4B92DB","#C8102E"], 
    'WAS':["#5A1414","#FFB612"], 
    'football':["#CBB67C","#663831"]
}

#TODO fix to include other selections
def hex_color_from_color_selection(selection, team):
    print("hex_color_from_color_selection()")

    # Change this
    return team_colors[team[0]][1]

#TODO throw into helper lib
def coalesce(*args):
    print("coalesce()")
    val = args[0]
    for arg in args:
        if val:
            return val
        val = arg
    return val

def filter_df(df, masks):
    print("filter_df()")
    for mask in masks:
        df=df.filter(mask)
    df = df.unique(subset='uniquePlayId') #TODO move this elsewhere?
    return df

 # *args is just there to force a cache update when there's a change in the filters
# @st.cache_data
def collect_df(_df, selected_columns, *args):
    return  _df.select(selected_columns).collect().to_pandas()

def add_filter_name_to_df(df, name):
    return df.select([pl.lit(name).alias(('FilterName')), pl.all()])

def get_item_from_team_info_df(selection, team, _df_team_info):
    print("get_item_from_team_info_df()")
    return _df_team_info.filter(pl.col('team_nick')==pl.lit(team)).select(selection).collect().item()

# @st.cache_data
# def get_logos(team, _df_team_info):
#     if len(team) == 1:
#         team=team[0]
#     try:
#         logos={
#             'logo': get_item_from_team_info_df('team_logo_espn', team, _df_team_info),
#             'wordmark': get_item_from_team_info_df('team_wordmark', team, _df_team_info),
#         }        
#         return logos
#     except:
#         logos={
#             'logo': 'https://raw.githubusercontent.com/nflverse/nflverse-pbp/master/NFL.png',
#             'wordmark': None #'https://raw.githubusercontent.com/nflverse/nflverse-pbp/master/NFL.png'
#         }    
#         return logos

def draw_sidebar():
    """Should include dynamically generated filters"""
    print("in draw_sidebar")

    with st.sidebar:
        print("in st.sidebar")

        st.markdown("""
        <style>
        .little-font {
            font-size:14x !important;
        }
        </style>
        """, unsafe_allow_html=True) #TODO throw this into a function
        st.title('Select which filters to enable')
        selected_filters = st.multiselect(
            '',
            list(get_human_filter_names(st.session_state.filters)),
            ['Offense'],
        )

        print("All selected filters", selected_filters)

        #TODO universal filter
        #TODO load preset filters
        #TODO save current filter to preset
        
        MyFilter.group_count = st.number_input("Groups", 1, 20)

        print("Enabling filters")
        for table_filter in st.session_state.filters:
            if table_filter.human_name in selected_filters:
                print(table_filter.human_name, ": enabled")
                table_filter.enable()
        print("Finished enabling filters")

        if is_any_filter_enabled():
            print("Filters are enabled")
            color_options=['Team Color 1', 'Team Color 2', 'Team Color 3', 'Team Color 4', 'Custom', 'Red', 'Orange', 'Yellow', 'Green', 'Blue','Indigo','Violet']
            filter_selections={}

            for i in range(1, MyFilter.group_count+1):
                filter_selection={}
                filter_selection['values']={}
                filter_selection['masks']={}
                generated_name = ''
                offense, defense = False, False
                
                st.markdown('_____________________________')
                st.title(f'Group {i}')

                custom_name=  st.text_input('Group Name', key=f'group_name_{i}')

                col1, col2 = st.columns([4,1])
                with col1:
                    filter_selection['color'] = st.selectbox('Color',color_options, key=f'color_selection_{i}')
                with col2:
                    if filter_selection['color']=='Custom':
                        filter_selection['color'] = st.color_picker('', key=f'custom_color_{i}')

                for table_filter in get_active_filters():
                    delimiter = ', '

                    col1, col2 = st.columns([4,1]) #have to reset for proper spacing
                    with col1:
                        table_filter.create_widget(i)
                    with col2:
                        st.markdown('<p class="little-font">Exclude</p>', unsafe_allow_html=True)
                        filter_selection['values'][table_filter.human_name],\
                        filter_selection['masks'][table_filter.human_name],\
                        generated_name_component\
                          = table_filter.exclude_widget(i)


                    if table_filter.human_name.startswith('Offens') and filter_selection['values'][table_filter.human_name]:
                        offense=True
                    elif table_filter.human_name.startswith('Defens') and filter_selection['values'][table_filter.human_name]:
                        defense=True
                    if offense and defense:
                        delimiter = ' vs '
                        offense, defense = False, False

                    if generated_name_component:
                        generated_name = generated_name + delimiter + generated_name_component
                        
                #TODO remove if any individual component is too long; cut off after like 3 components
                #TODO somehow make it say vs if offense and defense are included
                filter_selection['name'] = coalesce(custom_name, generated_name[2:])

                filter_selections[i]=filter_selection

        else:
            st.write("Please enable a filter")
            filter_selections=None

        return filter_selections


@st.cache_data
def get_options(_df,column):
    return sorted(_df.select(column).drop_nulls().unique().collect().get_columns()[0].to_list())

@st.cache_data
def get_min(_df,column):
    return _df.select(column).min().collect().item()

@st.cache_data
def get_max(_df,column):
    return _df.select(column).max().collect().item()



if __name__ == "__main__":
    
    # Read in data
    players, plays, games, tracking, play_results = get_data()

    #TODO put these filters in a function on another page or something
    passing_concepts=['Arches', 'Bow', 'Dragon', 'Drive', 'Leak', 'Mesh', 'Sail', 'Scissors', 'Shallow Cross', 'Shock', 'Smash', 'Snag', 'Stick', 'Tosser', 'Y Cross']
    down_dict={1:'1st',2:'2nd',3:'3rd',4:'4th'}
    quarter_dict={1:'1st Q',2:'2nd Q',3:'3rd Q',4:'4th Q',5:'OT'}
    format_time_remaining=lambda s: f'{s//60}:{s%60:02}'
    def calculate_field_position(yards_to_goalline):
        if yards_to_goalline<50:
            return f'Opp {yards_to_goalline}'
        elif yards_to_goalline>50:
            return f'Own {100-yards_to_goalline}'
        return '50'

    print("Loading filters")
    st.session_state.filters = (
        MyFilter(
            human_name='Offense',
            df_column='offense',
            suffix=' O',
            widget_type=st.multiselect,
            widget_options={'options':get_options(plays,'possessionTeam')},
        ),
        # MyFilter(
        #     human_name='Offensive Division',
        #     df_column='OffensiveDivision',
        #     suffix=' O',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(df_team_info,'team_division')},
        # ),e333333333333
        # MyFilter(
        #     human_name='Offensive Conference',
        #     df_column='OffensiveConference',
        #     suffix=' O',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(df_team_info,'team_conf')},
        # ),
        MyFilter(
            human_name='Defense',
            df_column='defense',
            suffix=' D',
            widget_type=st.multiselect,
            widget_options={'options':get_options(plays,'defensiveTeam')},
        ),
        MyFilter(
            human_name='Week',
            df_column='week',
            prefix = 'Week ',
            widget_type=st.slider,
            widget_options={'min_value':1, 'max_value':get_max(games,'week'), 'value':[1,get_max(games,'week')]},
        ),
        #Nid help
        # MyFilter(
        #     human_name='Quarter',
        #     df_column='Quarter',
        #     widget_type=st.select_slider,
        #     widget_options={'options':range(1,6), 'value':[1,5], 'format_func': lambda x: quarter_dict[x]}, 
        #     format_func=lambda x: quarter_dict[x]
        # ),
        # #Nid help
        # MyFilter(
        #     human_name='Time Remaining',
        #     df_column='TimeLeft',
        #     suffix=' left in the quarter',
        #     widget_type=st.select_slider,
        #     widget_options={'options':range(900,-1,-15), 'value':[900,0], 'format_func': format_time_remaining},
        #     format_func=format_time_remaining
        # ),
        # #Nid help
        # MyFilter(
        #     human_name='Down',
        #     df_column='Down',
        #     suffix=' Down',
        #     widget_type=st.select_slider,
        #     widget_options={'options':range(1,5), 'value':[1,4], 'format_func': lambda x: down_dict[x]}, 
        #     format_func=lambda x: down_dict[x]
        # ),
        # #Nid help
        # MyFilter(
        #     human_name='Distance',
        #     df_column='ToGo',
        #     suffix=' yards to go',
        #     widget_type=st.slider,
        #     widget_options={'min_value':1, 'max_value':get_max(plays,'ToGo'), 'value':[1,get_max(plays,'ToGo')]},
        # ),
        # #Nid help
        # MyFilter(
        #     human_name='Field Position',
        #     df_column='YardsFromEndzone',
        #     prefix='Snapped between ',
        #     widget_type=st.select_slider,
        #     widget_options={'options':range(99,0,-1), 'value':[99,1], 'format_func': calculate_field_position},
        #     format_func=calculate_field_position
        # ),
        # #Nid help
        # MyFilter(
        #     human_name='Passing Concepts (Any)',
        #     df_column=passing_concepts,
        #     widget_type=st.multiselect,
        #     widget_options={'options':passing_concepts},
        #     special_type='any_concepts'
        # ), 
        # MyFilter(
        #     human_name='Passing Concepts (All)',
        #     df_column=passing_concepts,
        #     widget_type=st.multiselect,
        #     widget_options={'options':passing_concepts},
        #     special_type='all_concepts'
        # ), 
        # MyFilter(
        #     human_name='Routes (Any)',
        #     df_column='Routes',
        #     suffix=' Route',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(df,'Route')},
        #     special_type='any_routes'
        # ), 
        # MyFilter(
        #     human_name='Routes (All)',
        #     df_column='Routes',
        #     suffix=' Route',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(df,'Route')},
        #     special_type='all_routes'
        # ), 
        # MyFilter(
        #     human_name='Coverage',
        #     df_column='CoverageScheme',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(plays,'CoverageScheme')}
        # ), 
        # MyFilter(
        #     human_name='Coverage Family',
        #     df_column='CoverageFamily',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(plays,'CoverageFamily')}
        # ), 
        # MyFilter(
        #     human_name='Personnel',
        #     df_column='Personnel',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(df,'Personnel')},
        # ),
        # MyFilter(
        #     human_name='Functional Personnel',
        #     df_column='FunctionalPersonnel',
        #     prefix='lined up as ',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(df,'FunctionalPersonnel')},
        # ),
        # MyFilter(
        #     human_name='Receiver Distribution',
        #     df_column='ReceiverDistribution',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(df,'ReceiverDistribution')},
        # ),
        # MyFilter(
        #     human_name='Drop Type',
        #     df_column='DropType',
        #     suffix=' Drop',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(plays,'DropType')},
        # ),
        # MyFilter(
        #     human_name='Bunch',
        #     df_column='Bunch',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(df,'Bunch')},
        # ),
        # MyFilter(
        #     human_name='Stack',
        #     df_column='Stack',
        #     suffix = ' Stacks',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(df,'Stack')},
        # ),
        # MyFilter(
        #     human_name='Compressed',
        #     df_column='Compressed',
        #     prefix='Compressed on ',
        #     widget_type=st.multiselect,
        #     widget_options={'options':get_options(df,'Compressed')},
        # ),
        # MyFilter(
        #     human_name='Play Action',
        #     df_column='PlayAction',
        #     widget_type=st.checkbox,
        # ),
        # MyFilter(
        #     human_name='Fake Handoffs',
        #     df_column='FakeHandoffs',
        #     suffix=' Fake Handoffs',
        #     widget_type=st.slider,
        #     widget_options={'min_value':0, 'max_value':get_max(df,'FakeHandoffs'), 'value':[0,get_max(df,'FakeHandoffs')]},
        # ),
        # MyFilter(
        #     human_name='Under Center',
        #     df_column='UnderCenter',
        #     widget_type=st.checkbox,
        # ),
        # MyFilter(
        #     human_name='Quick Motion',
        #     df_column='QuickMotion',
        #     widget_type=st.checkbox,
        # ),
        # MyFilter(
        #     human_name='Wildcat',
        #     df_column='Wildcat',
        #     widget_type=st.checkbox,
        # ),
        # MyFilter(
        #     human_name='Flex RB',
        #     df_column='FlexRB',
        #     widget_type=st.checkbox,
        # ),
        # MyFilter(
        #     human_name='Flex TE',
        #     df_column='FlexTE',
        #     widget_type=st.checkbox,
        # ),
        # MyFilter(
        #     human_name='Nub TE',
        #     df_column='NubTE',
        #     widget_type=st.checkbox,
        # ),
    )

    print("Loading filters done")

    plays=plays.with_columns([
        pl.when(pl.col('expectedPointsAdded')>pl.lit(0)).then(1).otherwise(0).alias('SuccessfulPlay'),
        pl.when(pl.col('playResult')>=pl.lit(10)).then(1).otherwise(0).alias('ExplosivePlay'),
        pl.when(pl.col('playResult')<=pl.lit(0)).then(1).otherwise(0).alias('StuffedPlay'),

    ]) 

    print("SuccessPlay/ExplosivePlay/StuffedPlay done")
    
    # st.write(plays.collect().to_pandas())
    # try:
    print("Trying to draw sidebar")
    filter_selections = draw_sidebar()
    print("Finished drawing sidebar")
    # st.write(df.collect().filter(True).to_pandas())
    # st.write(*filter_selections.items())
    # st.write(filter_selections[1]['masks']['Personnel'])
    # st.write(df.collect().filter(filter_selections[1]['masks']['Personnel']))
    #names = list(pluck('name', filter_selections.values()))
    #values = list(pluck('values', filter_selections.values()))
    # st.cache_data.clear()
    # master_df = df.join(plays, on='UniqueID', how='inner')
    # for side in ['Offensive','Defensive']:
    #     _ = df_team_info.select(['team_nick','team_conf','team_division']).rename({
    #         'team_nick':f'{side}Team', 'team_conf':f'{side}Conference', 'team_division':f'{side}Division'
    #         })
    #     master_df = master_df.join(_, on=f'{side}Team', how='inner')
    # st.write(master_df.collect().to_pandas().columns)
    # st.write(master_df.select('Route').unique().collect().to_pandas())
    dfs=[]
    stats_dfs=[] #TODO make this more elegant
    names=[]
    colors=[]
    logos=[]

    #TODO this is main; reorganize all this crap
    st.title('Pull the Plug')
    # st.image('/Users/bendavis/Documents/GitHub/BDB/assets/pullThePlug.png')
    options = ['Ridgeline', 'Heatmap', 'Sankey','Cut-Ups', 'About']
    selected_page = option_menu(None, options, orientation='horizontal', styles={'icon': {'font-size': '0px'}})
    if selected_page == 'Ridgeline':
        print("Selected Page: ", selected_page)

        st.header('EPA Ridgeline Plot and Stats')
        st.header('')
    
        for i in range(1, MyFilter.group_count+1): #todo have a function for this?
            print('Getting filter values')

            name = coalesce(filter_selections[i]['name'], 'NFL')
            color = filter_selections[i]['color']
            values = filter_selections[i]['values']
            masks = filter_selections[i]['masks']
            shared_offense=filter_selections.get(0,{}).get('values',{}).get('Offense','')
            shared_defense=filter_selections.get(0,{}).get('values',{}).get('Defense','')
            offense = values.get('Offense', '')
            defense = values.get('Defense', '')
            team = coalesce(shared_offense,shared_defense,offense,defense,'NA')
            print("Finished getting filter values")


            df = add_filter_name_to_df(play_results, name)
            #TODO allow ability to select defensive team's colors
            color = hex_color_from_color_selection(color, team)


            df = filter_df(df, masks.values())


            # start ridgeline function here?
            metric = 'expectedPointsAdded' #TODO bring out of loop? and is the below stupid?
            
            print("joining play_results to plays to get EPA")
            df = df.join(plays, on=['gameId','playId'], how='left')
            print("finished joining play_results to plays to get EPA")  

            # df.schema
            df = df.with_columns([pl.col(metric).alias('Metric')])
            selected_columns=['FilterName', 'Metric'] 
            # df = collect_df(df, selected_columns, values)
            # df = df.select(selected_columns).collect().to_pandas()
            

            #TODO exclude don't work
            #TODO defense don't work
            dfs.append(df.select(selected_columns).collect().to_pandas())
            names.append(name)
            colors.append(color)

            print("Creating Stats")
            #TODO let them select which
            stats_df=df.select([
                pl.lit(name).alias('Name'),
                pl.count('playResult').alias('Plays'),
                # pl.sum('OffensiveYardage').alias('Yards'),
                pl.mean('playResult').round(1).alias('Yards/Play'),
                pl.mean('expectedPointsAdded').round(2).alias('EPA/Play'),
                pl.mean('SuccessfulPlay').round(2).alias('Success Rate'),
                pl.mean('ExplosivePlay').round(2).alias('Explosive Rate'),
                pl.mean('StuffedPlay').round(2).alias('Stuff Rate')
            ])
            
            print("Selecting Columns: ", selected_columns)
            #TODO mess around with dataframe formatting available https://docs.streamlit.io/library/api-reference/data/st.dataframe
            selected_columns=['Name','Plays','Yards/Play','EPA/Play','Success Rate','Explosive Rate','Stuff Rate']
            stats_dfs.append(collect_df(stats_df, selected_columns, values, names))
            
        #TODO leave message if dfs = 0?
        print("Attempting to draw ridge plot")
        draw_ridgeplot(dfs, names, colors, MyFilter.group_count)
        stats_dfs = pd.concat(stats_dfs).set_index('Name')
        st.dataframe(stats_dfs,use_container_width=True)


    elif selected_page == 'Sankey':
        print("Selected Page: ", selected_page)

        st.header('Actual Personnel vs What Teams Lined Up Like')
        st.header('')

        minimum_snap_threshold = st.select_slider('Minimum Snap Percentage', options=range(0,16), format_func=lambda x: f'{x}%',  value=5) / 100
        combine_groups = st.checkbox('Combine other personnel packages into single group?')

        for i in range(1, MyFilter.group_count+1): #todo have a function for this?
            name = coalesce(filter_selections[i]['name'], 'NFL')
            color = filter_selections[i]['color']
            values = filter_selections[i]['values']
            masks = filter_selections[i]['masks']
            shared_offense=filter_selections.get(0,{}).get('values',{}).get('Offense','')
            shared_defense=filter_selections.get(0,{}).get('values',{}).get('Defense','')
            offense = values.get('Offense', '')
            defense = values.get('Defense', '')
            team = coalesce(shared_offense,shared_defense,offense,defense)

            df = add_filter_name_to_df(master_df, name)
            #TODO allow ability to select defensive team's colors
            color = hex_color_from_color_selection(color, team, df_team_info)
            logo = get_logos(team, df_team_info)

            df = filter_df(df, masks.values())
            
            # selected_columns=['FilterName', 'Metric']
            # dfs.append(collect_df(df, selected_columns, values))
            names.append(name) #TODO get rid of appends if I'm not using them; although probably better to stick them into function
            colors.append(color)
            logos.append(logo)

            draw_personnel_sankey(df, name, color, logo, minimum_snap_threshold, combine_groups)
            #st.write('_____________')

    elif selected_page == 'Heatmap':
        print("Selected Page: ", selected_page)
        st.header('Personnel Heatmap')
        st.header('')
        
        comparison_mode = st.selectbox('Mode', ['Personnel Usage of Individual Groups', 'Compare Personnel Usage Between Groups']) #TODO better names
        for i in range(1, MyFilter.group_count+1): #todo have a function for this?
            name = coalesce(filter_selections[i]['name'], 'NFL')
            color = filter_selections[i]['color']
            values = filter_selections[i]['values']
            masks = filter_selections[i]['masks']
            shared_offense=filter_selections.get(0,{}).get('values',{}).get('Offense','')
            shared_defense=filter_selections.get(0,{}).get('values',{}).get('Defense','')
            offense = values.get('Offense', '')
            defense = values.get('Defense', '')
            team = coalesce(shared_offense,shared_defense,offense,defense)

            df = add_filter_name_to_df(master_df, name)
            #TODO allow ability to select defensive team's colors
            color = hex_color_from_color_selection(color, team, df_team_info)
            logo = get_logos(team, df_team_info)

            df = filter_df(df, masks.values())
            
            dfs.append(df)
            names.append(name)
            colors.append(color)
            logos.append(logo)
        if len(dfs) < 2 and comparison_mode=='Compare Personnel Usage Between Groups':
            st.header('You must select multiple groups with the filter on the left to use this mode')
        else:
            draw_heatmap(dfs, names, colors, logos, comparison_mode)

    elif selected_page == 'Cut-Ups':
        print("Selected Page: ", selected_page)
        st.header('YouTube links to plays from each filter group')
        st.markdown('_(adblocker recommended_)')
        count_of_highlights = st.number_input('Select maximum number of videos to link:',value=5)
        touchdowns_only = st.checkbox('Touchdowns only?',value=True)
        st.markdown('_Recommended so that the play will show up on YouTube highlights_')
        for i in range(1, MyFilter.group_count+1): #todo have a function for this?
            name = coalesce(filter_selections[i]['name'], 'NFL')
            values = filter_selections[i]['values']
            masks = filter_selections[i]['masks']

            df = add_filter_name_to_df(master_df, name)

            df = filter_df(df, masks.values())
            
            # df = df.with_columns([pl.col(metric).alias('Metric')])
            # selected_columns=['FilterName', 'Metric']
            dfs.append(collect_df(df, ['Week','OffensiveTeam','DefensiveTeam','Quarter','TimeLeft', 'Touchdown'], values))
            names.append(name)
            df=dfs[i-1]
            if touchdowns_only:
                df = df[df['Touchdown']==1].reset_index(drop=True)
            df = df.sort_values(by=['Week','OffensiveTeam','Quarter','TimeLeft']).reset_index(drop=True)
            links = set()
            st.header('')
            st.header(name)
            i=0
            while len(links) <= count_of_highlights-1:
                try:
                    w = df['Week'][i]
                    o = df['OffensiveTeam'][i]
                    d = df['DefensiveTeam'][i]
                    q = df['Quarter'][i].item()
                    q = quarter_dict[q]
                    raw_time = df['TimeLeft'][i].item()
                    m = raw_time//60
                    s = f'{raw_time%60:02}'
                    md = f'{i+1}: [{o} vs {d} Week {w}, {m}:{s} left in {q}]'
                    link = f'(https://www.google.com/search?btnI=1&q=2020+week+{w}+{o}+{d}%20site:youtube.com)'.replace(' ', '_')
                    
                    if md not in links:
                        links.add(md)
                        st.markdown(md+link)
                    i+=1
            
                except:
                    break

    elif selected_page == 'About':
        print("Selected Page: ", selected_page)
        st.markdown('')
        st.markdown('')
        st.markdown('_Coming soon_')

    # except Exception as e: print(e)
        