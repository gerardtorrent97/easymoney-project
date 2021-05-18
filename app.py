import os, sys

import datetime
import streamlit as st
import pandas as pd

import metrics_methods as mm
import products_methods as pm


curr_dir = os.path.dirname(os.path.realpath(__file__))
data_path = curr_dir + "/data/total_df.csv"

@st.cache(persist=True)
def load_data():
    data = pd.read_csv(data_path, sep=";")
    data["pk_partition"] = pd.to_datetime(data["pk_partition"], format="%Y-%m-%d")
    del data["Unnamed: 0"]

    return data

def datetime_to_str(date):
    date = date.replace(day=28)
    date_str = date.strftime("%Y-%m-%d")

    return date_str

def app():
    df = load_data()

    st.image(curr_dir + "/em_logo.png")
    st.title("EasyMoney Interactive Dashboard")
    date = st.sidebar.date_input(
        "Pick a date:",
        value=datetime.date(2018, 1, 28),
        min_value=datetime.date(2018, 1, 28),
        max_value=datetime.date(2019, 5, 28)
    )
    product = st.sidebar.selectbox(
        "Which product would you like to select ?",
        tuple(mm.PRODUCTS)
    )
    date = datetime_to_str(date)

    st.header("Monthly Summary")
    st.write(mm.summary_table(df, date))

    st.header("Products")
    st.subheader("Summary Table:")
    st.write(pm.summary_table(df, product, date))

    st.subheader("Revenue Distribution Charts:")
    st.plotly_chart(pm.piecharts_revenue(df, date))

    st.subheader("Hirings vs Cancellations:")
    st.plotly_chart(pm.piechart_altas(df, product, date))
    

if __name__ == "__main__":
    app()