"""
This inlcudes the metrics_methods that will be used to set up the metrics part in the dashboard autoservice
"""

#Import libraries
import numpy as np
import pandas as pd
import datetime
import dateutil.relativedelta
import plotly_express as px

import streamlit as st


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

PAHORRO = ['long_term_deposit','pension_plan','short_term_deposit']
PINVERSION = ['funds','securities']
PFINANCIACION = ['credit_card','loans','mortgage']
PACCOUNT = ['debit_card','em_account_p','em_account_pp','em_acount','emc_account','payroll',
          'payroll_account']

def fill_nans(df):
    return df.fillna(0)

def calcula_tasa_fidelizacion(df, date):
    df_clients_with_product = df.loc[df[PRODUCTS].sum(axis=1) >= 1, :].groupby(by="pk_partition")["pk_cid"].count()
    df_clients_total = df.groupby(by="pk_partition")["pk_cid"].count()
    df_evo_clients = pd.concat([df_clients_total, df_clients_with_product], axis=1)
    df_evo_clients.columns = ["total", "con_producto"]

    df_evo_clients["porcentaje"] = round(df_evo_clients["con_producto"] / df_evo_clients["total"] * 100, 2)

    df_evo_clients = fill_nans(df_evo_clients)

    tasa = df_evo_clients.loc[df_evo_clients.index == date, "porcentaje"].values[0]
    tasa_str = f"{tasa}%"

    return tasa_str

def calcular_captacion(df, date):
    df_clients_with_product = df.loc[df[PRODUCTS].sum(axis=1) >= 1, :].groupby(by="pk_partition")[["pk_cid"]].count().sort_values(by="pk_partition", ascending=False)

    df_clients_with_product["mes_anterior"] = df_clients_with_product["pk_cid"].shift(-1)
    df_clients_with_product["nuevos"] = df_clients_with_product["pk_cid"] - df_clients_with_product["mes_anterior"]

    df_clients_with_product = fill_nans(df_clients_with_product)

    return df_clients_with_product.loc[df_clients_with_product.index == date, "nuevos"].values[0]

def calcular_churn(df, date):
    """Clientes que han dado de baja sus productos en el último mes."""
    # tenemos la suma de todos los 1 por productos
    df_churn = df.loc[df[PRODUCTS].sum(axis=1) >= 1, :].groupby(by="pk_partition")[PRODUCTS].sum()
    # la suma de todos los 1 del mes anterior
    # la diferencia entre los productos del mes anterior
    df_churn["churn"] = df_churn.sum(axis=1).shift(1) - df_churn.sum(axis=1)

    df_churn = fill_nans(df_churn)
    df_churn["churn"] = df_churn["churn"].astype(int)
    df_churn['churn']=np.where(df_churn['churn']<0,0,df_churn['churn'])

    return df_churn.loc[df_churn.index == date, "churn"].values[0]

def calcular_fuga_db(df, date):
    """Clientes que han tenido algun producto contratado se han fugado de la Base de Datos"""
    df_fugas = df.loc[df[PRODUCTS].sum(axis=1) >= 1].groupby(by="pk_cid")["pk_partition"].agg(["min", "max"])
    df_fugas.columns = ["min", "max"]
    previous_date = datetime.datetime.strptime(date, "%Y-%m-%d") - dateutil.relativedelta.relativedelta(months=1)

    df_fugas = fill_nans(df_fugas)

    return df_fugas[(df_fugas["min"] == previous_date.strftime("%Y-%m-%d")) & (df_fugas["max"] == date)].index.nunique()

def calcular_ventas_brutas(df, date):
    """Calcula las ventas brutas de ese mes (sin tener en cuenta 3 meses previos de permanencia) """
    df_ventas = df.loc[df[PRODUCTS].sum(axis=1) >= 1, :].groupby(by="pk_partition")[PRODUCTS].sum()

    for c in df_ventas.columns:
        if c in PAHORRO or c in PINVERSION:
            df_ventas[c]=df_ventas[c]*40
        elif c in PFINANCIACION:
            df_ventas[c]=df_ventas[c]*60
        elif c in PACCOUNT:
            df_ventas[c]=df_ventas[c]*10
        
    ventas = (df_ventas.sum(axis=1) * 100) / df_ventas.sum(axis=1).shift(1) - 100
    ventas = fill_nans(ventas)
    
    ventas_brutas_mes = round(ventas[ventas.index == date].values[0], 3)
    vb_mes_str = f"{ventas_brutas_mes}%"
    
    return vb_mes_str

