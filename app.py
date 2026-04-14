import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Simulador: Compra vs Aluguel", layout="wide")
st.title("🏡 Simulador Imobiliário Bancário (SAC)")
st.markdown("Comparativo de Patrimônio Líquido com precisão bancária (MIP/DFI detalhados).")

# --- BARRA LATERAL: ENTRADA DE DADOS ---
st.sidebar.header("Parâmetros da Simulação")

with st.sidebar.expander("1. Imóvel e Financiamento", expanded=True):
    valor_imovel = st.number_input("Valor atual do imóvel (R$)", value=350000.0, step=10000.0)
    entrada = st.number_input("Valor da entrada (R$)", value=126833.23, step=1000.0)
    prazo = st.number_input("Prazo (meses)", value=420, step=12)
    juros_aa = st.number_input("Taxa nominal financiamento (% a.a.)", value=8.16, step=0.1)
    valorizacao_aa = st.number_input("Valorização anual imóvel (% a.a.)", value=8.0, step=0.5)

with st.sidebar.expander("2. Seguros e Tarifas (Caixa)", expanded=True):
    mip_inicial = st.number_input("MIP na 1ª parcela (R$)", value=24.04, step=1.0)
    dfi_inicial = st.number_input("DFI na 1ª parcela (R$)", value=24.85, step=1.0)
    taxa_admin = st.number_input("Taxa de Administração (R$)", value=25.00, step=1.0)

with st.sidebar.expander("3. Custos de Manutenção (Compra)", expanded=True):
    iptu_anual_inicial = st.number_input("IPTU Anual (R$)", value=1200.0, step=100.0)
    condominio_inicial = st.number_input("Condomínio Mensal (R$)", value=400.0, step=50.0)
    reajuste_despesas_aa = st.number_input("Reajuste anual das despesas (% a.a.)", value=3.0, step=0.5)

with st.sidebar.expander("4. Investimento e Aluguel", expanded=True):
    rendimento_aa = st.number_input("Rendimento investimentos (% a.a.)", value=13.0, step=0.5)
    aluguel_inicial = st.number_input("Aluguel inicial (R$)", value=1800.0, step=100.0)
    reajuste_aluguel_aa = st.number_input("Reajuste anual do aluguel (% a.a.)", value=7.0, step=0.5)

with st.sidebar.expander("5. Orçamento e Déficit", expanded=True):
    orcamento_mensal = st.number_input("Orçamento fixo mensal inicial (R$)", value=3500.0, step=100.0)
    reajuste_orcamento_aa = st.number_input("Reajuste anual do orçamento (% a.a.)", value=3.0, step=0.5)
    taxa_divida_aa = st.number_input("Taxa de dívida/Cheque Especial (% a.a.)", value=40.0, step=1.0)

with st.sidebar.expander("6. Viver de Renda", expanded=True):
    tx_renda_passiva_am = st.number_input("Taxa de renda passiva mensal (% a.m.)", value=0.5, step=0.1) / 100
    # tx_renda_passiva_am /= 100

