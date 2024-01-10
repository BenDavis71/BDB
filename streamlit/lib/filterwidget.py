from dataclasses import dataclass, field
from operator import methodcaller
from typing import ClassVar

import streamlit as st
import polars as pl
import pandas as pd

def default_func(x):
    return x #easiest way of getting around needing a default function for class instance variable

@dataclass
class MyFilter:
    """This dataclass represents the filter that can be optionally enabled.

    It is created to parametrize the creation of filters from Streamlit and to keep the state."""

    # Class variables
    # table_name: ClassVar[str]
    # session: ClassVar[Session]
    # df_source: ClassVar[str]
    group_count: ClassVar[int]

    # The name to display in UI
    human_name: str
    # Corresponding column in the table
    df_column: str
    # The type of streamlit widget to generate
    widget_type: callable
    # Field to track if the filter is active. Can be used for filtering
    is_enabled: bool = False
    # max value
    _max_value: int = 0
    # String to prefix filter values with in charts
    prefix: str = ''
    # String to suffix filter values with in charts
    suffix: str = ''
    # widget values
    widget_values: dict = field(default_factory=dict)
    # widget masks
    widget_masks: dict = field(default_factory=dict)
    # widget options
    widget_options: dict = ()
    # function used to format string in sliders
    format_func: callable = default_func
    # how to handle a unique widget such as passing concepts
    special_type: str = 'default_func'

    def __post_init__(self):
        if self.widget_type not in (st.slider, st.select_slider, st.checkbox, st.multiselect):
            raise NotImplemented

        if self.widget_type is st.select_slider:
            self._max_value = (
                # self.session.table(MY_TABLE)
                # .select(max(col(self.df_column)))
                # .collect()[0][0]
                100
            )

    @property
    def max_value(self):
        return self._max_value

    def get_filter_value(self):
        return st.session_state.get(self.human_name)

    def enable(self):
        self.is_enabled = True

    def disable(self):
        self.is_enabled = False

    def create_widget(self, i):
        if self.widget_type in [st.slider, st.select_slider]:
            label = self.human_name
        elif self.widget_type is st.checkbox:
            label = ''
            st.markdown(f'<p class="little-font">{self.human_name}</p>', unsafe_allow_html=True)
        else:
            label = f'Choose {self.human_name}'
        widget_kwargs = dict(label=label, key=f'{self.human_name}_{i}')
        
        widget_kwargs.update(self.widget_options)
        
        self.widget_values[i] = self.widget_type(**widget_kwargs)

    def exclude_widget(self, i):
        is_excluded = st.checkbox(label='', key=f'{self.human_name}_exclusion_{i}')

        return self.get_final_selections(i, is_excluded)

    def get_final_selections(self, i, is_excluded):
        if self.widget_values[i]:
            if self.special_type=='any_concepts': #TODO more elegant
                concept_masks=[]
                for concept in self.widget_values[i]:
                    concept=concept.replace(' ','')
                    concept_masks.append(pl.col(concept).is_not_null())
                
                self.widget_masks[i]=pl.any(concept_masks)

                values=self.widget_values[i]
                conjunction = ' or ' if len(values) > 1 else ''
                generated_name_component = self.prefix + ', '.join(values[:-1]) + conjunction + values[-1] + self.suffix
                if is_excluded:
                    self.widget_masks[i], generated_name_component = self.invert_values(i, generated_name_component)
                    self.widget_values[i] = ['Not'] + self.widget_values[i]
                return self.widget_values[i], self.widget_masks[i], generated_name_component

            elif self.special_type=='all_concepts': #TODO more elegant
                concept_masks=[]
                for concept in self.widget_values[i]:
                    concept=concept.replace(' ','')
                    concept_masks.append(pl.col(concept).is_not_null())
                
                self.widget_masks[i]=pl.all(concept_masks)

                values=self.widget_values[i]
                conjunction = ' and ' if len(values) > 1 else ''
                generated_name_component = self.prefix + ', '.join(values[:-1]) + conjunction + values[-1] + self.suffix
                if is_excluded:
                    self.widget_masks[i], generated_name_component = self.invert_values(i, generated_name_component)
                    self.widget_values[i] = ['Not'] + self.widget_values[i]
                return self.widget_values[i], self.widget_masks[i], generated_name_component

            if self.special_type=='any_routes': #TODO more elegant
                route_masks=[]
                for route in self.widget_values[i]:
                    route_masks.append(pl.col('Routes').list.contains(route))
                
                self.widget_masks[i]=pl.any(route_masks)

                values=self.widget_values[i]
                conjunction = ' or ' if len(values) > 1 else ''
                generated_name_component = self.prefix + ', '.join(values[:-1]) + conjunction + values[-1] + self.suffix
                if is_excluded:
                    self.widget_masks[i], generated_name_component = self.invert_values(i, generated_name_component)
                    self.widget_values[i] = ['Not'] + self.widget_values[i]
                return self.widget_values[i], self.widget_masks[i], generated_name_component

            elif self.special_type=='all_routes': #TODO more elegant
                route_masks=[]
                for route in self.widget_values[i]:
                    route_masks.append(pl.col('Routes').list.contains(route))
                
                self.widget_masks[i]=pl.all(route_masks)

                values=self.widget_values[i]
                conjunction = ' and ' if len(values) > 1 else ''
                generated_name_component = self.prefix + ', '.join(values[:-1]) + conjunction + values[-1] + self.suffix
                if is_excluded:
                    self.widget_masks[i], generated_name_component = self.invert_values(i, generated_name_component)
                    self.widget_values[i] = ['Not'] + self.widget_values[i]
                return self.widget_values[i], self.widget_masks[i], generated_name_component

            elif self.widget_type is st.multiselect:
                self.widget_masks[i]=pl.col(f'{self.df_column}').is_in(self.widget_values[i])
                if 'Offensive Personnel' in self.human_name:
                    self.widget_values[i] = [f'{x}p' for x in self.widget_values[i]]
                generated_name_component = self.prefix + ', '.join(self.widget_values[i]) + self.suffix
                if is_excluded:
                    self.widget_masks[i], generated_name_component = self.invert_values(i, generated_name_component)
                    self.widget_values[i] = ['Not'] + self.widget_values[i]
                return self.widget_values[i], self.widget_masks[i], generated_name_component

            elif self.widget_type is st.checkbox:
                self.widget_masks[i]=pl.col(f'{self.df_column}')
                generated_name_component = self.human_name
                if is_excluded:
                    self.widget_masks[i], generated_name_component = self.invert_values(i, generated_name_component)
                    self.widget_values[i] = not self.widget_values[i]
                return self.widget_values[i], self.widget_masks[i], generated_name_component

            elif self.widget_type in [st.slider, st.select_slider]:
                self.widget_masks[i]=pl.col(f'{self.df_column}').is_between(*sorted(self.widget_values[i]))
                if self.widget_values[i] == tuple(self.widget_options['value']):
                    generated_name_component=''
                else: 
                    generated_name_component = self.prefix + self.format_slider(i) + self.suffix #TODO dict that turns 1 into 1st etc
                if is_excluded:
                    self.widget_masks[i], generated_name_component = self.invert_values(i, generated_name_component)
                    self.widget_values[i] = not self.widget_values[i]
                return self.widget_values[i], self.widget_masks[i], generated_name_component
        
        return None, True, ''

    def invert_values(self, i, generated_name_component):
        return  ~self.widget_masks[i],  'Non-' + generated_name_component

    def format_slider(self, i):
        if len(set(self.widget_values[i]))==1:
            self.widget_values[i]=self.widget_values[i][:1]
        if self.format_func != default_func:
            self.widget_values[i]=[self.format_func(x) for x in self.widget_values[i]]
        else:
            self.widget_values[i]=[str(x) for x in self.widget_values[i]]
        return '-'.join(self.widget_values[i])
        

    def __getitem__(self, item):
        return getattr(self, item)
