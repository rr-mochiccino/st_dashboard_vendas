import streamlit as st
import requests
import pandas as pd
import plotly.express as px



#Configurando o layout inicial da página

st.set_page_config(page_title="Vendas",
                page_icon=":ticket:",
                layout="wide")


##Funções

def formata_numero(valor, prefixo = ''):
    """
    Formata números para diminuir e arrendondar o seu 
    valor para duas casas decimais. Caso o valor for 
    maior que 1000, ele é divido por 1000, caso não, ele 
    retorna ele mesmo arredondado com a unidade default ('') ou com a 
    que foi estabelecida.
    
    """
    for unidade in ['',"mil"]:
        if valor < 1000:
            return f"{prefixo} {valor:.2f} {unidade}"
        else:
            valor /= 1000
    return f"{prefixo} {valor:.2f} milhões"

def formata_traces(fig, tabela_original, nome_coluna, posicao="outside"):
    """
    Formata os traces de um gráfico, colocando os números no 
    gráfico de barras na posição desejada e formatado de acordo
    com a função formata_numero.
    
    """
    fig.update_traces(texttemplate='%{text}',  
                    textposition='outside')
    
    fig.update_traces(
        text=[formata_numero(val) for val in tabela_original[nome_coluna]]
    )
    fig.update_yaxes(
        ticktext=[formata_numero(val) for val in tabela_original[nome_coluna].unique()]
    )
                        



st.title(":blue[DASHBOARD DE VENDAS] :ticket:")


url = 'https://labdados.com/produtos'
regioes = ["Brasil","Centro-Oeste","Nordeste","Norte","Sudeste","Sul"]

##Barra Lateral para Filtragem

st.sidebar.title("Filtros")
regiao = st.sidebar.selectbox("Região",regioes)
if regiao == "Brasil":    #Em caso de ser Brasil, que não se tem na API
    regiao=''

todos_anos = st.sidebar.checkbox("Dados de todo o período", value = True)
ano = '' if todos_anos else st.sidebar.slider("Ano",2020,2023)

##Extraindo os dados da API e colocando no app

query_string = {"regiao":regiao.lower(),"ano":ano} #query para colocar na url da API
response = requests.get(url, params = query_string)
dados = pd.DataFrame.from_dict(response.json())
dados["Data da Compra"] = pd.to_datetime(dados["Data da Compra"], format= "%d/%m/%Y")

if filtro_vendedores := st.sidebar.multiselect(
    "Vendedores", dados["Vendedor"].unique()
):
    dados = dados[dados["Vendedor"].isin(filtro_vendedores)] #Usa o DataFrame p/ filtrar o vendedor


###Tabelas

##Tabelas de Receita
receita_estados = dados.groupby("Local da compra")[["Preço"]].sum()
receita_estados = dados.drop_duplicates(subset="Local da compra")\
                                        [["Local da compra","lat","lon"]]\
                                        .merge(receita_estados, left_on = "Local da compra", right_index= True)\
                                        .sort_values("Preço", ascending= False)

receita_mensal = dados.set_index("Data da Compra")\
                        .groupby(pd.Grouper(freq =  "M"))["Preço"].sum()\
                        .reset_index()
receita_mensal["Ano"] = receita_mensal["Data da Compra"].dt.year
receita_mensal["Mês"] = receita_mensal["Data da Compra"].dt.month_name()

receita_categorias = dados.groupby("Categoria do Produto")[["Preço"]].sum()\
                            .sort_values("Preço", ascending=False)


##Tabelas de Qtd. de Vendas
qt_vendas_estados = pd.DataFrame(dados.groupby("Local da compra")["Preço"].count())
qt_vendas_estados = dados.drop_duplicates(subset="Local da compra")\
                                        [["Local da compra","lat","lon"]]\
                                        .merge(qt_vendas_estados, left_on="Local da compra", right_index=True)\
                                        .sort_values("Preço",ascending=False)

qt_vendas_mensal = pd.DataFrame(dados.set_index("Data da Compra")\
                                                                .groupby(pd.Grouper(freq = "M"))["Preço"]\
                                                                .count()).reset_index()
