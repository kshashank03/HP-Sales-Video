import os
import random

import pandas as pd
import streamlit as st

from prophet import Prophet
import altair as alt

st.set_page_config(layout="wide")
@st.cache_data
def load_data():
    stock_list = pd.read_csv("best_companies_stock_info.csv", delimiter='\t')
    stock_prices = pd.read_csv("stock_prices.csv")
    stock_info = pd.merge(stock_prices, stock_list, 'inner', on='SecuritiesCode')
    stock_info["Date"] = pd.to_datetime(stock_info["Date"])
    return stock_info

with st.expander("Welcome 👋", expanded=True):
    st.markdown("### We created a powerful dashboard that allows users to select top Japanese stocks and find non-correlating assets in real-time.")
    st.markdown("* This was made possible through the use of the Z by HP computer, which enables us to dynamically run forecasting models using the Meta Prophet library")
    st.markdown("* We used a Generative Pre-trained Transformer to create summaries and blurbs on why certain stocks might not be correlated")
    st.markdown("With the ability to run these models in real-time, users can make informed decisions and adjust their investments as needed to stay ahead of the market. The Z by HP's high-performance processing capabilities, coupled with its advanced data visualization capabilities, made it the perfect tool for creating this dashboard, allowing users to explore investment opportunities and gain a competitive edge in the ever-changing world of finance.")

with st.sidebar:
    data_load_state = st.text('Loading data...')
    data = load_data()
    data_load_state.text("Done! (using st.cache_data)")
    company = st.selectbox(label="Company", options=data["Name"].unique())
    periods = st.slider('How many days into the future do you want to predict?', 10, 700, 90, 1)
    preds = 16 * periods
    st.write(f"Select a company using the dropdown above, if the dashboard errors out, hit the hamburger menu on the upper right and 'Rerun'. Every run will generate {preds} new predicions spread over 16 charts")
    
new_data = data[data["Name"].isin([company])].reset_index(drop=True)
st.markdown(f""" 
# {new_data["Name"][0]}
#### Summary: 
{new_data["Summary"][0]}

""")

# periods = 300

def chart_creator(data, col, periods):
    forecast_df = data[['Date', col]].rename(columns={'Date':'ds', col:'y'})
    model = Prophet()
    model.fit(forecast_df)
    future_dates = model.make_future_dataframe(periods=periods, freq='D')
    forecast_df = model.predict(future_dates)
    forecast_df = forecast_df.tail(int(periods *  2))
    base = alt.Chart(forecast_df).mark_line().encode(
        x='ds',
        y='yhat'
    )
    bounds = alt.Chart(forecast_df).mark_area(opacity=0.3).encode(
        x=alt.X('ds', title='Date'),
        y=alt.Y('yhat_upper', title='Price (JPY)', scale=alt.Scale(zero=False)),
        y2='yhat_lower'
    )
    v_df = pd.DataFrame({'v': [forecast_df['ds'].iloc[len(forecast_df) - periods]]})
    # Create a chart with a vertical rule at the point v
    v_rule = alt.Chart(v_df).mark_rule(color='red').encode(
        x='v'
    )
    return base + bounds + v_rule

open_chart_components = chart_creator(new_data, 'Open', periods)
high_chart_components = chart_creator(new_data, 'High', periods)
low_chart_components = chart_creator(new_data, 'Low', periods)
close_chart_components = chart_creator(new_data, 'Close', periods)
volume_chart_components = chart_creator(new_data, 'Volume', periods)

col1, col2 = st.columns(2)

with col1:
   st.header("Open")
   open_chart = st.altair_chart(open_chart_components, use_container_width=True)
   st.header("High")
   high_chart = st.altair_chart(high_chart_components, use_container_width=True)

with col2:
   st.header("Close")
   close_chart = st.altair_chart(close_chart_components, use_container_width=True)
   st.header("Volume")
   volume_chart = st.altair_chart(volume_chart_components, use_container_width=True)

st.header("Non-correlated Asset Explorer")
my_bar = st.progress(0.0, text="Loading models")
tabs = 5

holding_dict = {}
non_corr_blurbs = pd.read_csv("non_correlation_gen.csv")

for perc, corp in enumerate(random.choices(data[data['Name'] != company]["Name"].unique(), k=tabs)):
    new_new_data = data[data["Name"] == corp].reset_index(drop=True)
    my_bar.progress(float((perc) / (tabs - 1)), text="Loading models")
    blurb = non_corr_blurbs.sample(1)['blurb'].values[0]
    blurb = blurb.replace("Company X", company)
    blurb = blurb.replace("Company Y", corp)
    holding_dict[corp] = [chart_creator(new_new_data, 'Open', periods),
                          chart_creator(new_new_data, 'High', periods),
                          chart_creator(new_new_data, 'Close', periods),
                          chart_creator(new_new_data, 'Volume', periods),
                          blurb
                          ]
print(holding_dict.keys())
tab1, tab2, tab3 = st.tabs(list(holding_dict.keys())[:3])

with tab1:
    st.subheader(holding_dict[list(holding_dict.keys())[0]][4])
    col1, col2 = st.columns(2)

    with col1:
        
        st.header("Open")
        open_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[0]][0], use_container_width=True)
        st.header("High")
        high_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[0]][1], use_container_width=True)

    with col2:
        st.header("Close")
        close_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[0]][2], use_container_width=True)
        st.header("Volume")
        volume_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[0]][3], use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.header("Open")
        open_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[1]][0], use_container_width=True)
        st.header("High")
        high_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[1]][1], use_container_width=True)

    with col2:
        st.header("Close")
        close_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[1]][2], use_container_width=True)
        st.header("Volume")
        volume_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[1]][3], use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.header("Open")
        open_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[2]][0], use_container_width=True)
        st.header("High")
        high_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[2]][1], use_container_width=True)

    with col2:
        st.header("Close")
        close_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[2]][2], use_container_width=True)
        st.header("Volume")
        volume_chart = st.altair_chart(holding_dict[list(holding_dict.keys())[2]][3], use_container_width=True)

