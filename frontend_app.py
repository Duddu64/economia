import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime
import os
from ibge_data_fetcher import IBGEDataFetcher, fetch_online_data

# Configuração da página
st.set_page_config(
    page_title="Análise do Mercado de Trabalho - Setor Imobiliário",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .sidebar-info {
        background-color: #111;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .update-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .update-info {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header"> Análise do Mercado de Trabalho - Setor Imobiliário</h1>', unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("## Painel de Controle")

# Função para carregar dados
@st.cache_data
def load_data(use_updated=False):
    """Carrega os dados das tabelas CSV"""
    try:
        if use_updated:
            # Tentar carregar dados atualizados primeiro
            construcao_path = "./tabela1_construcao_civil.csv"
            imobiliarias_path = "./tabela2_atividades_imobiliarias.csv"
            
            if os.path.exists(construcao_path) and os.path.exists(imobiliarias_path):
                df_construcao = pd.read_csv(construcao_path)
                df_imobiliarias = pd.read_csv(imobiliarias_path)
                return df_construcao, df_imobiliarias, True
        
        # Carregar dados originais
        df_construcao = pd.read_csv("./tabela1_construcao_civil.csv")
        df_imobiliarias = pd.read_csv("./tabela2_atividades_imobiliarias.csv")
        return df_construcao, df_imobiliarias, False
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None, False

# Estado da aplicação
if 'data_updated' not in st.session_state:
    st.session_state.data_updated = False

# Carregar dados
df_construcao, df_imobiliarias, using_updated = load_data(st.session_state.data_updated)

if df_construcao is not None and df_imobiliarias is not None:
    
    # Sidebar - Controles
    data_source = "Dados Atualizados Online" if using_updated else "Dados Originais (2014-2023)"
    st.sidebar.markdown(f'<div class="sidebar-info"><b> {data_source}</b><br>Fonte: PNAD Contínua (IBGE)<br>Última atualização: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>', unsafe_allow_html=True)
    
    # Botão para atualizar dados
    if st.sidebar.button(" Atualizar Dados Online", type="primary"):
        with st.spinner("Buscando dados atualizados do IBGE..."):
            try:
                # Limpar cache antes de atualizar
                st.cache_data.clear()
                
                # Buscar dados online
                success = fetch_online_data()
                
                if success:
                    st.session_state.data_updated = True
                    st.rerun()
                else:
                    st.error("Falha ao atualizar dados. Usando dados locais.")
                    
            except Exception as e:
                st.error(f"Erro durante atualização: {e}")
    
    # Indicador de status dos dados
    if using_updated:
        st.markdown('<div class="update-success"> Usando dados atualizados da API do IBGE</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="update-info"> Usando dados originais. Clique em "Atualizar Dados Online" para buscar informações mais recentes.</div>', unsafe_allow_html=True)
    
    # Seleção de visualização
    view_option = st.sidebar.selectbox(
        "Selecione a Visualização:",
        ["Visão Geral", "Taxa de Informalidade", "Emprego por Setor", "Comparação Detalhada", "Análise Temporal"]
    )
    
    # Filtros
    st.sidebar.markdown("### 🔍 Filtros")
    anos_disponiveis = sorted(df_construcao['Ano'].unique())
    anos_selecionados = st.sidebar.slider(
        "Período de Análise:",
        min_value=int(min(anos_disponiveis)),
        max_value=int(max(anos_disponiveis)),
        value=(int(min(anos_disponiveis)), int(max(anos_disponiveis))),
        step=1
    )
    
    # Filtrar dados por período
    df_construcao_filtered = df_construcao[
        (df_construcao['Ano'] >= anos_selecionados[0]) & 
        (df_construcao['Ano'] <= anos_selecionados[1])
    ]
    df_imobiliarias_filtered = df_imobiliarias[
        (df_imobiliarias['Ano'] >= anos_selecionados[0]) & 
        (df_imobiliarias['Ano'] <= anos_selecionados[1])
    ]
    
    # Conteúdo principal baseado na seleção
    if view_option == "Visão Geral":
        st.markdown("## Visão Geral do Mercado de Trabalho")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            latest_construcao = df_construcao_filtered['Taxa de Informalidade Setorial (%)'].iloc[-1]
            first_construcao = df_construcao_filtered['Taxa de Informalidade Setorial (%)'].iloc[0]
            st.metric(
                "Taxa Informalidade - Construção",
                f"{latest_construcao:.1f}%",
                f"{latest_construcao - first_construcao:.1f}%"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            latest_imobiliarias = df_imobiliarias_filtered['Taxa de Informalidade Setorial (%)'].iloc[-1]
            first_imobiliarias = df_imobiliarias_filtered['Taxa de Informalidade Setorial (%)'].iloc[0]
            st.metric(
                "Taxa Informalidade - Imobiliárias",
                f"{latest_imobiliarias:.1f}%",
                f"{latest_imobiliarias - first_imobiliarias:.1f}%"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            latest_ocupados_construcao = df_construcao_filtered['Total de Ocupados (PNAD, milhões)'].iloc[-1]
            first_ocupados_construcao = df_construcao_filtered['Total de Ocupados (PNAD, milhões)'].iloc[0]
            st.metric(
                "Total Ocupados - Construção",
                f"{latest_ocupados_construcao:.1f}M",
                f"{latest_ocupados_construcao - first_ocupados_construcao:.1f}M"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            latest_ocupados_imobiliarias = df_imobiliarias_filtered['Total de Ocupados (PNAD, milhões)'].iloc[-1]
            first_ocupados_imobiliarias = df_imobiliarias_filtered['Total de Ocupados (PNAD, milhões)'].iloc[0]
            st.metric(
                "Total Ocupados - Imobiliárias",
                f"{latest_ocupados_imobiliarias:.1f}M",
                f"{latest_ocupados_imobiliarias - first_ocupados_imobiliarias:.1f}M"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráfico de resumo
        st.markdown("### Evolução da Taxa de Informalidade")
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_construcao_filtered['Ano'],
            y=df_construcao_filtered['Taxa de Informalidade Setorial (%)'],
            mode='lines+markers',
            name='Construção Civil',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=8),
            hovertemplate='<b>Construção Civil</b><br>Ano: %{x}<br>Taxa: %{y:.1f}%<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=df_imobiliarias_filtered['Ano'],
            y=df_imobiliarias_filtered['Taxa de Informalidade Setorial (%)'],
            mode='lines+markers',
            name='Atividades Imobiliárias',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8),
            hovertemplate='<b>Atividades Imobiliárias</b><br>Ano: %{x}<br>Taxa: %{y:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title="Taxa de Informalidade Setorial",
            xaxis_title="Ano",
            yaxis_title="Taxa de Informalidade (%)",
            hovermode='x unified',
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif view_option == "Taxa de Informalidade":
        st.markdown("## 📈 Análise da Taxa de Informalidade")
        
        # Gráfico comparativo
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_construcao_filtered['Ano'],
            y=df_construcao_filtered['Taxa de Informalidade Setorial (%)'],
            mode='lines+markers',
            name='Construção Civil',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=10)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_imobiliarias_filtered['Ano'],
            y=df_imobiliarias_filtered['Taxa de Informalidade Setorial (%)'],
            mode='lines+markers',
            name='Atividades Imobiliárias',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=10)
        ))
        
        fig.update_layout(
            title="Comparação da Taxa de Informalidade entre Setores",
            xaxis_title="Ano",
            yaxis_title="Taxa de Informalidade (%)",
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Análise textual
        st.markdown("### 🔍 Insights")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Construção Civil:**
            - Mantém consistentemente uma taxa de informalidade acima de 50%
            - Setor com alta precariedade estrutural
            - Variações sazonais significativas
            """)
        
        with col2:
            st.markdown("""
            **Atividades Imobiliárias:**
            - Apresenta menor informalidade, geralmente abaixo de 45%
            - Setor mais formalizado e regulamentado
            - Tendência de estabilização nos últimos anos
            """)
    
    elif view_option == "Emprego por Setor":
        st.markdown("## 👷 Análise do Emprego por Setor")
        
        # Seletor de setor
        setor_selecionado = st.selectbox(
            "Selecione o setor para análise:",
            ["Construção Civil", "Atividades Imobiliárias"]
        )
        
        if setor_selecionado == "Construção Civil":
            df_selected = df_construcao_filtered
            color_scheme = ['#ff7f0e', '#ffbb78', '#d62728']
        else:
            df_selected = df_imobiliarias_filtered
            color_scheme = ['#1f77b4', '#aec7e8', '#2ca02c']
        
        # Gráfico de emprego
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_selected['Ano'],
            y=df_selected['Total de Ocupados (PNAD, milhões)'],
            mode='lines+markers',
            name='Total de Ocupados',
            line=dict(color=color_scheme[0], width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_selected['Ano'],
            y=df_selected['Empregados com Carteira (PNAD, milhões)'],
            mode='lines+markers',
            name='Empregados com Carteira',
            line=dict(color=color_scheme[1], width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_selected['Ano'],
            y=df_selected['Conta Própria (PNAD, milhões)'],
            mode='lines+markers',
            name='Conta Própria',
            line=dict(color=color_scheme[2], width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title=f"Evolução do Emprego - {setor_selecionado}",
            xaxis_title="Ano",
            yaxis_title="Milhões de Pessoas",
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de dados
        st.markdown("### Dados Detalhados")
        st.dataframe(df_selected, use_container_width=True)
    
    elif view_option == "Comparação Detalhada":
        st.markdown("## Comparação Detalhada entre Setores")
        
        # Gráficos lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Construção Civil")
            fig1 = px.bar(
                df_construcao_filtered,
                x='Ano',
                y=['Empregados com Carteira (PNAD, milhões)', 
                   'Empregados sem Carteira (PNAD, milhões)', 
                   'Conta Própria (PNAD, milhões)'],
                title="Composição do Emprego - Construção Civil",
                color_discrete_sequence=['#ff7f0e', '#ffbb78', '#d62728']
            )
            fig1.update_layout(height=400)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.markdown("#### Atividades Imobiliárias")
            fig2 = px.bar(
                df_imobiliarias_filtered,
                x='Ano',
                y=['Empregados com Carteira (PNAD, milhões)', 
                   'Empregados sem Carteira (PNAD, milhões)', 
                   'Conta Própria (PNAD, milhões)'],
                title="Composição do Emprego - Atividades Imobiliárias",
                color_discrete_sequence=['#1f77b4', '#aec7e8', '#2ca02c']
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
    
    elif view_option == "Análise Temporal":
        st.markdown("## ⏱️ Análise Temporal Avançada")
        
        # Gráfico de tendências
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Taxa de Informalidade', 'Total de Ocupados', 
                          'Empregados com Carteira', 'Variação Anual'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Taxa de Informalidade
        fig.add_trace(
            go.Scatter(x=df_construcao_filtered['Ano'], 
                      y=df_construcao_filtered['Taxa de Informalidade Setorial (%)'],
                      name='Construção - Informalidade', line=dict(color='#ff7f0e')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_imobiliarias_filtered['Ano'], 
                      y=df_imobiliarias_filtered['Taxa de Informalidade Setorial (%)'],
                      name='Imobiliárias - Informalidade', line=dict(color='#1f77b4')),
            row=1, col=1
        )
        
        # Total de Ocupados
        fig.add_trace(
            go.Scatter(x=df_construcao_filtered['Ano'], 
                      y=df_construcao_filtered['Total de Ocupados (PNAD, milhões)'],
                      name='Construção - Total', line=dict(color='#ff7f0e')),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=df_imobiliarias_filtered['Ano'], 
                      y=df_imobiliarias_filtered['Total de Ocupados (PNAD, milhões)'],
                      name='Imobiliárias - Total', line=dict(color='#1f77b4')),
            row=1, col=2
        )
        
        # Empregados com Carteira
        fig.add_trace(
            go.Scatter(x=df_construcao_filtered['Ano'], 
                      y=df_construcao_filtered['Empregados com Carteira (PNAD, milhões)'],
                      name='Construção - CLT', line=dict(color='#ff7f0e')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_imobiliarias_filtered['Ano'], 
                      y=df_imobiliarias_filtered['Empregados com Carteira (PNAD, milhões)'],
                      name='Imobiliárias - CLT', line=dict(color='#1f77b4')),
            row=2, col=1
        )
        
        # Saldo CAGED
        fig.add_trace(
            go.Bar(x=df_construcao_filtered['Ano'], 
                   y=df_construcao_filtered['Saldo Formal (CAGED, mil)'],
                   name='Construção - CAGED', marker_color='#ff7f0e', opacity=0.7),
            row=2, col=2
        )
        fig.add_trace(
            go.Bar(x=df_imobiliarias_filtered['Ano'], 
                   y=df_imobiliarias_filtered['Saldo Formal (CAGED, mil)'],
                   name='Imobiliárias - CAGED', marker_color='#1f77b4', opacity=0.7),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=True, title_text="Análise Temporal Completa")
        st.plotly_chart(fig, use_container_width=True)
    
    # Rodapé
    st.markdown("---")
    st.markdown("### Relatório e Dados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(" Download Relatório PDF"):
            try:
                with open("./relatorio_analitico.pdf", "rb") as pdf_file:
                    st.download_button(
                        label="Baixar PDF",
                        data=pdf_file.read(),
                        file_name="relatorio_mercado_trabalho.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Erro ao carregar PDF: {e}")
    
    with col2:
        if st.button("📊 Download Dados CSV"):
            # Combinar dados para download
            combined_data = {
                'Ano': df_construcao['Ano'],
                'Construcao_Total_Ocupados': df_construcao['Total de Ocupados (PNAD, milhões)'],
                'Construcao_Taxa_Informalidade': df_construcao['Taxa de Informalidade Setorial (%)'],
                'Imobiliarias_Total_Ocupados': df_imobiliarias['Total de Ocupados (PNAD, milhões)'],
                'Imobiliarias_Taxa_Informalidade': df_imobiliarias['Taxa de Informalidade Setorial (%)']
            }
            df_combined = pd.DataFrame(combined_data)
            csv = df_combined.to_csv(index=False)
            st.download_button(
                label="Baixar CSV",
                data=csv,
                file_name="dados_mercado_trabalho.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("Resetar para Dados Originais"):
            st.session_state.data_updated = False
            st.cache_data.clear()
            st.rerun()

else:
    st.error("❌ Erro ao carregar os dados. Verifique se os arquivos CSV estão disponíveis.")

# Informações na sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Sobre")
st.sidebar.markdown("""
**Análise do Mercado de Trabalho**

Esta aplicação analisa a evolução do emprego nos setores de Construção Civil e Atividades Imobiliárias no Brasil.

**Funcionalidades:**
- Visualizações interativas
- Atualização online de dados
- Análise temporal avançada
- Download de relatórios

**Fontes de Dados:**
- PNAD Contínua (IBGE)
- Novo CAGED (MTE)
- API SIDRA (IBGE)
""")

st.sidebar.markdown("---")

