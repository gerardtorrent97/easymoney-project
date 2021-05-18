"""
This inlcudes the products_methods that will be used to set up the products part in the dashboard autoservice
"""

#Import libraries
import numpy as np
import pandas as pd
import streamlit as st
import datetime
import dateutil.relativedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import metrics_methods as mm

PRODUCTS = ["short_term_deposit",
            "loans",
            "mortgage",
            "funds",
            "securities",
            "long_term_deposit",
            "em_account_pp",
            "credit_card",
            "payroll",
            "pension_plan",
            "payroll_account",
            "emc_account",
            "debit_card",
            "em_account_p",
            "em_acount"
        ]

AHORRO = (mm.PAHORRO, "Ahorro")
FINANCIACION = (mm.PFINANCIACION, "Finaciación")
INVERSION = (mm.PINVERSION, "Inversión")
CUENTAS = (mm.PACCOUNT, "Cuentas")
PRICE = {
    "Finaciación": 60,
    "Ahorro": 40,
    "Inversión": 40,
    "Cuentas": 10
}

def get_month_name(date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d")

    return date.strftime("%b")

def get_product_field(product):
    for field in [AHORRO, FINANCIACION, INVERSION, CUENTAS]:
        if product in field[0]:
            return field[1]
        else:
            pass

def calcular_altas(df, product, date):
    df_altas = df.groupby("pk_partition")[[product]].sum()

    return df_altas.loc[df_altas.index == date, product].values[0]

def calcular_bajas(df, product, date):
    df_altas = df.groupby("pk_partition")[[product]].sum()

    df_bajas = df_altas - df_altas.shift(1)

    return df_bajas.loc[df_bajas.index == date, product].values[0]

def calcular_revenue(df, product, date):
    df_altas = df.groupby("pk_partition")[[product]].sum()

    field = get_product_field(product)

    df_altas[product] = df_altas[product] * PRICE[field]

    return df_altas.loc[df_altas.index == date, product].values[0]

def calcular_churn(df, product, date):
    df_churn = df.groupby("pk_partition")[[product]].sum()

    df_churn["churn"] = (df_churn.sum(axis=1).shift(1) - df_churn.sum(axis=1)).fillna(0)

    return df_churn.loc[df_churn.index == date, "churn"].values[0]

@st.cache(persist=True)
def summary_table_actual(df, product, date):
    field = get_product_field(product)
    altas = calcular_altas(df, product, date)
    bajas = calcular_bajas(df, product, date)
    revenue = calcular_revenue(df, product, date)
    churn = calcular_churn(df, product, date)

    df_update = pd.DataFrame({
        "Campo": [field],
        "Altas": [altas],
        "Bajas": [bajas],
        "Revenue": [revenue],
        "Churn": [churn]
    })
    df_update.index = [get_month_name(date)]

    return df_update.fillna(0)

@st.cache(persist=True)
def summary_table_previous(df, product, date):
    date_prev = datetime.datetime.strptime(date, "%Y-%m-%d") - dateutil.relativedelta.relativedelta(months=1)

    return summary_table_actual(df, product, date_prev.strftime("%Y-%m-%d")).fillna(0)

def summary_table(df, product, date):
    df_act = summary_table_actual(df, product, date)
    if date == "2018-01-28":
        df_updt = df_act.T
    else:
        df_prev = summary_table_previous(df, product, date)
        df_updt = pd.concat([df_act.T, df_prev.T], axis=1)
        df_updt["Diff."] = df_updt.iloc[1:, 0] - df_updt.iloc[1:, 1]

    return df_updt

def revenue(df, date):
    df_ventas = df.loc[df[PRODUCTS].sum(axis=1) >= 1, :].groupby(by="pk_partition")[PRODUCTS].sum()

    for c in df_ventas.columns:
        if c in mm.PAHORRO or c in mm.PINVERSION:
            df_ventas[c]=df_ventas[c]*40
        elif c in mm.PFINANCIACION:
            df_ventas[c]=df_ventas[c]*60
        elif c in mm.PACCOUNT:
            df_ventas[c]=df_ventas[c]*10
        
    
    df_ventas = df_ventas.fillna(0)

    return df_ventas.loc[df_ventas.index == date]

def products(df, date):
    df_revenue = revenue(df, date)

    values = df_revenue.values[0].tolist()
    parents = df_revenue.columns.tolist()
    labels = []
    for col in parents:
        for cat in [AHORRO, INVERSION, FINANCIACION, CUENTAS]:
            if col in cat[0]:
                labels.append(cat[1])
    
    return values, parents, labels
    
def piecharts_revenue(df, date):
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]])

    values, parents, labels = products(df, date)

    fig.add_trace(
        go.Pie(
                labels=labels,
                values=values,
                hole=.3),
        row=1, 
        col=1
    )

    fig.add_trace(
        go.Pie(go.Pie(labels=parents, values=values, hole=.3)),
        row=1,
        col=2
    )

    return fig

def piechart_altas(df, product, date):
    actual = summary_table_actual(df, product, date).T
    actual.drop("Campo", axis=0, inplace=True)
    ab_chart = actual.loc[["Altas", "Bajas"], :]
    fig = go.Figure(go.Pie(values=ab_chart.iloc[:, 0].values.tolist(), labels=ab_chart.index.values, hole=.3))

    return fig
