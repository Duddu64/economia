import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os
from ibge_data_fetcher import fetch_online_data, fetch_bcb_data

def configure_page():
    """Configura a página e aplica CSS customizado."""
    st.set_page_config(
        page_title="Análise do Mercado de Trabalho - Setor Imobiliário",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
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
            background-color: #111;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 5px solid #1f77b4;
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1);
        }
        .sidebar-info {
            background-color: #f0f2f6;
            color: #333;
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
        .analysis-section {
            background-color: #111;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            border-left: 4px solid #17a2b8;
            word-wrap: break-word;
            overflow-wrap: break-word;
            max-width: 100%;
        }
        .stContainer {
            max-width: 100%;
            overflow-x: hidden;
        }
        .metric-card {
            background-color: #222;  /* Fundo mais escuro para melhor contraste */
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 5px solid #1f77b4;
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        
        .stPlotly {
            width: 100% !important;
            height: 500px !important;
        }
        
        .plot-container {
            width: 100%;
            overflow-x: auto;
            border-radius: 8px;
            padding: 10px;
            background-color: #1a1a1a;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

def display_header():
    """Exibe o título principal da aplicação."""
    st.markdown('<h1 class="main-header">Análise do Mercado de Trabalho - Setor Imobiliário</h1>', unsafe_allow_html=True)

# --- CARREGAMENTO E GESTÃO DE DADOS ---
@st.cache_data
def load_data(use_updated=False):
    """Carrega os dados das tabelas CSV, tratando possíveis erros."""
    try:
        prefix = "_updated" if use_updated else ""
        df_construcao = pd.read_csv(f"tabela1_construcao_civil{prefix}.csv")
        df_imobiliarias = pd.read_csv(f"tabela2_atividades_imobiliarias{prefix}.csv")
        
        # Tenta carregar dados do FGTS, mas não falha se não encontrar
        try:
            df_fgts = pd.read_csv("fgts_arrecadacao.csv")
        except FileNotFoundError:
            df_fgts = None
            
        return df_construcao, df_imobiliarias, df_fgts, use_updated
    except FileNotFoundError as e:
        st.error(f"Erro Crítico: Arquivo de dados não encontrado: {e.filename}. Verifique se os arquivos CSV estão na pasta correta.")
        return None, None, None, False
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
        return None, None, None, False

def initialize_session_state():
    """Inicializa o estado da sessão."""
    if 'data_updated' not in st.session_state:
        st.session_state.data_updated = False

def filter_data(df_construcao, df_imobiliarias, anos_selecionados):
    """Filtra os dados com base no período selecionado."""
    df_construcao_filtered = df_construcao[
        (df_construcao['Ano'] >= anos_selecionados[0]) & 
        (df_construcao['Ano'] <= anos_selecionados[1])
    ]
    df_imobiliarias_filtered = df_imobiliarias[
        (df_imobiliarias['Ano'] >= anos_selecionados[0]) & 
        (df_imobiliarias['Ano'] <= anos_selecionados[1])
    ]
    return df_construcao_filtered, df_imobiliarias_filtered

def create_sidebar(df_construcao, using_updated):
    """Cria e gerencia a barra lateral com controles reorganizados."""
    st.sidebar.markdown("## Painel de Controle")
    
    # Seção: Fonte de Dados
    st.sidebar.markdown("### Fonte de Dados")
    data_source_msg = "Dados Atualizados Online" if using_updated else "Dados Originais Locais"
    st.sidebar.markdown(f'<div class="sidebar-info"><b>Fonte:</b> {data_source_msg}<br><i>PNAD Contínua (IBGE)</i></div>', unsafe_allow_html=True)
    
    # Botão para atualizar dados (não retorna nada diretamente)
    if st.sidebar.button("Atualizar Dados Online", use_container_width=True, type="primary"):
        # Marca que a atualização foi solicitada
        st.session_state.update_requested = True
        # Não retorna aqui, apenas continua o fluxo
    
    # Seção: Navegação
    st.sidebar.markdown("### Visualizações")
    view_option = st.sidebar.selectbox(
        "Selecione a Análise:",
        [
            "Visão Geral", 
            "Análise de Informalidade", 
            "Composição do Emprego", 
            "Crescimento PJ/Informal + FGTS",
            "Juros no Financiamento Imobiliário"
        ],
        key='view_selector'
    )
    
    # Seção: Filtros
    st.sidebar.markdown("### 🔍 Filtros")
    anos_disponiveis = sorted(df_construcao['Ano'].unique())
    anos_selecionados = st.sidebar.slider(
        "Período de Análise:",
        min_value=int(min(anos_disponiveis)),
        max_value=int(max(anos_disponiveis)),
        value=(int(min(anos_disponiveis)), int(max(anos_disponiveis))),
        step=1
    )
    
    setores_selecionados = st.sidebar.multiselect(
        "Setores Analisados:",
        ["Construção Civil", "Atividades Imobiliárias"],
        default=["Construção Civil", "Atividades Imobiliárias"]
    )
    
    # Seção: Ações
    st.sidebar.markdown("### Ações")
    st.sidebar.markdown("As ações de download estarão disponíveis após carregar os dados")
    
    return view_option, anos_selecionados, setores_selecionados, False

def handle_data_update():
    """Gerencia a atualização de dados online."""
    with st.spinner("Buscando dados atualizados do IBGE..."):
        st.cache_data.clear()
        success = fetch_online_data()
        if success:
            st.session_state.data_updated = True
            st.success("Dados atualizados com sucesso! A página será recarregada.")
            st.rerun()  # Recarrega a página para aplicar os novos dados
        else:
            st.error("Falha ao atualizar dados. Usando dados locais.")

def create_sidebar_actions(df_construcao_filtered, df_imobiliarias_filtered):
    """Cria as ações da sidebar (download e reset)."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Ações")
    
    # Download
    df_combined = pd.merge(df_construcao_filtered, df_imobiliarias_filtered, on="Ano", suffixes=('_construcao', '_imob'))
    csv = df_combined.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="Baixar Dados Filtrados (CSV)",
        data=csv,
        file_name="dados_filtrados_mercado_imobiliario.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    # Reset
    if st.sidebar.button("Resetar para Dados Originais", use_container_width=True):
        st.session_state.data_updated = False
        st.cache_data.clear()
        st.rerun()

def show_data_status(using_updated):
    """Exibe o status dos dados carregados."""
    if using_updated:
        st.markdown('<div class="update-success">Você está vendo os dados mais recentes, buscados online.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="update-info">Você está vendo os dados originais. Para informações mais atuais, use o botão "Atualizar Dados Online".</div>', unsafe_allow_html=True)

def create_metrics_cards(df_construcao_filtered, df_imobiliarias_filtered):
    """Cria os cards de métricas principais."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Ocupados (Construção)", f"{df_construcao_filtered['Total de Ocupados (PNAD, milhões)'].iloc[-1]:.1f}M")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Ocupados (Imobiliário)", f"{df_imobiliarias_filtered['Total de Ocupados (PNAD, milhões)'].iloc[-1]:.1f}M")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Informalidade (Construção)", f"{df_construcao_filtered['Taxa de Informalidade Setorial (%)'].iloc[-1]:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Informalidade (Imobiliário)", f"{df_imobiliarias_filtered['Taxa de Informalidade Setorial (%)'].iloc[-1]:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)

def show_visao_geral(df_construcao_filtered, df_imobiliarias_filtered, setores_selecionados):
    """Exibe a visualização de Visão Geral."""
    st.markdown("## Visão Geral do Mercado de Trabalho")
    
    # Métricas em container
    with st.container():
        create_metrics_cards(df_construcao_filtered, df_imobiliarias_filtered)
    
    # Gráfico principal em container com div personalizada
    st.markdown("### Evolução do Total de Ocupados vs. Taxa de Informalidade")
    
    with st.container():
        # Criar figura com eixos secundários
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Dicionário de cores
        cores = {
            'construcao_ocupados': '#1f77b4',
            'construcao_informalidade': '#ff7f0e',
            'imobiliario_ocupados': '#2ca02c',
            'imobiliario_informalidade': '#d62728'
        }
        
        # Adicionar traços para cada setor
        if "Construção Civil" in setores_selecionados:
            # Barras para ocupados na construção
            fig.add_trace(
                go.Bar(
                    x=df_construcao_filtered['Ano'], 
                    y=df_construcao_filtered['Total de Ocupados (PNAD, milhões)'], 
                    name='Ocupados - Construção', 
                    marker_color=cores['construcao_ocupados'], 
                    opacity=0.7
                ), 
                secondary_y=False
            )
            
            # Linha para informalidade na construção
            fig.add_trace(
                go.Scatter(
                    x=df_construcao_filtered['Ano'], 
                    y=df_construcao_filtered['Taxa de Informalidade Setorial (%)'], 
                    name='Informalidade (%) - Construção', 
                    marker_color=cores['construcao_informalidade'], 
                    mode='lines+markers',
                    line=dict(width=3)
                ), 
                secondary_y=True
            )
        
        if "Atividades Imobiliárias" in setores_selecionados:
            # Barras para ocupados no imobiliário
            fig.add_trace(
                go.Bar(
                    x=df_imobiliarias_filtered['Ano'], 
                    y=df_imobiliarias_filtered['Total de Ocupados (PNAD, milhões)'], 
                    name='Ocupados - Imobiliário', 
                    marker_color=cores['imobiliario_ocupados'], 
                    opacity=0.7
                ), 
                secondary_y=False
            )
            
            # Linha para informalidade no imobiliário
            fig.add_trace(
                go.Scatter(
                    x=df_imobiliarias_filtered['Ano'], 
                    y=df_imobiliarias_filtered['Taxa de Informalidade Setorial (%)'], 
                    name='Informalidade (%) - Imobiliário', 
                    marker_color=cores['imobiliario_informalidade'], 
                    mode='lines+markers',
                    line=dict(width=3)
                ), 
                secondary_y=True
            )
        
        # Configurações do layout - CORRIGIDO: autosize em vez de responsive
        fig.update_layout(
            height=500, 
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=10)
            ),
            barmode='group',
            bargap=0.25,
            bargroupgap=0.1,
            margin=dict(l=50, r=50, t=50, b=100),
            title_text="Evolução do Emprego e Informalidade",
            title_x=0.5,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            autosize=True  # Propriedade correta para redimensionamento
        )
        
        # Configurar eixos (mantido igual)
        fig.update_yaxes(
            title_text="Total de Ocupados (milhões)", 
            secondary_y=False,
            rangemode='tozero',
            showgrid=False,
            zerolinecolor='lightgrey',
            title_font=dict(size=12)
        )
        
        fig.update_yaxes(
            title_text="Taxa de Informalidade (%)", 
            secondary_y=True,
            range=[0, 100],
            rangemode='tozero',
            showgrid=True,
            gridcolor='rgba(211,211,211,0.3)',
            zerolinecolor='lightgrey',
            title_font=dict(size=12)
        )
        
        fig.update_xaxes(
            title_text="Ano",
            type='category',
            showline=True,
            linecolor='lightgrey',
            title_font=dict(size=12)
        )
        
        # Container para controle de overflow
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={'responsive': True})
        st.markdown('</div>', unsafe_allow_html=True)       

