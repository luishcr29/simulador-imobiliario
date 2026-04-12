import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Simulador de Decisão Imobiliária", layout="wide")
st.title("🏡 Simulador de Patrimônio: Compra vs. Aluguel")
st.markdown("Analise o custo de oportunidade e o acúmulo de patrimônio líquido ao longo do tempo.")

# --- BARRA LATERAL: ENTRADA DE DADOS ---
st.sidebar.header("Parâmetros da Simulação")

with st.sidebar.expander("1. Imóvel e Financiamento (SAC)", expanded=True):
    valor_imovel = st.number_input("Valor atual do imóvel (R$)", value=300000.0, step=10000.0)
    entrada = st.number_input("Valor da entrada (R$)", value=87793.35, step=1000.0)
    prazo = st.number_input("Prazo (meses)", value=420, step=12)
    juros_aa = st.number_input("Taxa financiamento (% a.a.)", value=8.16, step=0.1)
    seguro_taxa_inicial = st.number_input("Seguro/Taxa 1ª parcela (R$)", value=91.0, step=5.0)
    valorizacao_aa = st.number_input("Valorização do imóvel (% a.a.)", value=4.5, step=0.5)

with st.sidebar.expander("2. Investimento e Aluguel", expanded=True):
    rendimento_aa = st.number_input("Rendimento investimentos (% a.a.)", value=11.5, step=0.5)
    aluguel_inicial = st.number_input("Aluguel inicial (R$)", value=1500.0, step=100.0)
    reajuste_aluguel_aa = st.number_input("Reajuste do aluguel (% a.a.)", value=5.5, step=0.5)

with st.sidebar.expander("3. Orçamento e Comportamento", expanded=True):
    orcamento_mensal = st.number_input("Orçamento mensal inicial (R$)", value=2500.0, step=100.0)
    reajuste_orcamento_aa = st.number_input("Reajuste anual do orçamento (% a.a.)", value=3.0, step=0.5)
    taxa_divida_aa = st.number_input("Taxa de dívida/Cheque Especial (% a.a.)", value=40.0, step=1.0)

# --- MOTOR DE CÁLCULO ---
def calcular_simulacao():
    valor_financiado = valor_imovel - entrada
    taxa_mensal_fin = (juros_aa / 100) / 12
    amortizacao = valor_financiado / prazo if prazo > 0 else 0
    saldo_devedor = valor_financiado

    taxa_admin_fixa = 25.0
    seguro_puro_inicial = max(0, seguro_taxa_inicial - taxa_admin_fixa)

    taxa_invest_am = (1 + rendimento_aa / 100) ** (1 / 12) - 1
    taxa_divida_am = (1 + taxa_divida_aa / 100) ** (1 / 12) - 1
    taxa_reaj_alug_aa = reajuste_aluguel_aa / 100
    taxa_reaj_orc_aa = reajuste_orcamento_aa / 100
    
    inv_compra = 0.0 
    inv_aluguel = entrada 
    aluguel_atual = aluguel_inicial
    orc_atual = orcamento_mensal
    
    dados = []

    for mes in range(1, int(prazo) + 1):
        if mes > 1 and (mes - 1) % 12 == 0:
            aluguel_atual *= (1 + taxa_reaj_alug_aa)
            orc_atual *= (1 + taxa_reaj_orc_aa)

        proporcao_saldo = saldo_devedor / valor_financiado if valor_financiado > 0 else 0
        seguro_mes = taxa_admin_fixa + (seguro_puro_inicial * proporcao_saldo)

        juros_mes = saldo_devedor * taxa_mensal_fin
        parcela_mes = amortizacao + juros_mes + seguro_mes
        
        saldo_devedor = max(0, saldo_devedor - amortizacao)

        sobra_compra = orc_atual - parcela_mes
        if inv_compra < 0:
            inv_compra = inv_compra * (1 + taxa_divida_am) + sobra_compra
        else:
            inv_compra = inv_compra * (1 + taxa_invest_am) + sobra_compra
        
        sobra_aluguel = orc_atual - aluguel_atual
        if inv_aluguel < 0:
            inv_aluguel = inv_aluguel * (1 + taxa_divida_am) + sobra_aluguel
        else:
            inv_aluguel = inv_aluguel * (1 + taxa_invest_am) + sobra_aluguel

        dados.append({
            "Mês": mes,
            "Orçamento (R$)": round(orc_atual, 2),
            "Parcela Financiamento (R$)": round(parcela_mes, 2),
            "Aluguel (R$)": round(aluguel_atual, 2),
            "Caixa Cenário Compra (R$)": round(inv_compra, 2),
            "Caixa Cenário Aluguel (R$)": round(inv_aluguel, 2)
        })
        
    df = pd.DataFrame(dados)
    
    # Patrimônio líquido final
    valor_final_imovel = valor_imovel * ((1 + (valorizacao_aa/100)) ** (prazo/12))
    patrimonio_compra = valor_final_imovel + inv_compra
    patrimonio_aluguel = inv_aluguel
    
    return df, patrimonio_compra, patrimonio_aluguel, valor_final_imovel, inv_compra, inv_aluguel

# --- PROCESSAMENTO E UI ---
df_resultados, pat_compra, pat_aluguel, val_imovel, cx_compra, cx_aluguel = calcular_simulacao()

# KPIs (Métricas Principais)
st.subheader("Balanço Patrimonial ao Final do Prazo")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Patrimônio Total: COMPRA", value=f"R$ {pat_compra:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    if cx_compra < 0:
        st.error(f"⚠️ Termina com dívida de R$ {abs(cx_compra):,.2f}")

with col2:
    st.metric(label="Patrimônio Total: ALUGUEL", value=f"R$ {pat_aluguel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    if cx_aluguel < 0:
        st.error(f"⚠️ Termina com dívida de R$ {abs(cx_aluguel):,.2f}")

with col3:
    diff = pat_compra - pat_aluguel
    if diff > 0:
        st.success(f"🏆 COMPRAR vence por R$ {abs(diff):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.info(f"🏆 ALUGAR vence por R$ {abs(diff):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.divider()

# Gráfico de Evolução
st.subheader("Evolução do Caixa/Investimentos (Liquidez)")
st.markdown("Mostra o dinheiro disponível na conta ao longo dos meses (desconsidera o valor do imóvel de tijolo). Valores abaixo de zero indicam dívida no cheque especial.")
grafico_dados = df_resultados.set_index("Mês")[["Caixa Cenário Compra (R$)", "Caixa Cenário Aluguel (R$)"]]
st.line_chart(grafico_dados)

st.divider()

# Tabela e Exportação
st.subheader("Detalhamento Mês a Mês")
st.dataframe(df_resultados, use_container_width=True)

csv = df_resultados.to_csv(index=False, sep=';').encode('utf-8')
st.download_button(
    label="📥 Baixar planillha completa (CSV)",
    data=csv,
    file_name='simulacao_compra_vs_aluguel.csv',
    mime='text/csv',
)
