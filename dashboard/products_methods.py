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
@st.cache(persist=True)
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
def evolución_productos_por_mes(df):
    df_ventas_month = df.loc[:, ["pk_partition"] + PRODUCTS]
    df_ventas_month = df_ventas_month.groupby(by="pk_partition").sum()

    return df_ventas_month

def calcular_churn(df, product, date):
    mes_actual=evolución_productos_por_mes(df)
    mes_anterior=evolución_productos_por_mes(df).shift(1)
    df_churn=mes_anterior-mes_actual
    df_churn.fillna(0,inplace=True)
    for c in df_churn.columns:
        df_churn[c]=df_churn[c].apply(lambda x:0 if x<0 else x)
    df_churn=(df_churn/mes_anterior)*100
    
    return round(df_churn.loc[date,product],2)

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

    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"},{"type": "domain"}]])

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
    fig = go.Figure(go.Pie(values=ab_chart.iloc[:, 0].values.tolist(), labels=ab_chart.index.values,
     hole=.3))
    fig.update_layout(title='Nuevas contrataciones vs Cancelaciones')

    return fig

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
        if c not in ['payroll','payroll_account']:
            if c in l_ahorro or c in l_inversion:
                df_ingresos[c]=df_ventas_producto_mes[c]*40
            elif c in l_financiacion:
                df_ingresos[c]=df_ventas_producto_mes[c]*60
            else:
                df_ingresos[c]=df_ventas_producto_mes[c]*10
        else:
            df_ingresos[c]=df_ventas_producto_mes[c]*0
    return df_ingresos
    

def calcula_revenue_total(df):
    df_ingresos=calcula_ingresos_por_mes(df)
    df_ingresos['total_revenue']=df_ingresos.sum(axis=1)
    return df_ingresos

def tabla_resumen_mes(df,mes):
    df_ingresos=calcula_revenue_total(df)
    tabla_resumen=pd.DataFrame(columns=['altas','bajas','revenue','churn'],index=df_ingresos.T.index)
    tabla_resumen['revenue']=df_ingresos.loc[mes]
    tabla_resumen=tabla_resumen[0:-1]
    for product in tabla_resumen.index:
        tabla_resumen.at[product,'bajas']=calcular_bajas(df,product,mes)
        tabla_resumen.at[product,'altas']=calcular_altas(df,product,mes)
        tabla_resumen.at[product,'churn']=calcular_churn(df,product,mes) 
    d_equiv={'long_term_deposit':'ahorro','pension_plan':'ahorro','short_term_deposit':'ahorro','funds':'inversion',
         'securities':'inversion','credit_card':'financiacion','loans':'financiacion','mortgage':'financiacion',
         'debit_card':'cuentas','em_account_p':'cuentas','em_account_pp':'cuentas','em_acount products':'cuentas',
         'emc_account products':'cuentas','payroll':'cuentas','payroll_account':'cuentas','emc_account':'cuentas',
        'em_acount':'cuentas'}
    tabla_resumen['categoria']=tabla_resumen.index.map(d_equiv)
    tabla_resumen.reset_index(drop=False,inplace=True)
    tabla_resumen.columns=['Producto','altas','bajas','revenue','churn','categoria']
    tabla_resumen.sort_values(by='categoria',inplace=True)
    index = pd.MultiIndex.from_frame(tabla_resumen[['categoria','Producto']])
    tabla_resumen = pd.DataFrame(data = tabla_resumen[['altas','bajas','revenue','churn']].values, index = index, columns =['altas','bajas','revenue','churn'])
    df_table = tabla_resumen.reset_index()
    df_table.loc[df_table['categoria'].duplicated(), 'categoria'] = ''
    table = go.Table(columnwidth = [4,6,3,3,3,3,3],
    header=dict(values=df_table.columns.tolist(),fill_color='#17202A'),
    cells=dict(values=df_table.T.values,fill_color='#212F3C'))

    fig = go.Figure(data=table).update_layout(height=550)

    return fig

def edad_genero_por_producto(df,product,date):
    df_product=df[df['pk_partition']==date][[product,'age','salary','gender','entry_channel','active_customer','region_code']]
    df_product=df_product[df_product[product]==1]
    fig1=px.pie(df_product.dropna(),values=product,names='gender',title='Genero de los clientes con producto: {}'.format(product))
    fig2=px.histogram(df_product, x="age", y=product,title='Distribucón de la edad de los clientes con producto: {}'.format(product))
    return fig1,fig2
def compara_tipos_productos(df,date):
    df_product=df[df['pk_partition']==date][PRODUCTS+['age','salary','gender','entry_channel','active_customer','region_code']]
    d_equiv={'AHORRO':['long_term_deposit','pension_plan','short_term_deposit'],'INVERSION':['funds',
         'securities','credit_card'],'FINANCIACIÓN':['loans','mortgage','debit_card'],'CUENTAS':['em_account_p','em_account_pp',
         'em_acount','emc_account','payroll','payroll_account','emc_account',
        'em_acount']} 
    fig1 = go.Figure()
    for key,value in d_equiv.items():
        cond=df_product[value].sum(axis=1)>1
        df_product[key]=np.where(cond,1,0)
        fig1.add_trace(go.Box(x=df_product[df_product[key]==1]['age'],name=key))
    fig1.update_traces()
    fig1.update_layout(title="Edad por tipo de producto")
    return fig1