# --- MOTOR DE CÁLCULO ---
@st.cache_data
def calcular_simulacao(valor_imovel, entrada, prazo, juros_aa, valorizacao_aa, 
                       mip_inicial, dfi_inicial, taxa_admin, 
                       rendimento_aa, aluguel_inicial, reajuste_aluguel_aa, 
                       orcamento_mensal, reajuste_orcamento_aa, taxa_divida_aa,
                       iptu_anual, condominio_mensal, reajuste_despesas):
    
    valor_financiado = valor_imovel - entrada
    taxa_mensal_fin = (juros_aa / 100) / 12
    amortizacao = valor_financiado / prazo if prazo > 0 else 0
    saldo_devedor = valor_financiado

    aliquota_mip = mip_inicial / valor_financiado if valor_financiado > 0 else 0

    taxa_invest_am = (1 + rendimento_aa / 100) ** (1 / 12) - 1
    taxa_divida_am = (1 + taxa_divida_aa / 100) ** (1 / 12) - 1
    taxa_reajuste_alug_aa = reajuste_aluguel_aa / 100
    taxa_reajuste_orc_aa = reajuste_orcamento_aa / 100
    
    inv_compra = 0.0 
    inv_aluguel = entrada 
    aluguel_atual = aluguel_inicial
    orc_atual = orcamento_mensal
    iptu_mensal = iptu_anual / 12
    cond_atual = condominio_mensal
    
    dados = []

    for mes in range(1, int(prazo) + 1):
        if mes > 1 and (mes - 1) % 12 == 0:
            aluguel_atual *= (1 + taxa_reajuste_alug_aa)
            orc_atual *= (1 + taxa_reajuste_orc_aa)
            iptu_mensal *= (1 + reajuste_despesas / 100)
            cond_atual *= (1 + reajuste_despesas / 100)

        mip_atual = saldo_devedor * aliquota_mip
        seguros_totais = dfi_inicial + taxa_admin + mip_atual
        juros_mes = saldo_devedor * taxa_mensal_fin        
        parcela_mes = amortizacao + juros_mes + seguros_totais        
        saldo_devedor = max(0, saldo_devedor - amortizacao)
        custo_manut_compra = iptu_mensal + cond_atual

        sobra_compra = orc_atual - parcela_mes - custo_manut_compra
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
            "Manutenção Compra (R$)": round(custo_manut_compra, 2),
            "Aluguel (R$)": round(aluguel_atual, 2),
            "Caixa Compra (R$)": round(inv_compra, 2),
            "Caixa Aluguel (R$)": round(inv_aluguel, 2)
        })
        
    df = pd.DataFrame(dados)
    valor_final_imovel = valor_imovel * ((1 + (valorizacao_aa/100)) ** (prazo/12))
    patrimonio_compra = valor_final_imovel + inv_compra
    patrimonio_aluguel = inv_aluguel
    
    return df, patrimonio_compra, patrimonio_aluguel, valor_final_imovel, inv_compra, inv_aluguel

# --- PROCESSAMENTO ---
df_resultados, pat_compra, pat_aluguel, val_imovel, cx_compra, cx_aluguel = calcular_simulacao(
    valor_imovel, entrada, prazo, juros_aa, valorizacao_aa, 
    mip_inicial, dfi_inicial, taxa_admin, 
    rendimento_aa, aluguel_inicial, reajuste_aluguel_aa, 
    orcamento_mensal, reajuste_orcamento_aa, taxa_divida_aa,
    iptu_anual_inicial, condominio_inicial, reajuste_despesas_aa
)

# Pagamento Total
pag_total_aluguel = df_resultados['Aluguel (R$)'].sum()
pag_total_compra = entrada + df_resultados['Parcela Financiamento (R$)'].sum() + df_resultados['Manutenção Compra (R$)'].sum()

ultimo_aluguel = df_resultados['Aluguel (R$)'].iloc[-1]

# --- INTERFACE DE RESULTADOS ---

