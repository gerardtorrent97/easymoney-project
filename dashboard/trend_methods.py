import numpy as np
import pandas as pd
import datetime
import dateutil.relativedelta
import plotly_express as px
import streamlit as st
import os


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
curr_dir = os.path.dirname(os.path.realpath(__file__))
data_path_1 = curr_dir + "/data/evolucion_clientes.pkl"
data_path_2 = curr_dir + "/data/evolucion_clientes_activos_web.pkl"

@st.cache(persist=True)
def evolucion_clientes(df_clientes):
    _df = df_clientes[df_clientes[PRODUCTS].sum(axis=1) >= 1].groupby(
        by=["pk_partition"])[["pk_cid"]].count().sort_values(by="pk_partition", ascending=False)
    _df["ant"] = _df["pk_cid"].shift(-1)
    _df["dif"] =_df["pk_cid"] -_df["ant"]
    df_n_cli = df_clientes.groupby(by=["pk_partition"])[["pk_cid"]].count().sort_values(by="pk_partition", ascending=False)
    df_evolucion_clientes=pd.concat([df_n_cli, _df], axis=1)
    df_evolucion_clientes.columns = ["total", "con_producto", "siguiente", "dif"]
    df_evolucion_clientes["porcentaje"] = round(df_evolucion_clientes["con_producto"] / 
    df_evolucion_clientes["total"] * 100, 2)
    df_evolucion_clientes.reset_index(inplace=True)
    fig = px.line(df_evolucion_clientes, x="pk_partition", y="porcentaje", range_y=[50,100],
    title='Evolución de la tasa de conversión')
    return fig , df_evolucion_clientes

def activos_web(df_clientes):
    df_numero_clientes_activos = df_clientes[df_clientes["active_customer"] == 1].groupby(by=["pk_partition"])[["pk_cid"]].count().sort_values(by="pk_partition", ascending=False)
    df_numero_clientes = df_clientes.groupby(by=["pk_partition"])[["pk_cid"]].count().sort_values(by="pk_partition", ascending=False)
    df_evolucion_clientes_activos_web = pd.concat([df_numero_clientes, df_numero_clientes_activos], axis=1)
    df_evolucion_clientes_activos_web.columns = ["total", "activos_web"]  
    df_evolucion_clientes_activos_web["porcentaje"] = round(df_evolucion_clientes_activos_web["activos_web"] / df_evolucion_clientes_activos_web["total"] * 100, 2)
    df_evolucion_clientes_activos_web.reset_index(inplace=True)
    fig = px.line(df_evolucion_clientes_activos_web, x="pk_partition", y="porcentaje", range_y=[0,50],title='Evolución tasa de navegación en la web')
    return fig,df_evolucion_clientes_activos_web

def clientestotales_vs_clientesproducto():
    df_evolucion_cientes_T=pd.read_pickle(data_path_1)
    fig = px.line(df_evolucion_cientes_T, x="pk_partition", y="value", color="variable",
                title='Evolución de clientes totales vs clientes con uno o más productos activos')
    return fig

def clientestotales_vs_clientesactivosweb():
    df_evolucion_clientes_activos_web_T=pd.read_pickle(data_path_2)
    fig = px.line(df_evolucion_clientes_activos_web_T, x="pk_partition", y="value", color="variable",
    title='Evolución de clientes activos en web vs total de clientes')
    
    return fig

def ventas_totales_por_producto(df):
    df_productos= df.loc[:, ["pk_cid","pk_partition",] + PRODUCTS]
    df_permanencia=df_productos[df_productos[PRODUCTS].sum(axis=1) >= 1].pivot_table(values=PRODUCTS, index='pk_cid', aggfunc='sum')
    for c in df_permanencia.columns:
        df_permanencia[c]=np.where(df_permanencia[c]>3,1,df_permanencia[c])
        
    df_ventas_totales=pd.DataFrame(df_permanencia.apply(sum).sort_values(ascending=False),columns=['Ventas_totales'])
    df_ventas_totales.reset_index(drop=False,inplace=True)
    df_ventas_totales.columns=['Producto','Ventas_totales']
    d_equiv={'long_term_deposit':'ahorro','pension_plan':'ahorro','short_term_deposit':'ahorro','funds':'inversion',
         'securities':'inversion','credit_card':'financiacion','loans':'financiacion','mortgage':'financiacion',
         'debit_card':'cuentas','em_account_p':'cuentas','em_account_pp':'cuentas','em_acount products':'cuentas',
         'emc_account products':'cuentas','payroll':'cuentas','payroll_account':'cuentas','emc_account':'cuentas',
        'em_acount':'cuentas'}
    df_ventas_totales['categoria']=df_ventas_totales['Producto'].map(d_equiv)

    fig = px.treemap(df_ventas_totales, path=['categoria', 'Producto'], values='Ventas_totales',width=1000, height=500)   
    
    return fig

def comisiones_por_mes (df):
        df_productos= df.loc[:, ["pk_cid","pk_partition",] + PRODUCTS]
        df_ventas_mes=df_productos[df_productos[PRODUCTS].sum(axis=1) >= 1].pivot_table(values=PRODUCTS, index=['pk_cid','pk_partition'])
        df_ventas_mes.reset_index(inplace=True)
        df_ventas_mes.set_index('pk_partition',inplace=True)
        df_ventas_mes.drop_duplicates(keep='first',inplace=True)
        df_ventas_producto_mes=df_ventas_mes.groupby(by=df_ventas_mes.index).sum()
        del(df_ventas_producto_mes['pk_cid'])
        df_ventas_producto_mes=df_ventas_producto_mes[3:]
        fig=px.line(df_ventas_producto_mes,x=df_ventas_producto_mes.index,y=PRODUCTS,title='Evolución de ventas por producto')
        return fig,df_ventas_producto_mes

def calcula_ingresos_por_mes(df):
    df_ventas_producto_mes=comisiones_por_mes(df)[1]
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
    
    fig=px.line(df_ingresos,x=df_ingresos.index,y=PRODUCTS,title='Evolución de ingresos por producto')
    return fig, df_ingresos

def calcula_revenue_total(df):
    df_ingresos=calcula_ingresos_por_mes(df)[1]
    df_ingresos['total_revenue']=df_ingresos.sum(axis=1)
    fig=px.bar(df_ingresos,x=df_ingresos.index,y='total_revenue')
    return fig,df_ingresos

def fugas_ingresos_por_mes(df):
    df_productos= df.loc[:, ["pk_cid","pk_partition",] + PRODUCTS]
    df_productos.drop('pk_cid',axis=1,inplace=True)
    clientes_producto=df_productos.groupby('pk_partition').sum()
    clientes_mes=pd.DataFrame(clientes_producto.sum(axis=1))
    clientes_mes.columns=['Clientes']
    clientes_producto=df_productos.groupby('pk_partition').sum()
    clientes_mes['Clientes_Mes_Anterior']=clientes_mes['Clientes'].shift(1)
    clientes_mes['Fugas_Ingresos']=clientes_mes['Clientes']-clientes_mes['Clientes_Mes_Anterior']
    clientes_mes['Fugas_vs_ingresos']=np.where(clientes_mes['Fugas_Ingresos']>0,'Ingresos','Fugas')
    df_fugas_ingresos=clientes_mes[1:]
    fig=px.bar(df_fugas_ingresos,x=df_fugas_ingresos.index,y='Fugas_Ingresos',color='Fugas_vs_ingresos',barmode='group')
    return fig