# TODO no tener en cuenta los clientes de la primera partición (son clientes de los que ya podemos haber cobrado su alta)
def calcular_comisiones(df, date):
    """Calculamos las comisiones del mes actual teniendo en cuenta permanencia de 3 meses (el actual + los dos anteriores)"""
    # solo podemos calcularlas los meses poseriores a 2018-03-28 (podemos ya haber cobrado esas altas de la primera particion)
    if date == "2018-03-28":
        return 0
    
    df_comi = preparar_df_comi(df, date)
    # agrupamos por cliente y calculamos la suma de sus distintos productos
    df_comi = df_comi.groupby("pk_cid")[PRODUCTS].sum()
    # miramos que la suma de la row por cliente de sus productos sea mayor o igual a 3
    # (uno o más productos con 3 meses de permanencia)
    df_comi = df_comi.loc[df_comi[PRODUCTS].sum(axis=1) >= 3, :]
    # ponemos todo numero igual a 3 a 0 (asi solo tenemos múltiplos de 3)
    df_comi = df_comi.where(df_comi[PRODUCTS] == 3, other=0)

    for c in df_comi.columns:
        if c in PAHORRO or c in PINVERSION:
            df_comi[c] = df_comi[c] * 40/3
        elif c in PFINANCIACION:
            df_comi[c] = df_comi[c] * 60/3
        elif c in PACCOUNT:
            df_comi[c] = df_comi[c] * 10/3
    
    # sumamos todas las comisiones de cada cliente (row) y luego sacamos el total
    return df_comi[PRODUCTS].sum(axis=1).sum()

def filtrar_clientes_tres_particiones(df):
    """Filtra aquellos clientes que aparecen en las tres particiones del df ya filtrado"""
    df = df[df["pk_cid"].map(df["pk_cid"].value_counts() == 3)]

    return df

def preparar_df_comi(df, date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    date_1_month = date - dateutil.relativedelta.relativedelta(months=1)
    date_2_month = date_1_month - dateutil.relativedelta.relativedelta(months=1)

    df = df[df["pk_partition"].isin([date, date_1_month, date_2_month])]

    df = filtrar_clientes_tres_particiones(df)

    del df["pk_partition"]      

    return df
def comisiones_por_mes (df):
    df_productos= df.loc[:, ["pk_cid","pk_partition",] + PRODUCTS]
    df_ventas_mes=df_productos[df_productos[PRODUCTS].sum(axis=1) >= 1].pivot_table(values=PRODUCTS, index=['pk_cid','pk_partition'])
    df_ventas_mes.reset_index(inplace=True)
    df_ventas_mes.set_index('pk_partition',inplace=True)
    df_ventas_mes.drop_duplicates(keep='first',inplace=True)
    df_ventas_producto_mes=df_ventas_mes.groupby(by=df_ventas_mes.index).sum()
    del(df_ventas_producto_mes['pk_cid'])
    return df_ventas_producto_mes[3:]

def calcula_ingresos_por_mes(df):
    df_ventas_producto_mes=comisiones_por_mes(df)
    df_ingresos=pd.DataFrame()
    l_ahorro=['long_term_deposit','pension_plan','short_term_deposit']
    l_inversion=['funds','securities']
    l_financiacion=['credit_card','loans','mortgage']
    l_cuenta=['debit_card','em_account_p','em_account_pp','em_acount','emc_account','payroll',
          'payroll_account']
    for c in df_ventas_producto_mes.columns:
        if c in l_ahorro or c in l_inversion:
            df_ingresos[c]=df_ventas_producto_mes[c]*40
        elif c in l_financiacion:
            df_ingresos[c]=df_ventas_producto_mes[c]*60
        else:
            df_ingresos[c]=df_ventas_producto_mes[c]*10
    return df_ingresos
    

def calcula_revenue_total(df):
    df_ingresos=calcula_ingresos_por_mes(df)
    df_ingresos['total_revenue']=df_ingresos.sum(axis=1)
    return df_ingresos
    
@st.cache(persist=True)
def summary_table(df, date):
    tasa = calcula_tasa_fidelizacion(df, date)
    captacion = calcular_captacion(df, date)
    churn = calcular_churn(df, date)
    fuga = calcular_fuga_db(df, date)
    vb = comisiones_por_mes(df).sum(axis=1)[date]
    incremento_porcentual=calcular_ventas_brutas(df,date)
    comisiones = calcula_revenue_total(df)['total_revenue'][date]
    df_update = pd.DataFrame({
        "Fidelización": [tasa],
        "Captación": [captacion],
        "Abandono": [churn],
        "Fuga Clientes": [fuga],
        "Ventas Brutas": [vb],
        "Aumento porcentual ventas":[incremento_porcentual],
        "Comisiones facturadas": [comisiones]
    })
    df_update.index = [""]

    return df_update

