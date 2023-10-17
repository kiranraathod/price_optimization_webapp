import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import base64
import itertools
import matplotlib.pyplot as plt
# To build our model
import tqdm as notebook_tqdm
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly

st.set_page_config(page_title="Price Optimization App")

@st.cache_data()
def load_csv(input_metric):
    df_input = None
    df_input = pd.DataFrame()
    df_input = pd.read_csv(input_metric, sep=',', engine='python', encoding='utf-8',
                           parse_dates=True)
    return df_input.copy()

def prep_data(df):

    df_input = df.rename({date_col: "ds", metric_col: "y"},
                         errors='raise', axis=1)
    st.markdown(
        "The selected date column is now labeled as **ds** and the values columns as **y**")
    df_input = df_input[['ds', 'y']]
    df_input = df_input.sort_values(by='ds', ascending=True)
    df_input['ds'] = pd.to_datetime(df_input['ds'])
    df_input['y'] = df_input['y'].astype(float)
    return df_input.copy()



st.title('Price Optimization')

st.write('This app makes it easy to optimize your prices.')

    # caching.clear_cache()
df = pd.DataFrame()

st.subheader('1. Data loading ')
st.write("Import a time series csv file.")
with st.expander("Data format"):
        st.markdown("The dataset can contain multiple columns, but you will need to select a column to be used as dates and a second column containing the metric you wish to forecast. The columns will be renamed as **ds** and **y** to be compliant with Prophet. Even though we are using the default Pandas date parser, the ds (datestamp) column should be of a format expected by Pandas, ideally `YYYY-MM-DD` for a date or `YYYY-MM-DD HH:MM:SS` for a timestamp. The y column must be numeric.")
        st.write("For example, see this table format.")
        example_df = pd.read_csv('w_data.csv')
        st.write(example_df.head())
        st.image('input_format.png', caption='Data Format Example', use_column_width=True)

input = st.file_uploader('')

if input:
    with st.spinner('Loading data..'):
        df = load_csv(input)

        st.write("Columns:")
        st.write(list(df.columns))
        columns = list(df.columns)

        col1, col2 = st.columns(2)
        with col1:
            date_col = st.selectbox(
                "Select date column",
                options=columns,
                key="date"
            )
        with col2:
            metric_col = st.selectbox(
                "Select values column",
                options=columns,
                key="values"
            )

        df = prep_data(df)
        output = 0

if st.checkbox('Chart data', key='show'):
    with st.spinner('Plotting data..'):
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(df)

        with col2:
            st.write("Dataframe description:")
            st.write(df.describe())

    try:
        line_chart = alt.Chart(df).mark_line().encode(
            x=alt.X('ds:T', title='Date'),
            y=alt.Y('y:Q', title='Target'),
            tooltip=['ds:T', 'y']
        ).properties(title="Time series preview").interactive()
        st.altair_chart(line_chart, use_container_width=True)

    except Exception as e:
        st.line_chart(df['y'], use_container_width=True, height=300)
        
        
st.subheader("2.Parameters configuration ")

with st.form("config"):

        with st.container():
            
            with st.expander("Trend components"):
                trend_components = ['Daily', 'Weekly', 'Monthly', 'Yearly']

                with st.container():
                    selected_trend = st.selectbox(
                        label="Select trend", options=trend_components,index=None)

                trend = ''  # Initialize the trend variable

                if selected_trend == 'Daily':
                    trend = 'daily'
                elif selected_trend == 'Weekly':
                    trend = 'weekly'
                elif selected_trend == 'Monthly':
                    trend = 'monthly'
                elif selected_trend == 'Yearly':
                    trend = 'yearly'

            
            with st.expander("Horizon"):
                periods_input = st.number_input(f'Select how many future periods {trend} to forecast.', 
                                                min_value=1, max_value=366, value=90)

            with st.expander('Holidays'):
                countries = ['Country name', 'Italy', 'Spain', 'United States', 'France', 'Germany', 'Ukraine']

                with st.container():
                    selected_country = st.selectbox(
                        label="Select country", options=countries)

                    # You should assign the country code to a variable.
                    country_code = ''
                    
                    if selected_country == 'Italy':
                        country_code = 'IT'
                        
                    elif selected_country == 'Spain':
                        country_code = 'ES'
                        
                    elif selected_country == 'United States':
                        country_code = 'US'
                    
                    elif selected_country == 'France':
                        country_code = 'FR'
                        
                    elif selected_country == 'Germany':
                        country_code = 'DE'

                    if selected_country == 'Germany':
                        country_code = 'BR'

            with st.expander('Train'):
                train = df.copy()  # You need to call the copy() method to create a copy of the DataFrame.
                if train is not None and not train.empty:
                    st.write(list(train.columns))
                else:
                    st.write("The 'train' DataFrame is empty or None.")

            # Jesus' part of work


                
            