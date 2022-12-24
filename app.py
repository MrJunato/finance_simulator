import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from simulador_financeiro import simulador
from datetime import datetime
import pyautogui

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month + 1

def clear_fields():
    ano_inicio.clear()
    mes_inicio.clear()

def main():
    ########## Sidebar ##########
    
    ########## Datas
    anos = range(1970, 2101)
    meses = [
        'Janeiro',
        'Fevereiro',
        'Março',
        'Abril',
        'Maio',
        'Junho',
        'Julho',
        'Agosto',
        'Setembro',
        'Outubro',
        'Novembro',
        'Dezembro'
    ]
    
    with st.sidebar:
        st.title("Controles do simulador")
        st.markdown("""Preencha os campos  para controlar sua simulação, caso não precise de alguma das informações, deixe o campo em branco ou com o número zero.""")
        
        # Limpando campos
        if st.button("Limpar campos"):
            pyautogui.hotkey("ctrl","F5")
        
        # Data inicio
        st.subheader("Data Inicio Simulação")
        ano_inicio = st.selectbox('Ano Inicio', anos)
        mes_inicio = st.selectbox('Mês Inicio', meses)
        get_mes_number = lambda mes: str(meses.index(mes) + 1).zfill(2)
        data_inicio = f'{ano_inicio}-{get_mes_number(mes_inicio)}-01'

        # Data Fim
        st.subheader("Data Fim Simulação")
        ano_filtrado = filter(lambda ano: ano >= ano_inicio, anos)
        ano_fim = st.selectbox('Ano Fim', ano_filtrado)

        meses_filtrados = meses[meses.index(mes_inicio):]
        lista_meses_fim = meses_filtrados if ano_inicio == ano_fim else meses
        mes_fim = st.selectbox('Mês Fim', lista_meses_fim)
        data_fim = f'{ano_fim}-{get_mes_number(mes_fim)}-01'

        # Informações sobre aporte
        st.subheader('Aportes')
        aporte_inicial = st.number_input("Qual será o primeiro aporte?", value=0.0)
        aporte_mensal = st.number_input("Quantos reais você deseja aportar por mês?", value=0.0)
        aumento_aporte = st.number_input("Qual a porcentagem de aumento desse aporte mês a mês?", value=0.0)
        aumento_aporte = aumento_aporte / 100

        # Aportes Bônus
        st.subheader('Aportes Bônus')
        meses_bonus = st.multiselect("Escolha os meses onde você fará aportes complementares caso existam, por exemplo vindo de bônus, décimo terceiro e etc...", meses)
        meses_bonus = list(map(lambda mes: int(get_mes_number(mes)), meses_bonus))
        valor_bonus = st.number_input("Qual seria o valor inicial desses aportes bônus?", value=0.0)
        crescimento_bonus = st.number_input("Qual a porcentagem de aumento desses aportes a cada ocorrência?", value=0.0)
        crescimento_bonus = crescimento_bonus / 100

        # Informações Complementares
        st.subheader('Informações Complementares')
        rendimento_anual = st.number_input("Qual será a porcentagem de rendimento anual de seu patrimônio?", value=0.0)
        rendimento_anual = rendimento_anual / 100

        # Adicionando tabela histórica
        st.subheader('Histórico personalizado')
        st.markdown("""
        Caso você já tenha algum histórico de aportes, use ele em formato excel e passe para o app utiliza-lo,
        lembrando que o excel precisa ter 3 colunas, data, aporte e custodia, seguindo o modelo abaixo:
        """)

        df = pd.DataFrame({'data':['2022-01-01', '2022-02-01', '2022-03-01','2022-04-01'],
                            'aporte':[1250, 1300, 1100, 1700],
                            'custodia':[1251, 2560, 3665, 5380]})

        # CSS to inject contained in a string
        hide_table_row_index = """
                <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
                </style>
                """
        # Inject CSS with Markdown
        st.markdown(hide_table_row_index, unsafe_allow_html=True)

        st.table(df)
        st.markdown("""
        - **data:** O aplicativo lê apenas o ano e o mês, mas o dia também precisa estar presente, é importante que o excel tenha entendido essa coluna como data
        
        - **aporte:** É o valor que foi guardado no mês descrito na coluna data
        
        - **custodia:** É o valor que você tinha disponível depois do aporte no fim do mês da data (esse valor precisa incluir os rendimentos para uma simulação mais realista)
        
        """)
        file = st.file_uploader('Abaixo, faça o upload de um arquivo excel:')

        if file is not None:
            upload_df = pd.read_excel(file)
            
            fdata_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            primeira_data_ok = upload_df['data'].min() == fdata_inicio
            primeira_data_nok = upload_df['data'].min() != fdata_inicio
            
            diff_datas = diff_month(upload_df['data'].max(), upload_df['data'].min())
            qtd_datas_ok = diff_datas == len(upload_df)
            qtd_datas_nok = diff_datas != len(upload_df)
            
            if primeira_data_ok & qtd_datas_ok:
                upload_df_plot = upload_df.copy()
                upload_df_plot.loc[:,'data'] = upload_df['data'].dt.strftime('%Y-%m-%d')
                st.table(upload_df_plot)
            else:
                upload_df = []
                if primeira_data_nok:
                    st.markdown('''*ATENÇÃO!!! A primeira data de seu arquivo não coincide com a primeira data que você passou nos controles, por conta disso a tabela não será utilizada, por favor atualize a data inicial ou seu arquivo*''')
                elif qtd_datas_nok:
                    st.markdown('''*ATENÇÃO!!! Existem meses faltando entre o primeiro e último mês de seu arquivo, por favor atualize seu arquivo para que ele possa ser utilizado*''')
                
        else:
            upload_df = []

            
    ########## Título Página ##########
    st.title("Simulador Financeiro")
    simulador(
        data_inicio = data_inicio,
        data_fim = data_fim,
        aporte_inicial = aporte_inicial,
        aporte_mensal = aporte_mensal,
        aumento_aporte = aumento_aporte,

        meses_bonus = meses_bonus,
        valor_bonus = valor_bonus,
        crescimento_bonus = crescimento_bonus,

        rendimento_anual = rendimento_anual,
        dados_reais = upload_df
    )
if __name__ == '__main__':
    main()
