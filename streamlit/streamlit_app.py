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

@st.cache_data(persist=False, show_spinner=False)
def get_data():
    # read all data
    players = pl.scan_parquet('Data/players.parquet')
    plays = pl.scan_parquet('Data/plays.parquet')
    games = pl.scan_parquet('Data/games.parquet')
    tracking = pl.scan_parquet('Data/tracking_week_*.parquet')
    play_results = pl.scan_parquet('Data/results.parquet')
    team_info = pl.read_csv('Data/teams_colors_logos.csv')

    return players, plays, games, tracking, play_results, team_info

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

def get_item_from_team_info_df(selection, team, _df_team_info):
    return _df_team_info.filter(pl.col('team_abbr')==pl.lit(team)).select(selection).item()

# @st.cache_data
def hex_color_from_color_selection(selection, team, _df_team_info):
    if len(team) == 1:
        team=team[0]
    if selection == 'Team Color 1':
        try:
            return get_item_from_team_info_df('team_color', team, _df_team_info) 
        except:
            return '#013369'
    elif selection == 'Team Color 2':
        try:
            return get_item_from_team_info_df('team_color2', team, _df_team_info) 
        except:
            return '#D50A0A'
    elif selection == 'Team Color 3':
        try:
            return get_item_from_team_info_df('team_color3', team, _df_team_info) 
        except:
            return '#000000'
    elif selection == 'Team Color 4':
        try:
            return get_item_from_team_info_df('team_color4', team, _df_team_info) 
        except:
            return '#A5ACAF'
    return selection


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
@st.cache_data
def collect_df(_df, selected_columns, *args):
    return  _df.select(selected_columns).collect().to_pandas()