qt_vendas_mensal["Ano"] = qt_vendas_mensal["Data da Compra"].dt.year
qt_vendas_mensal["Mes"] = qt_vendas_mensal["Data da Compra"].dt.month_name()

qt_vendas_categorias = pd.DataFrame(dados.groupby("Categoria do Produto")["Preço"].count()\
                                                                                .sort_values(ascending=False))

##Tabelas de Vendedores
vendedores = pd.DataFrame(dados.groupby("Vendedor")["Preço"]\
                                .agg(["sum","count"]))


###Visualização no streamlit


##Gráficos

#Criando o gráfico de mapa de Receitas
fig_mapa_receita = px.scatter_geo(receita_estados,
                                lat = "lat", lon = "lon",
                                scope = "south america",
                                size = "Preço",
                                template = "seaborn",
                                hover_name = "Local da compra",
                                hover_data = {"lat": False, "lon": False, "Preço":True},
                                title = "Receita por Estado")
fig_mapa_receita.update_traces(hovertemplate='<b>%{hovertext}</b><br>Receita: %{marker.size}')
#Criando o gráfico de linhas de Receitas
fig_receita_mensal = px.line(receita_mensal,
                            x = "Mês", y = "Preço",
                            markers = True,
                            range_y = (0,receita_mensal.max()),
                            color = "Ano",
                            line_dash= "Ano",
                            title = "Receita Mensal")
fig_receita_mensal.update_layout(yaxis_title = "Receita")
#Criando o gráfico de barra Receita Estados
fig_receita_estados = px.bar(receita_estados.head(),
                            x = "Local da compra", y = "Preço",
                            text = "Preço",
                            text_auto = True,
                            title = "Top 5 Estados por Receita")
fig_receita_estados.update_layout(yaxis_title="Receita")
formata_traces(fig_receita_estados, receita_estados, "Preço")
fig_receita_estados.update_traces(hovertemplate='<b>%{x}</b><br>Receita: %{y}')
#Criando o gráfico de barra Receita Categorias
fig_receita_categorias = px.bar(receita_categorias, 
                                y = "Preço",
                                text="Preço",
                                text_auto = True,
                                title = "Receita por Categoria")
fig_receita_categorias.update_layout(yaxis_title="Receita",
                                    showlegend = False)
formata_traces(fig_receita_categorias, receita_categorias, "Preço")
fig_receita_categorias.update_traces(hovertemplate='<b>%{x}</b><br>Receita: %{y}')


#Criando o gráfico de mapa de Quantidade de Vendas por Estado
fig_mapa_qt_vendas = px.scatter_geo(qt_vendas_estados, 
                                lat = "lat", 
                                lon= "lon", 
                                scope = "south america", 
                                #fitbounds = 'locations', 
                                template= "seaborn", 
                                size = "Preço", 
                                hover_name ="Local da compra", 
                                hover_data = {"lat":False,"lon":False,"Preço":True},
                                title = "Vendas por estado")
fig_mapa_qt_vendas.update_traces(hovertemplate='<b>%{hovertext}</b><br>Qtd.: %{marker.size}')
#Criando o gráfico de linhas de Quantidade de Vendas Mensal
fig_qt_vendas_mensal = px.line(qt_vendas_mensal,
                                x = "Mes", y = "Preço",
                                markers = True,
                                range_y =(0,qt_vendas_mensal.max()),
                                color = "Ano",
                                line_dash = "Ano",
                                title = "Quantidade de Vendas Mensal")
fig_qt_vendas_mensal.update_layout(yaxis_title = "Quantidade de Vendas")
#Criando o gráfico de barras com top 5 Estados c/ maior Qtd. de Vendas
fig_qt_vendas_estados = px.bar(qt_vendas_estados.head(),
                                x = "Local da compra", y = "Preço",
                                text_auto = "True",
                                hover_data = {"lat": False, "lon": False},
                                title = "Top 5 Estados por Quantidade de Vendas")