def show_pj_informal_fgts_impact(df_construcao_filtered, df_fgts, anos_selecionados):
    """Exibe análise do crescimento PJ/Informal e impacto no FGTS."""
    st.markdown("## Crescimento do Trabalho PJ/Informal e Impacto no FGTS")
    
    st.markdown("""
    <div class="analysis-section">
        <b>Análise:</b> O aumento do trabalho por conta própria (PJ) e informal na construção civil tem impacto direto na arrecadação do FGTS, 
        uma vez que esses trabalhadores não contribuem para o fundo. Isso reduz a capacidade de investimento em habitação popular e infraestrutura.
    </div>
    """, unsafe_allow_html=True)
    
    # Criar DataFrame combinado
    df_combined = df_construcao_filtered.copy()
    
    # Calcular trabalho informal/PJ (conta própria + sem carteira)
    df_combined['Trabalho Informal/PJ'] = (
        df_combined['Conta Própria (PNAD, milhões)'] + 
        df_combined['Empregados sem Carteira (PNAD, milhões)']
    )
    
    # Adicionar dados do FGTS se disponível
    if df_fgts is not None:
        df_combined = pd.merge(df_combined, df_fgts, on='Ano', how='left')
    
    # Criar visualização
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Trabalho Informal/PJ (barra)
    fig.add_trace(
        go.Bar(
            x=df_combined['Ano'],
            y=df_combined['Trabalho Informal/PJ'],
            name='Trabalho Informal/PJ (milhões)',
            marker_color='#FF7F0E',
            opacity=0.7
        ),
        secondary_y=False
    )
    
    # FGTS (linha) se disponível
    if df_fgts is not None and 'Arrecadacao_Bruta_R_Bilhoes' in df_combined:
        fig.add_trace(
            go.Scatter(
                x=df_combined['Ano'],
                y=df_combined['Arrecadacao_Bruta_R_Bilhoes'],
                name='Arrecadação FGTS (R$ Bi)',
                mode='lines+markers',
                line=dict(color='#1F77B4', width=3)
            ),
            secondary_y=True
        )
    
    fig.update_layout(
        title="Crescimento do Trabalho Informal/PJ vs. Arrecadação do FGTS",
        xaxis_title="Ano",
        legend_title="Indicadores",
        height=500
    )
    fig.update_yaxes(title_text="Trabalho Informal/PJ (milhões)", secondary_y=False)
    if df_fgts is not None:
        fig.update_yaxes(title_text="Arrecadação FGTS (R$ Bi)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True, config={'responsive': True})
    
    # Análise de correlação
    if df_fgts is not None and 'Arrecadacao_Bruta_R_Bilhoes' in df_combined:
        correlation = df_combined['Trabalho Informal/PJ'].corr(
            df_combined['Arrecadacao_Bruta_R_Bilhoes']
        )
        st.markdown(f"**Correlação entre Trabalho Informal/PJ e Arrecadação FGTS:** {correlation:.2f}")
        st.markdown("""
        - Correlação negativa indica que aumento do trabalho informal/PJ tende a reduzir a arrecadação do FGTS
        - Cada 1 milhão de trabalhadores informais/PJ representa potencial perda de ~R$ 1.2 bilhões/ano em contribuições
        """)

def show_juros_financiamento(anos_selecionados):
    """Exibe análise específica de juros no financiamento imobiliário."""
    st.markdown("## Juros no Financiamento Imobiliário")
    
    st.markdown("""
    <div class="analysis-section">
        <b>Análise:</b> As taxas de juros são determinantes para a saúde do setor imobiliário. 
        Juros elevados encarecem os financiamentos, reduzindo a demanda por imóveis e impactando 
        toda a cadeia produtiva da construção civil.
    </div>
    """, unsafe_allow_html=True)
    
    # Buscar dados atualizados
    with st.spinner("Carregando dados de juros do Banco Central..."):
        df_juros = fetch_bcb_data()
    
    if df_juros is not None:
        # Filtrar por período selecionado
        start_date = f"{anos_selecionados[0]}-01-01"
        end_date = f"{anos_selecionados[1]}-12-31"
        df_juros_filtrado = df_juros.loc[start_date:end_date]
        
        if not df_juros_filtrado.empty:
            # Média móvel para suavizar
            df_juros_filtrado['Media_Movel'] = df_juros_filtrado['valor'].rolling(window=6).mean()
            
            # Criar visualização
            fig = go.Figure()
            
            # Linha principal
            fig.add_trace(go.Scatter(
                x=df_juros_filtrado.index,
                y=df_juros_filtrado['valor'],
                name='Juros (% a.m.)',
                line=dict(color='#888', width=1),
                hoverinfo='y'
            ))
            
            # Linha suavizada
            fig.add_trace(go.Scatter(
                x=df_juros_filtrado.index,
                y=df_juros_filtrado['Media_Movel'],
                name='Tendência (6 meses)',
                line=dict(color='#E377C2', width=3),
                hoverinfo='y'
            ))
            
            # Destaque para valores acima da média
            media_historica = df_juros_filtrado['valor'].mean()
            df_high = df_juros_filtrado[df_juros_filtrado['valor'] > media_historica]
            fig.add_trace(go.Scatter(
                x=df_high.index,
                y=df_high['valor'],
                mode='markers',
                name='Juros Elevados',
                marker=dict(color='red', size=8),
                hoverinfo='y'
            ))
            
            fig.update_layout(
                title='Evolução da Taxa de Juros para Financiamento Imobiliário',
                yaxis_title='Taxa Mensal (%)',
                hovermode='x unified',
                height=500
            )
            st.plotly_chart(fig, use_container_width=True, config={'responsive': True})
            
            # Análise estatística
            ultima_taxa = df_juros_filtrado['valor'].iloc[-1]
            media_periodo = df_juros_filtrado['valor'].mean()
            max_historico = df_juros_filtrado['valor'].max()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Taxa Atual", f"{ultima_taxa:.2f}%")
            col2.metric("Média no Período", f"{media_periodo:.2f}%")
            col3.metric("Máximo Histórico", f"{max_historico:.2f}%")
            
            st.markdown(f"### Impacto no Mercado:")
            st.markdown(f"""
            - **Custo de Financiamento:** Uma taxa de {ultima_taxa:.2f}% a.m. significa que um financiamento de R$ 500 mil terá:
              - Prestação inicial: R$ {500000 * ultima_taxa/100:.0f}/mês
              - Custo total: R$ {500000 * (1 + ultima_taxa/100)**360:.0f} em 30 anos
              
            - **Sensibilidade da Demanda:** Estudos mostdem que cada 1% de aumento na taxa reduz em 5-7% a demanda por imóveis novos
            """)
        else:
            st.warning("Não há dados de juros para o período selecionado.")
    else:
        st.error("Não foi possível carregar os dados de juros do Banco Central.")

def show_analise_informalidade(df_construcao_filtered, df_imobiliarias_filtered, setores_selecionados):
    """Exibe a análise de informalidade."""
    st.markdown("## Análise Detalhada da Taxa de Informalidade")
    
    fig = go.Figure()
    if "Construção Civil" in setores_selecionados:
        fig.add_trace(go.Scatter(
            x=df_construcao_filtered['Ano'], 
            y=df_construcao_filtered['Taxa de Informalidade Setorial (%)'], 
            mode='lines+markers', 
            name='Construção Civil', 
            line=dict(color='#ff7f0e', width=3), 
            marker=dict(size=8)
        ))
    
    if "Atividades Imobiliárias" in setores_selecionados:
        fig.add_trace(go.Scatter(
            x=df_imobiliarias_filtered['Ano'], 
            y=df_imobiliarias_filtered['Taxa de Informalidade Setorial (%)'], 
            mode='lines+markers', 
            name='Atividades Imobiliárias', 
            line=dict(color='#1f77b4', width=3), 
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title="Taxa de Informalidade Setorial ao Longo do Tempo", 
        xaxis_title="Ano", 
        yaxis_title="Taxa de Informalidade (%)", 
        hovermode='x unified', 
        height=500
    )
    st.plotly_chart(fig, use_container_width=True, config={'responsive': True})

def show_composicao_emprego(df_construcao_filtered, df_imobiliarias_filtered, setores_selecionados):
    """Exibe a composição do emprego."""
    st.markdown("## Composição do Emprego por Tipo de Vínculo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if "Construção Civil" in setores_selecionados:
            st.markdown("#### Construção Civil")
            fig1 = px.bar(
                df_construcao_filtered, 
                x='Ano', 
                y=['Empregados com Carteira (PNAD, milhões)', 'Empregados sem Carteira (PNAD, milhões)', 'Conta Própria (PNAD, milhões)'], 
                title="Composição do Emprego - Construção", 
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig1, use_container_width=True, config={'responsive': True})
    
    with col2:
        if "Atividades Imobiliárias" in setores_selecionados:
            st.markdown("#### Atividades Imobiliárias")
            fig2 = px.bar(
                df_imobiliarias_filtered, 
                x='Ano', 
                y=['Empregados com Carteira (PNAD, milhões)', 'Empregados sem Carteira (PNAD, milhões)', 'Conta Própria (PNAD, milhões)'], 
                title="Composição do Emprego - Imobiliário", 
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig2, use_container_width=True, config={'responsive': True})

def show_analise_economica(df_construcao_filtered, df_fgts, anos_selecionados):
    """Exibe a análise econômica (FGTS e Juros)."""
    st.markdown("## Análise Econômica: FGTS e Juros Imobiliários")
    
    # Análise do FGTS
    st.markdown("### Impacto da Informalidade no FGTS")
    st.markdown('<div class="analysis-section">O Fundo de Garantia (FGTS) é crucial para o financiamento habitacional, sendo nutrido por contribuições de empregos formais. O aumento do trabalho informal e por conta própria (PJ) reduz essa base de arrecadação, o que pode comprometer futuros investimentos em habitação e infraestrutura.</div>', unsafe_allow_html=True)
    
    if df_fgts is not None:
        df_merged = pd.merge(df_construcao_filtered, df_fgts, on="Ano", how="inner")
        if not df_merged.empty:
            fig_fgts = make_subplots(specs=[[{"secondary_y": True}]])
            fig_fgts.add_trace(go.Bar(x=df_merged['Ano'], y=df_merged['Conta Própria (PNAD, milhões)'], name='Conta Própria (Construção)', marker_color='orange'), secondary_y=False)
            fig_fgts.add_trace(go.Scatter(x=df_merged['Ano'], y=df_merged['Arrecadacao_Bruta_R_Bilhoes'], name='Arrecadação FGTS', marker_color='green', mode='lines+markers'), secondary_y=True)
            fig_fgts.update_layout(title_text='Trabalho por Conta Própria vs. Arrecadação do FGTS', height=500)
            fig_fgts.update_yaxes(title_text="Conta Própria (milhões)", secondary_y=False)
            fig_fgts.update_yaxes(title_text="Arrecadação FGTS (R$ Bi)", secondary_y=True)
            st.plotly_chart(fig_fgts, use_container_width=True, config={'responsive': True})
        else:
            st.warning("Não há dados de FGTS para o período selecionado.")
    else:
        st.warning("Arquivo 'fgts_arrecadacao.csv' não encontrado. Análise do FGTS indisponível.")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Análise dos Juros
    st.markdown("### Evolução dos Juros no Financiamento Imobiliário")
    st.markdown('<div class="analysis-section">As taxas de juros influenciam diretamente o custo e a demanda por financiamentos imobiliários. Variações na taxa SELIC e nas políticas de crédito têm impacto direto no setor. Abaixo, a evolução da taxa média mensal, segundo o Banco Central do Brasil.</div>', unsafe_allow_html=True)
    
    with st.spinner("Carregando dados de juros do Banco Central..."):
        df_juros = fetch_bcb_data()
    
    if df_juros is not None:
        df_juros_filtrado = df_juros[(df_juros.index.year >= anos_selecionados[0]) & (df_juros.index.year <= anos_selecionados[1])]
        fig_juros = px.line(
            df_juros_filtrado, 
            x=df_juros_filtrado.index, 
            y='valor', 
            title='Taxa Média Mensal de Juros - Financiamento Imobiliário (% a.m.)', 
            labels={'valor': 'Taxa (% a.m.)', 'index': 'Data'}
        )
        fig_juros.update_traces(line_color='#e377c2', line_width=2.5)
        st.plotly_chart(fig_juros, use_container_width=True, config={'responsive': True})
    else:
        st.error("Não foi possível carregar os dados de juros do Banco Central.")

def show_footer():
    """Exibe o rodapé da aplicação."""
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: grey; font-size: 0.9rem;">
        <p>Desenvolvido como uma demonstração de análise de dados com Streamlit.<br>
        Fontes: IBGE, Banco Central do Brasil, Caixa Econômica Federal.</p>
        </div>
        """, unsafe_allow_html=True
    )

def main():
    """Função principal que executa a aplicação."""
    # Limpar cache se necessário
    if hasattr(st.session_state, 'clear_cache') and st.session_state.clear_cache:
        st.cache_data.clear()
        st.session_state.clear_cache = False
    # Configuração inicial
    configure_page()
    display_header()
    initialize_session_state()
    
    # Verificar se há solicitação de atualização
    if hasattr(st.session_state, 'update_requested') and st.session_state.update_requested:
        st.session_state.update_requested = False  # Resetar o flag
        handle_data_update()  # Executar a atualização
    
    # Carregamento de dados
    df_construcao, df_imobiliarias, df_fgts, using_updated = load_data(st.session_state.data_updated)
    
    # Verificação se os dados foram carregados com sucesso
    if df_construcao is None or df_imobiliarias is None:
        st.error("Não foi possível carregar os dados. Verifique os arquivos CSV.")
        return
    
    # Interface lateral e filtros
    view_option, anos_selecionados, setores_selecionados, data_updated = create_sidebar(df_construcao, using_updated)
    
    # Status dos dados
    show_data_status(using_updated)
    
    # Filtragem dos dados
    df_construcao_filtered, df_imobiliarias_filtered = filter_data(df_construcao, df_imobiliarias, anos_selecionados)
    
    # Roteamento das visualizações ATUALIZADO
    if view_option == "Visão Geral":
        show_visao_geral(df_construcao_filtered, df_imobiliarias_filtered, setores_selecionados)
    
    elif view_option == "Análise de Informalidade":
        show_analise_informalidade(df_construcao_filtered, df_imobiliarias_filtered, setores_selecionados)
    
    elif view_option == "Composição do Emprego":
        show_composicao_emprego(df_construcao_filtered, df_imobiliarias_filtered, setores_selecionados)
    
    elif view_option == "Crescimento PJ/Informal + FGTS":
        show_pj_informal_fgts_impact(df_construcao_filtered, df_fgts, anos_selecionados)
    
    elif view_option == "Juros no Financiamento Imobiliário":
        show_juros_financiamento(anos_selecionados)
    
    # Ações da sidebar (agora usando os DataFrames filtrados)
    create_sidebar_actions(df_construcao_filtered, df_imobiliarias_filtered)
    
    # Rodapé
    show_footer()

# --- EXECUÇÃO ---
if __name__ == "__main__":
    main()