def add_filter_name_to_df(df, name):
    return df.select([pl.lit(name).alias(('FilterName')), pl.all()])

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
    players, plays, games, tracking, play_results, team_info = get_data()

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
        MyFilter(
            human_name='Box, Spill, or Dent',
            df_column='defenseType',
            widget_type=st.multiselect,
            widget_options={'options':['Box','Spill','Dent']}
        ),
        MyFilter(
            human_name='Box Type',
            df_column='boxType',
            suffix = ' Box',
            widget_type=st.multiselect,
            widget_options={'options':['Heavy','Light']}
        ),
        MyFilter(
            human_name='Playside Front Characteristics',
            df_column='playsideFrontCharacteristics',
            widget_type=st.multiselect,
            widget_options={'options':get_options(play_results,'playsideFrontCharacteristics')}
        ),
        MyFilter(
            human_name='Playside Surface',
            df_column='playsideSurface',
            suffix = ' Man Surface',
            widget_type=st.slider,
            widget_options={'min_value':2,'max_value':5,'value':[2,5]}
        ),
    )

    # st.write(play_results.schema)
    # st.write(get_options(play_results,'defenseType'))
    

    print("Loading filters done")

    play_results=play_results.with_columns([
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
    # st.title('Pull the Plug')
    st.image('https://github.com/BenDavis71/BDB/blob/da386305f8711aa8f6eeb71662425ff3e7e0c2ca/assets/littleLogo.png?raw=true')
    options = ['Ridgeline', 'Play Animation', 'About']
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
            color = hex_color_from_color_selection(color, team, team_info)

            df = filter_df(df, masks.values())


            # start ridgeline function here?
            metric = 'expectedPointsAdded' #TODO bring out of loop? and is the below stupid?
            
            # print("joining play_results to plays to get EPA")
            # df = df.join(plays, on=['gameId','playId'], how='left')
            # print("finished joining play_results to plays to get EPA")  

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


    elif selected_page == 'Play Animation':
        print("Selected Page: ", selected_page)

        # normalize orientation 'o' and direction 'dir'
        # convert 'NA' to 0
        replacement_values = {'NA': '0'}
        tracking = tracking.with_columns(
            pl.col('o').apply(lambda x: replacement_values.get(x, x)),
        )

        tracking=tracking.with_columns([
            pl.when(pl.col('playDirection')=='right').then(pl.col('o').cast(pl.Float64)).otherwise((180+pl.col('o').cast(pl.Float64))%360).alias('firstAdjustedO'),
        ])

        tracking=tracking.with_columns([
            pl.when(pl.col('firstAdjustedO') <= 180).then(180-pl.col('firstAdjustedO')).otherwise(540-pl.col('firstAdjustedO')).alias('adjustedO')
        ])

        tracking=tracking.with_columns([
            pl.when(pl.col('playDirection')=='right').then(53.3-pl.col('y')).otherwise(pl.col('y')).alias('x'),
            pl.when(pl.col('playDirection')=='right').then(pl.col('x')).otherwise(120-pl.col('x')).alias('y')
        ])

        players = players.with_columns([pl.col('nflId').cast(pl.Utf8)])

        def hex_to_rgb_array(hex_color):
            '''take in hex val and return rgb np array'''
            return np.array(tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))) 

        def ColorDistance(hex1,hex2):
            '''d = {} distance between two colors(3)'''
            if hex1 == hex2:
                return 0
            rgb1 = hex_to_rgb_array(hex1)
            rgb2 = hex_to_rgb_array(hex2)
            rm = 0.5*(rgb1[0]+rgb2[0])
            d = abs(sum((2+rm,4,3-rm)*(rgb1-rgb2)**2))**0.5
            return d

        def ColorPairs(team1,team2):
            color_array_1 = team_colors[team1]
            color_array_2 = team_colors[team2]

            # If color distance is small enough then flip color order
            if ColorDistance(color_array_1[0],color_array_2[0])<500:
                return {team1:[color_array_1[0],color_array_1[1]],team2:[color_array_2[1],color_array_2[0]],'football':team_colors['football']}
            else:
                return {team1:[color_array_1[0],color_array_1[1]],team2:[color_array_2[0],color_array_2[1]],'football':team_colors['football']}

        def animate_play(games,tracking_df,play_df,players,gameId,playId, highlighted_players = []):
            selected_game_df = games[games.gameId==gameId].copy()
            selected_play_df = play_df[(play_df.playId==playId)&(play_df.gameId==gameId)].copy()
            
            tracking_players_df = pd.merge(tracking_df,players,how="left",on = "nflId")
            selected_tracking_df = tracking_players_df[(tracking_players_df.playId==playId)&(tracking_players_df.gameId==gameId)].copy()

            sorted_frame_list = selected_tracking_df.frameId.unique()
            sorted_frame_list.sort()
            
            # get good color combos
            team_combos = list(set(selected_tracking_df.club.unique())-set(["football"]))
            
            color_orders = ColorPairs(team_combos[0], team_combos[1])
            
            # get play General information 
            line_of_scrimmage = np.where(selected_tracking_df.playDirection.values[0] == "right", selected_play_df.absoluteYardlineNumber.values[0], 120 - selected_play_df.absoluteYardlineNumber.values[0])
            
            ## Fixing first down marker issue from last year
            if selected_tracking_df.playDirection.values[0] == "right":
                first_down_marker = line_of_scrimmage - selected_play_df.yardsToGo.values[0]
            else:
                first_down_marker = line_of_scrimmage + selected_play_df.yardsToGo.values[0]
            down = selected_play_df.down.values[0]
            quarter = selected_play_df.quarter.values[0]
            gameClock = selected_play_df.gameClock.values[0]
            playDescription = selected_play_df.playDescription.values[0]
            # Handle case where we have a really long Play Description and want to split it into two lines
            if len(playDescription.split(" "))>15 and len(playDescription)>115:
                playDescription = " ".join(playDescription.split(" ")[0:16]) + "<br>" + " ".join(playDescription.split(" ")[16:])

            # initialize plotly start and stop buttons for animation
            updatemenus_dict = [
                {
                    "buttons": [
                        {
                            "args": [None, {"frame": {"duration": 100, "redraw": False},
                                        "fromcurrent": True, "transition": {"duration": 0}}],
                            "label": "Play",
                            "method": "animate"
                        },
                        {
                            "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                            "mode": "immediate",
                                            "transition": {"duration": 0}}],
                            "label": "Pause",
                            "method": "animate"
                        }
                    ],
                    "direction": "left",
                    "pad": {"r": 10, "t": 87},
                    "showactive": False,
                    "type": "buttons",
                    "x": 0.1,
                    "xanchor": "right",
                    "y": 0,
                    "yanchor": "top"
                }
            ]
            # initialize plotly slider to show frame position in animation
            sliders_dict = {
                "active": 0,
                "yanchor": "top",
                "xanchor": "left",
                "currentvalue": {
                    "font": {"size": 20},
                    "prefix": "Frame:",
                    "visible": True,
                    "xanchor": "right"
                },
                "transition": {"duration": 10, "easing": "cubic-in-out"},
                "pad": {"b": 10, "t": 50},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "steps": []
            }


            frames = []
            for frameId in sorted_frame_list:
                data = []
                # Add Numbers to Field 
                data.append(
                    go.Scatter(
                        y=np.arange(20,110,10), 
                        x=[5]*len(np.arange(20,110,10)),
                        mode='text',
                        text=list(map(str,list(np.arange(20, 61, 10)-10)+list(np.arange(40, 9, -10)))),
                        textfont_size = 30,
                        textfont_family = "Courier New, monospace",
                        textfont_color = "#ffffff",
                        showlegend=False,
                        hoverinfo='none'
                    )
                )
                data.append(
                    go.Scatter(
                        y=np.arange(20,110,10), 
                        x=[53.5-5]*len(np.arange(20,110,10)),
                        mode='text',
                        text=list(map(str,list(np.arange(20, 61, 10)-10)+list(np.arange(40, 9, -10)))),
                        textfont_size = 30,
                        textfont_family = "Courier New, monospace",
                        textfont_color = "#ffffff",
                        showlegend=False,
                        hoverinfo='none'
                    )
                )
                # Add line of scrimage 
                data.append(
                    go.Scatter(
                        y=[line_of_scrimmage,line_of_scrimmage], 
                        x=[0,53.5],
                        line_dash='dash',
                        line_color='blue',
                        showlegend=False,
                        hoverinfo='none'
                    )
                )
                # # Add First down line 
                # data.append(
                #     go.Scatter(
                #         y=[first_down_marker,first_down_marker], 
                #         x=[0,53.5],
                #         line_dash='dash',
                #         line_color='yellow',
                #         showlegend=False,
                #         hoverinfo='none'
                #     )
                # )
                # Add Endzone Colors 
                endzoneColors = {0:color_orders[selected_game_df.homeTeamAbbr.values[0]][0],
                                110:color_orders[selected_game_df.visitorTeamAbbr.values[0]][0]}
                for x_min in [0,110]:
                    data.append(
                        go.Scatter(
                            y=[x_min,x_min,x_min+10,x_min+10,x_min],
                            x=[0,53.5,53.5,0,0],
                            fill="toself",
                            fillcolor=endzoneColors[x_min],
                            mode="lines",
                            line=dict(
                                color="white",
                                width=3
                                ),
                            opacity=1,
                            showlegend= False,
                            hoverinfo ="skip"
                        )
                    )
                # Plot Players
                # Note: references to "x" and "y" are using "adjustedX" and "adjustedY"
                for team in selected_tracking_df.club.unique():
                    plot_df = selected_tracking_df[(selected_tracking_df.club==team)&(selected_tracking_df.frameId==frameId)].copy()
                    if team != "football":
                        hover_text_array=[]
                        for nflId in plot_df.nflId:
                            selected_player_df = plot_df[plot_df.nflId==nflId]

                            if selected_player_df.jerseyNumber.values[0] in highlighted_players:
                                vision_cone = get_vision_cone_coordinates(selected_player_df)
                                data.append(go.Scatter(
                                    x=vision_cone[0], y=vision_cone[1], mode='lines', line_shape='spline', fill='toself',  # Fill the area inside the polygon
                                    fillcolor='rgba(255,255,153,0.6)', line=dict(color='rgba(255,255,153,0)', width=2), showlegend=False)
                                )
                                data.append(go.Scatter(
                                    x=vision_cone[2], y=vision_cone[3], mode='lines', line_shape='spline', fill='toself',  # Fill the area inside the polygon
                                    fillcolor='rgba(255,255,153,0.6)', line=dict(color='rgba(255,255,153,0)', width=2), showlegend=False)
                                )
                            hover_text_array.append("nflId:{}<br>displayName:{}<br>".format(selected_player_df["nflId"].values[0],
                                                                                            selected_player_df["displayName"].values[0]))
                        data.append(go.Scatter(x=plot_df["x"], y=plot_df["y"],mode = 'markers',marker=go.scatter.Marker(
                                                                                                    color=color_orders[team][0],
                                                                                                    line=go.scatter.marker.Line(width=2,
                                                                                                                    color=color_orders[team][1]),
                                                                                                    size=10),
                                                name=team,hovertext=hover_text_array,hoverinfo="text"))
                    else:
                        data.append(go.Scatter(x=plot_df["x"], y=plot_df["y"],mode = 'markers',marker=go.scatter.Marker(
                                                                                                    color=color_orders[team][0],
                                                                                                    line=go.scatter.marker.Line(width=2,
                                                                                                                    color=color_orders[team][1]),
                                                                                                    size=10),
                                                name=team,hoverinfo='none'))
                # add frame to slider
                slider_step = {"args": [
                    [frameId],
                    {"frame": {"duration": 100, "redraw": False},
                    "mode": "immediate",
                    "transition": {"duration": 0}}
                ],
                    "label": str(frameId),
                    "method": "animate"}
                sliders_dict["steps"].append(slider_step)
                frames.append(go.Frame(data=data, name=str(frameId)))

            scale=8
            layout = go.Layout(
                autosize=False,
                height=120*scale,
                width=60*scale,
                yaxis=dict(range=[0, 120], autorange=False, tickmode='array',tickvals=np.arange(10, 111, 5).tolist(),showticklabels=False),
                xaxis=dict(range=[0, 53.3], autorange=False,showgrid=False,showticklabels=False),

                plot_bgcolor='#00B140',
                updatemenus=updatemenus_dict,
                sliders = [sliders_dict]
            )

            fig = go.Figure(
                data=frames[0]["data"],
                layout= layout,
                frames=frames[1:]
            )
            # # Create First Down Markers 
            # for y_val in [0,53]:
            #     fig.add_annotation(
            #             y=first_down_marker,
            #             x=y_val,
            #             text=str(down),
            #             showarrow=False,
            #             font=dict(
            #                 family="Courier New, monospace",
            #                 size=16,
            #                 color="black"
            #                 ),
            #             align="center",
            #             bordercolor="black",
            #             borderwidth=2,
            #             borderpad=4,
            #             bgcolor="#ff7f0e",
            #             opacity=1
            #             )
            
            # Add Team Abbreviations in EndZone's
            for y_min in [0,110]:
                if y_min == 0:
                    teamName=selected_game_df.homeTeamAbbr.values[0]
                else:
                    teamName=selected_game_df.visitorTeamAbbr.values[0]
                    
                fig.add_annotation(
                    y=y_min+5,
                    x=53.5/2,
                    text=teamName,
                    showarrow=False,
                    font=dict(
                        family="Courier New, monospace",
                        size=32,
                        color="White"
                        ),
                    textangle = 0
                )
                
            buffer = 15
            fb = selected_tracking_df[selected_tracking_df['club']=='football']
            origin_fb_loc = fb.iloc[0]

            # Can use this to zoom in but the vision cones look off
            max_diff = 0
            if (abs(fb['x'].max()-origin_fb_loc['x']) > abs(fb['x'].min()-origin_fb_loc['x'])):
                max_diff = abs(fb['x'].max()-origin_fb_loc['x'])
            else:
                max_diff = abs(fb['x'].min()-origin_fb_loc['x'])

            # fig.update_layout(updatemenus=[dict(x=2, y=2)])
            return fig

        def get_vision_cone_coordinates(player):
            import math
            DIST = 3
            DIST_MULTIPLIER = .95
            ANGLE = 22.5

            player_x = player['x'].iloc[0]
            player_y = player['y'].iloc[0]
            player_orientation = float(player['adjustedO'].iloc[0])

            # bad design but it's ok for now
            x_values = []
            y_values = []
            
            x1_values = []
            y1_values = []
            
            x1 = player_x + (DIST) * math.cos(math.radians(player_orientation+ANGLE))
            y1 = player_y + (DIST) * math.sin(math.radians(player_orientation+ANGLE))

            x2 = player_x + (DIST) * math.cos(math.radians(player_orientation-ANGLE))
            y2 = player_y + (DIST) * math.sin(math.radians(player_orientation-ANGLE))

            x1_with_multiplier = player_x + (DIST*DIST_MULTIPLIER) * math.cos(math.radians(player_orientation+ANGLE))
            y1_with_multiplier = player_y + (DIST*DIST_MULTIPLIER) * math.sin(math.radians(player_orientation+ANGLE))
            x2_with_multiplier = player_x + (DIST*DIST_MULTIPLIER) * math.cos(math.radians(player_orientation+ANGLE))
            y2_with_multiplier = player_y + (DIST*DIST_MULTIPLIER) * math.sin(math.radians(player_orientation+ANGLE))

            x1 = player_x + (DIST*DIST_MULTIPLIER) * math.cos(math.radians(player_orientation+ANGLE))
            y1 = player_y + (DIST*DIST_MULTIPLIER) * math.sin(math.radians(player_orientation+ANGLE))

            x3 = player_x + (DIST) * math.cos(math.radians(player_orientation))
            y3 = player_y + (DIST) * math.sin(math.radians(player_orientation))

            # print("hyp1: ", high_on_potenuse, " player_orientation: ", player_orientation)
            # print("player_x ", player_x, " player_y ", player_y)
            # print("x1: ", x1, " y1: ", y1)
            # print("x2: ", x2, " y2: ", y2)

            x_values.append(x1)
            y_values.append(y1)

            x_values.append(x3)
            y_values.append(y3)
            
            x_values.append(x2)
            y_values.append(y2)

            x1_values.append(x1)
            y1_values.append(y1)
            x1_values.append(player_x)
            y1_values.append(player_y)
            x1_values.append(x2)
            y1_values.append(y2)

            # print("player: ", player_x, ", ", player_y)
            # print(x3_values)
            # print(y3_values)
            
            return (x_values, y_values, x1_values, y1_values)

        for i in range(1): #todo have a function for this?
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
            color = hex_color_from_color_selection(color, team, team_info)

            df = filter_df(df, masks.values())
            st.write(df.schema)

        tracking = tracking.filter(pl.col('gameId')==2022091107).filter(pl.col('playId')==1841)

        st.write(defenseType)

        st.plotly_chart(animate_play(games.collect().to_pandas(), tracking.collect().to_pandas(), plays.collect().to_pandas(), players.collect().to_pandas(), 2022091107, 1841))
        

    elif selected_page == 'About':
        print("Selected Page: ", selected_page)
        st.markdown('')
        st.markdown('')
        st.markdown('_Coming soon_')

    # except Exception as e: print(e)
        