fig_qt_vendas_estados.update_traces(hovertemplate='<b>%{x}</b><br>Qtd.: %{y}')
fig_qt_vendas_estados.update_layout(yaxis_title = "Quantidade de Vendas")
#Criando o gráfico de barras de Quantidade de Vendas por Categoria
fig_qt_vendas_categorias = px.bar(qt_vendas_categorias,
                                    text_auto = True,
                                    title = "Vendas por Categoria",
                                    hover_data = {"variable":False})
fig_qt_vendas_categorias.update_layout(showlegend = False, 
                                        yaxis_title = "Quantidade de Vendas")
fig_qt_vendas_categorias.update_traces(hovertemplate='<b>%{x}</b><br>Qtd.: %{y}')



##Tabs

aba1,aba2,aba3 = st.tabs(["Receita","Quantidade de Vendas","Vendedores"])

with aba1: #RECEITA
    #Layout com duas colunas
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric("Receita", formata_numero(dados["Preço"].sum(), "R$")) #Métrica da Receita
        st.plotly_chart(fig_mapa_receita, use_container_width=True) #Gráfico de Mapa do Local das Compras
        st.plotly_chart(fig_receita_estados, use_container_width=True) #Gráfico de Barras das Receitas dos Estados
    with coluna2:
        st.metric("Quantidade de vendas", formata_numero(dados.shape[0])) #Métrica Qtd. Vendas
        st.plotly_chart(fig_receita_mensal, use_container_width=True) #Gráfico de Linhas mostrando a Receita
        st.plotly_chart(fig_receita_categorias, use_container_width=True) #Gráfico de Barras das Receitas por Categoria

with aba2: #QUANTIDADE DE VENDAS
    #Layout com duas colunas
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric("Receita", formata_numero(dados["Preço"].sum(), "R$")) #Métrica da Receita
        st.plotly_chart(fig_mapa_qt_vendas, use_container_width=True) #Gráfico de Mapa da Qtd.Vendas
        st.plotly_chart(fig_qt_vendas_estados, use_container_width=True) #Gráfico de barras com top 5 Estados c/ maior Qtd. de Vendas
    with coluna2:
        st.metric("Quantidade de vendas", formata_numero(dados.shape[0])) #Métrica Qtd. Vendas
        st.plotly_chart(fig_qt_vendas_mensal, use_container_width=True) #Gráfico de Linhas 
        st.plotly_chart(fig_qt_vendas_categorias, use_container_width=True) #
with aba3: #VENDEDORES
    qtd_vendedores = st.number_input("Quantidade de Vendedores",2,10,5)

    #Layout com duas colunas
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric("Receita", formata_numero(dados["Preço"].sum(), "R$")) #Métrica da Receita
        #Gráfico da Receita por Vendedor
        fig_receita_vendedores = px.bar(vendedores[["sum"]].sort_values("sum", ascending=False).head(qtd_vendedores),
                                        x = "sum", 
                                        y = vendedores[["sum"]].sort_values("sum", ascending=False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title = f"Top {qtd_vendedores} vendedores (Receita)")
        fig_receita_vendedores.update_layout(yaxis_title="",xaxis_title="")
        fig_receita_vendedores.update_traces(hovertemplate='<b>%{y}</b><br>Receita: %{x}')
        st.plotly_chart(fig_receita_vendedores,use_container_width=True)
    with coluna2:
        st.metric("Quantidade de vendas", formata_numero(dados.shape[0])) #Métrica Qtd. Vendas
        #Gráfico de Vendas dos Vendedores
        fig_vendas_vendedores = px.bar(vendedores[["count"]].sort_values("count", ascending=False).head(qtd_vendedores),
                                        x = "count", 
                                        y = vendedores[["count"]].sort_values("count", ascending=False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title = f"Top {qtd_vendedores} vendedores (Quantidade de Vendas)")
        fig_vendas_vendedores.update_layout(yaxis_title="",xaxis_title="")
        fig_vendas_vendedores.update_traces(hovertemplate='<b>%{y}</b><br>Qtd.: %{x}')
        st.plotly_chart(fig_vendas_vendedores,use_container_width=True)






