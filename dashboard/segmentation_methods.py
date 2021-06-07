#Import libraries
import numpy as np
import pandas as pd
import streamlit as st
import datetime
import dateutil.relativedelta
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns  
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


@st.cache(persist=True)
def ficha_cliente (X_processed):
    metricas_a_analizar=['total_ahorro','total_inversion','total_financiacion','total_cuentas']
    ficha_df = pd.DataFrame()
    for i, col in enumerate(metricas_a_analizar):
        resumen_data = X_processed[["cluster", col]].groupby("cluster").describe().T[1:]
        ficha_df = ficha_df.append(resumen_data)
    return ficha_df 

def crea_df_resumen(X_processed):
    df_resumen=X_processed.groupby('cluster').agg({     
                                         'total_ahorro':np.mean,
                                         'total_inversion':np.mean,
                                         'total_financiacion':np.mean,
                                         'total_cuentas':np.mean,
                                         'num_bajas':np.mean,
                                         'num_altas':np.mean,
                                         'numero_de_cobros':np.mean,
                                        #'edad':np.mean,
                                        'activo_web':np.mean,
                                        'cluster':len 
})

    df_resumen.rename(columns={"cluster":'Numero de clientes por cluster'},inplace=True)
    return df_resumen 
def fig_tipo_productos_por_segmento(X_processed):
    df_res=crea_df_resumen(X_processed)
    df_res.reset_index(drop=False,inplace=True)
    df_resumen_m=df_res.melt(id_vars=['cluster'],
              value_vars=['total_ahorro','total_inversion','total_financiacion','total_cuentas'],
              var_name='Tipo de Producto',
              value_name='Total')
    fig=px.bar(df_resumen_m, x="cluster", y="Total", color='Tipo de Producto', orientation='v', 
                              height=600,title='Relación de tipos de productos por segmento')
    return fig

def fig_clientes_por_cluster(X_processed):
    df_res=crea_df_resumen(X_processed)
    df_res.reset_index(drop=False,inplace=True)
    fig=px.pie(df_res,names='cluster',values='Numero de clientes por cluster',
        title='Clientes por segmento')
    return fig
def fig_activos_web(X_processed):
    df_res=crea_df_resumen(X_processed)
    df_res.reset_index(drop=False,inplace=True)
    fig_web=px.bar(df_res,x=df_res.index,y='activo_web',title='Actividad en la web por segmento')

    return fig_web
def  fig_altas_bajas(X_processed):
    df_res=crea_df_resumen(X_processed)
    df_res.reset_index(drop=False,inplace=True)
    df_altas_bajas=df_res.melt(id_vars=['cluster'],
              value_vars=['num_bajas','num_altas'],
              var_name='Altas y bajas',
              value_name='Altas y bajas medias')
    fig=px.bar(df_altas_bajas,x='cluster',y='Altas y bajas medias',
                        color='Altas y bajas',barmode='group',title='Altas y bajas por segmento')
    return fig
def fig_producto_por_segmento(df_tot):
    prod_por_clus=df_tot.pivot_table(index=['cluster'],values=PRODUCTS,aggfunc=[np.mean])
    prod_por_clus.columns=['credit_card','debit_card','em_account_p',	'em_account_pp',	'em_acount',	'emc_account',	'funds','loans','long_term_deposit','mortgage','payroll','payroll_account','pension_plan','securities',
                       'short_term_deposit']
    prod_por_clus.reset_index(drop=False,inplace=True)
    prod_por_clus=prod_por_clus.melt(id_vars=['cluster'],
                value_vars=PRODUCTS,
                var_name='Producto',
                value_name='Total')
    fig=px.bar(prod_por_clus, x="cluster", y="Total", color='Producto', orientation='v', 
                                height=600,title='Relación de productos por grupos de clientes')
    return fig 

def edad_por_segmento(df_tot):
    df_explora=df_tot.sort_values(by=['pk_partition','pk_cid']).groupby('pk_cid').agg({'age':'first','salary':np.mean,'cluster':'first'})
    fig_edad = px.box(df_explora, x="cluster", y="age",title='Edad por segmento')

    return fig_edad
def genero_por_segmento(df_tot):
    df_explora=df_tot.sort_values(by=['pk_partition','pk_cid']).groupby('pk_cid').agg({'age':'first','salary':np.mean,'cluster':'first','gender':'first'})
    df_explora['gender']=df_explora['gender'].replace({0:'Mujer',1:'Hombre'})
    fig=px.histogram(df_explora.dropna(), x='cluster', color="gender", barmode='group',title='Genero por segmento')
    return fig