def pie_charts_revenue(df,fecha):
    df_ventas_producto_mes=comisiones_por_mes(df)
    df_ingresos=pd.DataFrame()
    l_ahorro=['long_term_deposit','pension_plan','short_term_deposit']
    l_inversion=['funds','securities']
    l_financiacion=['credit_card','loans','mortgage']
    l_cuenta=['debit_card','em_account_p','em_account_pp','em_acount','emc_account']
    
    for c in df_ventas_producto_mes.columns:
        if c not in ['payroll','payroll_account']:
            if c in l_ahorro:
                df_ingresos[c]=df_ventas_producto_mes[c]*40
            elif c in l_inversion:
                df_ingresos[c]=df_ventas_producto_mes[c]*40 
            elif c in l_financiacion:
                df_ingresos[c]=df_ventas_producto_mes[c]*60
            else:
                df_ingresos[c]=df_ventas_producto_mes[c]*10
                
    df_ingresos=df_ingresos.T
    df_ingresos.columns=['2018-04-28',
       '2018-05-28', '2018-06-28', '2018-07-28', '2018-08-28',
       '2018-09-28', '2018-10-28', '2018-11-28', '2018-12-28',
       '2019-01-28', '2019-02-28', '2019-03-28', '2019-04-28',
       '2019-05-28']
    d_equiv={'long_term_deposit':'ahorro','pension_plan':'ahorro','short_term_deposit':'ahorro','funds':'inversion',
            'securities':'inversion','credit_card':'financiacion','loans':'financiacion','mortgage':'financiacion',
            'debit_card':'cuentas','em_account_p':'cuentas','em_account_pp':'cuentas','em_acount products':'cuentas',
            'emc_account products':'cuentas','emc_account':'cuentas',
            'em_acount':'cuentas'}
    df_ingresos['categoria']=df_ingresos.index.map(d_equiv)
    fig1=px.pie(df_ingresos,values=df_ingresos[fecha].values,names=df_ingresos.index)
    df_cat=df_ingresos.groupby(by='categoria').sum()
    fig2=px.pie(df_cat,values=df_cat[fecha].values,names=df_cat.index)
        
    return fig1,fig2

def numero_de_productos(df):
    df['num_productos']=df[PRODUCTS].sum(axis=1)
    data_num_prods=df['num_productos'].value_counts().to_frame()
    data_num_prods.reset_index(drop=False,inplace=True)
    data_num_prods.columns=['numero_de_productos','frequencia']
    data_num_prods.sort_values(by='numero_de_productos',inplace=True)
    fig=px.bar(data_num_prods,x='numero_de_productos',y='frequencia',title='Cuantos productos contratan nuestros clientes?')
    return fig
def nuevo_vs_existente(df,fecha_actual,fecha_anterior):
    df['num_productos']=df[PRODUCTS].sum(axis=1)
    mes_actual=df[df['pk_partition']==fecha_actual]
    mes_anterior=df[df['pk_partition']==fecha_anterior]
    clientes_actuales=set(mes_actual['pk_cid'].values)
    clientes_mes_anterior=set(mes_anterior['pk_cid'].values)
    df_clientes_mes_anterior=mes_anterior[mes_anterior['pk_cid'].isin(clientes_mes_anterior) & mes_anterior['num_productos']==0]
    clientes_mes_anterior_sin_producto=set(df_clientes_mes_anterior['pk_cid'].values)
    cliente_existente=clientes_actuales.intersection(clientes_mes_anterior)
    cliente_nuevo=clientes_actuales-clientes_mes_anterior
    ventas_clientes_viejos=mes_actual[(mes_actual['pk_cid'].isin(clientes_mes_anterior_sin_producto))]['num_productos'].sum()
    ventas_clientes_nuevos=mes_actual[mes_actual['pk_cid'].isin(cliente_nuevo)]['num_productos'].sum()
    porcentaje_compra_nuevos=(ventas_clientes_nuevos/len(cliente_nuevo))*100
    porcentaje_compra_existente=(ventas_clientes_viejos/len(clientes_mes_anterior_sin_producto))*100
    
    return porcentaje_compra_nuevos, porcentaje_compra_existente 

def nuevos_vs_existentes_chart(df):
    l_date=df['pk_partition'].unique()
    pct_nuevos=[]
    pct_existentes=[]
    for i in range( len(l_date)-1):
        pct_nuevos.append(nuevo_vs_existente(df,l_date[i+1],l_date[i])[0])
        pct_existentes.append(nuevo_vs_existente(df,l_date[i+1],l_date[i])[1])
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=l_date,
        y=pct_nuevos[5:],
        name='Clientes Nuevos',
        marker_color='indianred'
    ))
    fig.add_trace(go.Bar(
        x=l_date,
        y=pct_existentes,
        name='Clientes_existentes',
        marker_color='lightsalmon'
    ))
    fig.update_layout(barmode='group', xaxis_tickangle=-45,title='Porcentaje de compra en clientes nuevos vs existentes')
    fig.update_xaxes()
    return fig
       