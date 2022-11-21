# Carregando bibliotecas
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib as mpl
import streamlit as st
import plotly.express as px
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb


# Criação da função
def aumento_cumulativo(lista, porc_aumento):
    for i, valor in enumerate(lista):
        lista[i] = lista[i-1] * (1 + porc_aumento) if i > 0 else valor
    return lista

def simulador(data_inicio = '2021-09-01',
              data_fim = '2024-12-01',
              aporte_mensal = 0,
              aumento_aporte = 0,

              meses_bonus = [],
              valor_bonus = 0,
              crescimento_bonus = 0,

              rendimento_anual = 0,
              dados_reais = []):
  
    # Rendimento mensal
    rendimento_mensal = ((1 + rendimento_anual) ** (1/12)) - 1

    # Corrigindo tamanho dos dados reais
    if len(dados_reais) > 0:
        dados_reais = dados_reais.loc[dados_reais['data'] <= data_fim]

    # Data máxima disponibilizada
    try:
        data_real_max = dados_reais['data'].max()
    except:
        pass

    # Criando dataframe em branco
    df = pd.DataFrame(columns = ['data','aporte','custodia'])

    df['data'] = pd.to_datetime(pd.date_range(data_inicio,
                                            data_fim,
                                            freq='MS').strftime("%Y-%m"), 
                              format="%Y-%m")

    #Preenchendo coluna de aportes
    if len(dados_reais) == 0:
        df['aporte'] = aumento_cumulativo([aporte_mensal] * len(df['data']),
                                          aumento_aporte)
    else:
        aporte_artificial = ([aporte_mensal] * (len(df['data']) -
                                                len(dados_reais['aporte'])))

        df['aporte'] = (dados_reais['aporte'].tolist() + 
                        aumento_cumulativo(aporte_artificial, aumento_aporte))

    # Adicionando o bônus à lista de aportes
    if len(dados_reais) == 0:
        cond = df['data'].dt.month.isin(meses_bonus)
    else:
        cond = ((df['data'].dt.month.isin(meses_bonus)) &
                (df['data'] > data_real_max))

    lista_aportes = df.loc[cond,'aporte'].tolist()

    if len(lista_aportes) > 0:
        lista_aportes[0] = lista_aportes[0] + valor_bonus

    lista_aportes = aumento_cumulativo(lista_aportes, crescimento_bonus)

    df.loc[cond,'aporte'] = lista_aportes

    # Preenchendo coluna de custódia
    def func_addcustodia(df, na = False):
        df_iter = df if na == False else df.loc[df['custodia'].isna()]
        for i, row in df_iter.iterrows():
            df.loc[i,'custodia'] = (df.loc[i,'aporte'] if i == 0 
                                  else df.loc[i-1,'custodia'] * (1 + rendimento_mensal) + df.loc[i,'aporte'])
        return df['custodia']

    if len(dados_reais) == 0:
        df['custodia'] = func_addcustodia(df)
    else:
        df = df[['data','aporte']].merge(dados_reais[['data','custodia']],
                                         on = 'data',
                                         how='left')

        df.loc[:,'custodia'] = func_addcustodia(df, na = True)

    num_to_str = lambda valor: (str("R$ {:,.2f}"
                              .format(round(valor,2)))
                              .replace('.','#')
                              .replace(',','%')
                              .replace('#',',')
                              .replace('%','.'))

    data_max = df['data'].max()

    total_aportado = df['aporte'].sum()

    rendimento = df.loc[df['data'] == data_max,'custodia'].iloc[0] - total_aportado
    rendimento_porc = round((df.loc[df['data'] == data_max,'custodia'].iloc[0] - total_aportado) / df.loc[df['data'] == data_max,'custodia'].iloc[0] * 100, 2) 

    # Desconto de IR no saque
    desconto_ir = rendimento * 0.15
    df.loc[df['data'] == data_max,'custodia'] = df.loc[df['data'] == data_max,'custodia'] - desconto_ir
    total_liquido = df.loc[df['data'] == data_max,'custodia'].iloc[0]


    #
    #st.metric(label="Total Líquido", value=num_to_str(total_liquido))
    st.markdown("""---------------------------------------""")
    col1, col2 = st.columns(2)
    col1.markdown("""
    \nTotal Aportado: {0}
    \nRendimento: {1}
    \nDesconto IR: {2}
    """.format(
        num_to_str(total_aportado),
        num_to_str(rendimento),
        num_to_str(desconto_ir)
        )
    )
    rendimento_porc = 0 if rendimento == 0 else rendimento_porc
    col2.metric(label="Total Líquido", value=num_to_str(total_liquido), delta=str(rendimento_porc)+'%')
    
    
    # Mudando formato das colunas para exibição
    aporte_serie = df['aporte']
    custodia_serie = df['custodia']
    df_plot = df.copy()
    
    df['aporte'] = df['aporte'].apply(num_to_str)
    df['custodia'] = df['custodia'].apply(num_to_str)

    ### Congiruação Tabela
    st.markdown("""---------------------------------------""")
    st.subheader('Resultado Tabela')
    
    
    df.loc[:,'data'] = df['data'].dt.strftime('%Y-%m-%d')
    df_plot.loc[:,'data'] = df_plot['data'].dt.strftime('%Y-%m-%d')
    
    gb = GridOptionsBuilder.from_dataframe(df_plot)
    gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
    gb.configure_side_bar() #Add a sidebar
    gridOptions = gb.build()
    
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        data_return_mode='AS_INPUT', 
        update_mode='MODEL_CHANGED', 
        fit_columns_on_grid_load=False,
        theme='streamlit', #Add theme color to the table
        enable_enterprise_modules=True,
        height=500, 
        width='100%',
        reload_data=True
    )
    
    def to_excel(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        format1 = workbook.add_format({'num_format': '0.00'}) 
        worksheet.set_column('A:A', None, format1)  
        writer.save()
        processed_data = output.getvalue()
        return processed_data
    
    st.download_button(label="Download tabela", data = to_excel(df_plot), file_name = 'dinheiro_simulado.xlsx')
    
    ### Configuração Gráfico
    st.markdown("""---------------------------------------""")
    st.subheader('Gráfico de evolução patrimônial')
    
    fig = px.line(df_plot, x='data', y='custodia', markers=True)
    fig.update_layout(
        xaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True,
            ticks='outside'),
        yaxis=dict(
            tickmode = "array",
            showline=True,
            showgrid=False,
            showticklabels=True,
            ticks='outside')
    )
    st.plotly_chart(fig, use_container_width=True)

    
    return df