# Patrimônio
st.subheader("Balanço Patrimonial Final (Mês 420)")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Patrimônio Total: COMPRA", f"R$ {pat_compra:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    if cx_compra < 0:
        st.error(f"⚠️ Alerta: Termina com dívida de R$ {abs(cx_compra):,.2f}")

with col2:
    st.metric("Patrimônio Total: ALUGUEL", f"R$ {pat_aluguel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    if cx_aluguel < 0:
        st.error(f"⚠️ Alerta: Termina com dívida de R$ {abs(cx_aluguel):,.2f}")

with col3:
    diff = pat_compra - pat_aluguel
    if diff > 0:
        porcent = (abs(diff)/pat_aluguel) * 100
        st.success(f"✅ COMPRAR vence por R$ {abs(diff):,.2f} (+{porcent:,.2f}%)".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        porcent = (abs(diff)/pat_compra) * 100
        st.info(f"✅ ALUGAR vence por R$ {abs(diff):,.2f} (+{porcent:,.2f}%)".replace(",", "X").replace(".", ",").replace("X", "."))

if cx_compra < 0 or cx_aluguel < 0:
    st.warning("Aviso: O orçamento configurado foi insuficiente para cobrir as despesas básicas em alguns períodos, gerando juros de dívida corrosivos. Ajuste o 'Orçamento inicial' na barra lateral.")

# Pagamento Total
st.subheader("Total de Pagamento Realizado (Mês 420)")
col4, col5, col6 = st.columns(3)

with col4:
    st.metric("Pagamento Total: COMPRA", f"R$ {pag_total_compra:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with col5:
    st.metric("Pagamento Total: ALUGUEL", f"R$ {pag_total_aluguel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with col6:
    diff = pag_total_aluguel - pag_total_compra
    if diff > 0:
        porcent = (abs(diff)/pag_total_aluguel) * 100
        st.success(f"✅ COMPRAR pagou R$ {abs(diff):,.2f} a menos (-{porcent:,.2f}%)".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        porcent = (abs(diff)/pag_total_compra) * 100
        st.info(f"✅ ALUGAR pagou R$ {abs(diff):,.2f} a menos (-{porcent:,.2f}%)".replace(",", "X").replace(".", ",").replace("X", "."))

# Rendimento Mensal Final
st.subheader("Rendimento Mensal Final (Mês 420)")
col7, col8, col9 = st.columns(3)

with col7:
    rendimento_compra = (pat_compra - val_imovel) * tx_renda_passiva_am
    st.metric("Rendimento Mensal: COMPRA", f"R$ {rendimento_compra:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
with col8:
    rendimento_aluguel = pat_aluguel * tx_renda_passiva_am
    st.metric("Rendimento Mensal: ALUGUEL", f"R$ {rendimento_aluguel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with col9:
    diff = rendimento_compra - rendimento_aluguel
    if diff > 0:
        porcent = (abs(diff)/rendimento_aluguel) * 100
        st.success(f"✅ COMPRAR vence por R$ {abs(diff):,.2f} (+{porcent:,.2f}%)".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        porcent = (abs(diff)/rendimento_compra) * 100
        st.info(f"✅ ALUGAR vence por R$ {abs(diff):,.2f} (+{porcent:,.2f}%)".replace(",", "X").replace(".", ",").replace("X", "."))

# Aluguel Final 
st.subheader("Valor Final do Imóvel e Aluguel Esperado (Mês 420)")
col10, col11, col12 = st.columns(3)

with col10:
    st.metric("Valor do Imóvel:", f"R$ {val_imovel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with col11:
    st.metric("Aluguel:", f"R$ {ultimo_aluguel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with col12:
    diff = rendimento_aluguel - rendimento_compra - ultimo_aluguel
    if diff < 0:
        st.success(f"✅ ALUGAR não rende o suficiente para pagar o aluguel e cobrir o rendimento do rendimento de COMPRAR, faltando R$ {abs(diff):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        porcent = (abs(diff)/rendimento_compra) * 100
        st.info(f"✅ ALUGAR rende o suficiente para pagar o aluguel e cobrir o rendimento do rendimento de COMPRAR, sobrando R$ {abs(diff):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.divider()

# Gráfico
st.subheader("Evolução do Caixa / Investimentos Acumulados")
st.markdown("Visualização da liquidez ao longo do tempo (desconsidera o valor do imóvel físico).")
grafico_dados = df_resultados.set_index("Mês")[["Caixa Compra (R$)", "Caixa Aluguel (R$)"]]
st.line_chart(grafico_dados)

st.divider()

# Tabela e Exportação
st.subheader("Detalhamento Mês a Mês")
st.dataframe(df_resultados, use_container_width=True)

csv = df_resultados.to_csv(index=False, sep=';').encode('utf-8')
st.download_button(
    label="📥 Exportar Simulação Completa (CSV)",
    data=csv,
    file_name='simulacao_bancaria_exata.csv',
    mime='text/csv',
)
