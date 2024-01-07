
from dataclasses import dataclass, field
from operator import methodcaller
from typing import ClassVar

import streamlit as st
import polars as pl
import pandas as pd


def filter_df(df, masks, play_grain=False):
    for mask in masks:
        df=df.filter(mask)
    if play_grain:
        df = df.unique(subset='UniqueID')
    return df


@st.cache_data #values is an arg in order to force a rerun when the previous filters have changed but rely on the cache otherwise
def get_options(_df,column,values):
    return sorted(_df.select(column).drop_nulls().unique().collect().get_columns()[0].to_list())


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

    def __post_init__(self):
        if self.widget_type not in (st.select_slider, st.checkbox, st.multiselect):
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

    def get_filter_value_deprecated(self):
        """Custom unpack function that retrieves the value of the filter
        from session state in a format compatible with self.df_method"""
        val = st.session_state.get(self.human_name)
        if self.widget_type is st.checkbox:
            # For .eq
            return dict(bool=val)
        if self.widget_type is st.multiselect:
            # For .eq
            return dict(other=val)
        elif self.widget_type is st.select_slider:
            # For .between
            return dict(lower_bound=val[0], upper_bound=val[1])
        else:
            raise NotImplemented

    def enable(self):
        self.is_enabled = True

    def disable(self):
        self.is_enabled = False

    def create_widget(self, df, i, filter_selection):
        if self.widget_type is st.select_slider:
            label = {self.human_name}
        elif self.widget_type is st.checkbox:
            label = ''
            st.markdown(f'<p class="little-font">{self.human_name}</p>', unsafe_allow_html=True)
        else:
            label = f'Choose {self.human_name}'
        widget_kwargs = dict(label=label, key=f'{self.human_name}_{i}')
        
        if self.widget_type is st.select_slider:
            widget_kwargs.update(
                dict(
                    options=list(range(self.max_value + 1)),
                    value=(0, self.max_value),
                )
            )
        elif self.widget_type is st.multiselect:
            filtered_df=filter_df(df, filter_selection['masks'].values())
            self.widget_options={'options':get_options(filtered_df,self.df_column,filter_selection['values'])}
            widget_kwargs.update(self.widget_options)
        
        self.widget_values[i] = self.widget_type(**widget_kwargs)

    def exclude_widget(self, i):
        is_excluded = st.checkbox(label='', key=f'{self.human_name}_exclusion_{i}')

        return self.get_final_selections(i, is_excluded)

    def get_final_selections(self, i, is_excluded):
        if self.widget_values[i]:
            if self.widget_type is st.multiselect:
                self.widget_masks[i]=pl.col(f'{self.df_column}').is_in(self.widget_values[i])
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
        
        return None, True, ''

    def invert_values(self, i, generated_name_component):
        return  ~self.widget_masks[i],  'Non-' + generated_name_component

    def __getitem__(self, item):
        return getattr(self, item)