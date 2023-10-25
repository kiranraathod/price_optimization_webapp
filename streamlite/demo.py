import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
# To build our model
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly

st.set_page_config(page_title="Price Optimization App")

@st.cache_data()
def load_csv(input_metric):
    df_input = None
    df_input = pd.DataFrame()
    df_input = pd.read_csv(input_metric, sep=',', engine='python', encoding='utf-8',
                           parse_dates=True)
    df_input['date'] = pd.to_datetime(df_input['date'])                           
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

col1, col2 = st.columns((1.3, 5))
col1.image("logo-no-background.svg", width=130 )
col2.title("Price Optimization")
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

        #df = prep_data(df)
        output = 0

#---- First part Jesus code ----
@st.cache_data  # 👈 Add the caching decorator
def transform_1():
    """
     In this part we are defining all the functions that would be used in the load_model() where is going to call 
    the Facebook's Prophet Algorithm, make the propert transformations and plot its own chart function to demonstrate the results

    """
    # Create a copy of the original DataFrame 'df' and store it in 'train'
    train = df.copy()
    
    # Convert the 'date' column in the 'train' DataFrame to datetime format
    # Please can you check your code if this step has been done, so you can drop this line of code because your already did it.
    train['date'] = pd.to_datetime(train['date'])

    # Rename the columns in the 'train' DataFrame
    train = train.rename(columns={'quantity_sold': 'y', 'date': 'ds'})

    return train

def transform_2():
    # Create a copy of the original DataFrame 'df' and store it in 'train'
    train = df.copy()

    # Create a new DataFrame 'fd' by selecting specific columns from 'train'
    fd = train[['date', 'quantity_sold'] + selected_columns]

    return fd

def preprocess_data(df):
    # With this function we are going to fill the future dates witht our latest value of the other features. (Those features are required to predict the target value)
    df = df[['ds'] + selected_columns]
    df.fillna(method='ffill', inplace=True)
    return df

def create_future_dataframe(model, periods=4, freq='W'):
    # Creating a dataframe with the new dates to predict. Depends of the user input. They have to select the period and the frequency of the new dates.
    future_data = model.make_future_dataframe(periods=periods, freq=freq)
    future_data['ds'] = future_data['ds'].dt.strftime('%Y-%m-%d')
    return future_data

# Creating a list of countries that Prophet know their holidays 
country_mapping = {
    'United States': 'US',
    'United Kingdom': 'GB',
    'Germany': 'DE',
    'France': 'FR',
    'Brazil': 'BR'}

# Creating a dictionary of the two options that users will have so they can predict daily or weekly target value
seasonality_configs = {
        "Weekly": {"name": "weekly", "period": 7, "fourier_order": 3},
        "Monthly": {"name": "monthly", "period": 30.5, "fourier_order": 5}
    }

@st.cache_data  # 👈 Add the caching decorator
def load_model(seasonality_config, selected_columns, future_periods, future_freq, selected_country):
    # Instantiate Prophet
    model_new = Prophet()
    
    # Add customizable seasonality
    model_new.add_seasonality(
        name=seasonality_config['name'],
        period=seasonality_config['period'],
        fourier_order=seasonality_config['fourier_order']
    )

    # Add selected columns as regressors
    for column in selected_columns:
        model_new.add_regressor(column)

    # Add selected holidays for the country
    if selected_country:
        two_letter_code = country_mapping.get(selected_country)
        if two_letter_code:
            model_new.add_country_holidays(country_name=two_letter_code)

    # Fit the model to the training data
    model_new.fit(train)

    # Create a future DataFrame for 4 weeks
    future_data = create_future_dataframe(model_new, future_periods, future_freq)
    
    # Bring back the base data set to concatenate with the future dataset
    fd = transform_2()
    
    # Let's merge our future data with our features
    combined_df = pd.concat([fd, future_data], axis=1)
    combined_df = preprocess_data(combined_df)

    # Predict on the 'future' dataset
    forecast_data = model_new.predict(combined_df)
    
    fig = model_new.plot(forecast_data)
    
    # Customize x-label and y-label
    plt.xlabel('Date')
    plt.ylabel('Target value')
    plt.grid(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)

    return fig

#----End first part Jesus Code-----


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
        st.line_chart(df['quantity_sold'], use_container_width=True, height=300)

st.subheader("2. Prophet Time Series Forecasting App")

# Just a message that the user has to upload a file to run the forecasting app
if input is None :
    """
        Waiting file 🔍
    """

# Main Streamlit app code
# Will run if the user uploads a file
if input is not None :
    """
        File loaded ✅
    """
    # ----- Second part Jesus code -----        
    st.caption("Parameters configuration ")
    # Selectbox to choose columns
    selected_columns = st.multiselect("Select Regressor Columns", df.columns[3:])  # Exclude 'date' from options

    # Dropdown to select the country for holidays
    selected_country = st.selectbox("Select Country for Holidays", list(country_mapping.keys()), index=None)

    # Dropdown to select seasonality
    seasonality_choice = st.radio("Choose Seasonality", ["Weekly", "Monthly"])

    # Frequency for future predictions
    future_freq_options = ['D', 'W']  # Daily, Weekly, Monthly
    future_freq = st.selectbox("Frequency for Future Predictions Daily, Weekly", future_freq_options, index=None)

    # Number of periods for future predictions
    future_periods = st.number_input("Number of Future Periods", value=2)

    # Create a train dataset
    train = transform_1()

    # Create a second dataset to combined witht the future
    fd = transform_2()

    # Load the model
    fig = load_model(seasonality_configs[seasonality_choice], selected_columns, future_periods, future_freq, selected_country)
            
    # Plot the forecast
    st.pyplot(fig)

# ----- End second part Jesus code -----        