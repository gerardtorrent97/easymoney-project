import os, sys

import datetime
import streamlit as st
import pandas as pd

import metrics_methods as mm
import products_methods as pm
import segmentation_methods as sm
import trend_methods as tm

from PIL import Image


img=Image.open('em_logo.png')
curr_dir = os.path.dirname(os.path.realpath(__file__))
data_path = curr_dir + "/data/total_df.csv"
data_seg_path=curr_dir+"/data/Segmentacion.pkl"
data_post_seg_path=curr_dir+"/data/df_post_segmentacion_2.pkl"

@st.cache(persist=True)

def load_data():
    data = pd.read_csv(data_path, sep=";")
    data["pk_partition"] = pd.to_datetime(data["pk_partition"], format="%Y-%m-%d")
    del data["Unnamed: 0"]
    return data
def load_data_cluster():
    data=pd.read_pickle(data_seg_path) 
    return data
def load_data_post_cluster():
    data=pd.read_pickle(data_post_seg_path)
    return data

def datetime_to_str(date):
    date = date.replace(day=28)
    date_str = date.strftime("%Y-%m-%d")

    return date_str

def app():
    df = load_data()
    df_seg=load_data_cluster()
    df_post_seg=load_data_post_cluster()

   
    
    
    rad = st.sidebar.radio("Navigation",['Home','Monthly Summary','Products','Trend analysis','Customer segmentation'])
    if rad=='Home':
        st.title("EasyMoney Interactive Dashboard")
        st.image(img)
    if rad=='Monthly Summary':
        st.header('Monthly summary')
        date = st.sidebar.date_input(
            "Pick a date:",
            value=datetime.date(2018, 4, 28),
            min_value=datetime.date(2018, 4, 28),
            max_value=datetime.date(2019, 5, 28)
        )
    
        date = datetime_to_str(date) 
        st.write(mm.summary_table(df, date)) 
        
        col1,col2=st.beta_columns(2)
        with col1:
            st.subheader('Tabla resumen del mes')
            st.plotly_chart(pm.tabla_resumen_mes(df,date))
            st.subheader('Distribución del revenue por producto')
            st.plotly_chart(pm.pie_charts_revenue(df,date)[0])
        with col2:
            st.subheader('Distribución del revenue por tipologia de producto')
            st.plotly_chart(pm.pie_charts_revenue(df,date)[1])

    elif rad=='Products':
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
        st.header("Products")
        col3,col4=st.beta_columns((4,1))
        with col3:
            st.subheader("Como se distribuyen nuestras ventas de forma global?")
            st.plotly_chart(tm.ventas_totales_por_producto(df))
        with col4:
            st.subheader("Tabla resumen para {}".format(product))
            st.write('\n')
            st.write('\n')
            st.write('\n')
            st.write(pm.summary_table(df, product, date))
        col1, col2 = st.beta_columns(2)
        
        with col1:
            st.plotly_chart(pm.edad_genero_por_producto(df,product,date)[0])
            st.plotly_chart(pm.edad_genero_por_producto(df,product,date)[1])
            st.plotly_chart(pm.numero_de_productos(df))

        with col2:
            st.plotly_chart(pm.compara_tipos_productos(df,date))
            st.plotly_chart(pm.piechart_altas(df, product, date))
            #st.plotly_chart(pm.nuevos_vs_existentes_chart(df))

    elif rad=="Trend analysis" :
        st.header('Trend analysis')
        col1, col2 = st.beta_columns(2)
        with col1:
            st.plotly_chart(tm.comisiones_por_mes(df)[0])
            st.plotly_chart(tm.calcula_revenue_total(df)[0])
            st.plotly_chart(tm.evolucion_clientes(df)[0])
            st.plotly_chart(tm.clientestotales_vs_clientesproducto())
        with col2:
            st.plotly_chart(tm.calcula_ingresos_por_mes(df)[0])
            st.plotly_chart(tm.activos_web(df)[0])
            st.plotly_chart(tm.fugas_ingresos_por_mes(df))
            st.plotly_chart(tm.clientestotales_vs_clientesactivosweb())

        
        #with col2:
        
    elif rad=="Customer segmentation":
        st.header('Customer segmentation')
        col1, col2 = st.beta_columns(2)
        with col1: 
            st.plotly_chart(sm.fig_tipo_productos_por_segmento(df_seg))
            st.plotly_chart(sm.fig_clientes_por_cluster(df_seg))
            st.plotly_chart(sm.fig_activos_web(df_seg))
            st.plotly_chart(sm.genero_por_segmento(df_post_seg))
        with col2:
            st.plotly_chart(sm.fig_producto_por_segmento(df_post_seg))
            st.plotly_chart(sm.fig_altas_bajas(df_seg))
            st.plotly_chart(sm.edad_por_segmento(df_post_seg))
        

if __name__ == "__main__":
    app()