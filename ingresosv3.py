import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==============================
# CONFIGURACIÓN INICIAL
# ==============================
st.set_page_config(page_title="Control Financiero", layout="wide")
DATA_PATH = "transactions.csv"

# ==============================
# FUNCIONES
# ==============================
def create_initial_data():
    ingreso_mensual = 5_000_000
    gastos_fijos = {
        "Arriendo": 550_000,
        "Servicios": 200_000,
        "Inversiones": 500_000,
        "Transporte": 200_000,
        "Gastos hormiga": 1_000_000
    }

    data = []
    for mes in range(8, 9):  # Solo agosto 2025
        fecha = f"2025-{mes:02d}-01"
        # Ingreso
        data.append([fecha, "Ingreso", "Salario", "Transferencia", ingreso_mensual, "Pago mensual"])
        # Gastos
        for categoria, monto in gastos_fijos.items():
            data.append([fecha, "Gasto", categoria, "Efectivo", monto, f"Gasto de {categoria}"])

    df = pd.DataFrame(data, columns=["date", "type", "category", "method", "amount", "description"])
    df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")
    return df

def load_data():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df
    else:
        return create_initial_data()

def save_data(df):
    df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")

# ==============================
# CARGAR DATOS
# ==============================
df = load_data()

# ==============================
# SIDEBAR - FORMULARIO NUEVO MOVIMIENTO
# ==============================
st.sidebar.header("➕ Nuevo Movimiento")

with st.sidebar.form("nuevo_movimiento"):
    date = st.date_input("Fecha")
    tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
    categoria = st.text_input("Categoría", placeholder="Ej: Comida, Transporte, Nómina")
    metodo = st.selectbox("Método de pago", ["Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Transferencia"])
    monto = st.number_input("Monto", min_value=0.0, step=100.0, format="%.2f")
    descripcion = st.text_input("Descripción", placeholder="Detalle opcional")

    submitted = st.form_submit_button("Guardar")
    if submitted:
        nuevo = pd.DataFrame([{
            "date": pd.to_datetime(date),
            "type": tipo,
            "category": categoria,
            "method": metodo,
            "amount": monto,
            "description": descripcion
        }])
        df = pd.concat([df, nuevo], ignore_index=True)
        save_data(df)
        st.success("✅ Movimiento agregado con éxito")
        st.rerun()

# ==============================
# SIDEBAR - IMPORTAR PLANTILLA
# ==============================
st.sidebar.header("📁 Importar Plantilla CSV")
uploaded_file = st.sidebar.file_uploader("Sube tu archivo CSV", type=["csv"])
if uploaded_file:
    new_data = pd.read_csv(uploaded_file)
    expected_cols = ["date","type","category","method","amount","description"]
    if all(col in new_data.columns for col in expected_cols):
        new_data["date"] = pd.to_datetime(new_data["date"], errors="coerce")
        df = pd.concat([df, new_data], ignore_index=True)
        save_data(df)
        st.success("✅ Plantilla importada correctamente")
        st.rerun()
    else:
        st.error(f"El CSV debe contener las columnas: {expected_cols}")

# ==============================
# FILTROS
# ==============================
st.sidebar.header("🔎 Filtros")
if not df.empty:
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year

    month_names = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    df["month_name"] = df["month"].map(month_names)

    year_filter = st.sidebar.multiselect("Año", ["Todos"] + sorted(df["year"].dropna().unique().tolist()), default=["Todos"])
    month_filter = st.sidebar.multiselect("Mes", ["Todos"] + sorted(df["month_name"].dropna().unique().tolist()), default=["Todos"])
    type_filter = st.sidebar.multiselect("Tipo", ["Todos"] + sorted(df["type"].dropna().unique().tolist()), default=["Todos"])
    category_filter = st.sidebar.multiselect("Categoría", ["Todos"] + sorted(df["category"].dropna().unique().tolist()), default=["Todos"])

    dff = df.copy()
    if "Todos" not in year_filter:
        dff = dff[dff["year"].isin(year_filter)]
    if "Todos" not in month_filter:
        dff = dff[dff["month_name"].isin(month_filter)]
    if "Todos" not in type_filter:
        dff = dff[dff["type"].isin(type_filter)]
    if "Todos" not in category_filter:
        dff = dff[dff["category"].isin(category_filter)]
else:
    dff = df.copy()

# ==============================
# DASHBOARD
# ==============================
st.title("📊 Control Financiero Personal")

if dff.empty:
    st.info("No hay datos registrados todavía.")
else:
    ingresos = dff[dff["type"] == "Ingreso"]["amount"].sum()
    gastos = dff[dff["type"] == "Gasto"]["amount"].sum()
    balance = ingresos - gastos
    ahorro_pct = (balance / ingresos * 100) if ingresos > 0 else 0

    # Métricas adaptadas a móvil
    cols = st.columns(2)
    with cols[0]:
        st.metric("💰 Ingresos", f"${ingresos:,.0f}")
        st.metric("📈 Balance", f"${balance:,.0f}")
    with cols[1]:
        st.metric("💸 Gastos", f"${gastos:,.0f}")
        st.metric("💾 Ahorro %", f"{ahorro_pct:.1f}%")

    # Gráfico circular
    pie = px.pie(values=[ingresos, gastos], names=["Ingresos", "Gastos"], title="Distribución Ingresos vs Gastos")
    st.plotly_chart(pie, use_container_width=True)

    # Gráfico de evolución mensual ajustado
    resumen = dff.groupby(["year", "month", "month_name", "type"])["amount"].sum().reset_index()
    resumen = resumen.sort_values(["year", "month"])
    bar = px.bar(
        resumen,
        x="month_name", y="amount", color="type",
        barmode="group", facet_col="year",
        title="Evolución mensual"
    )
    st.plotly_chart(bar, use_container_width=True)

    # ==============================
    # TABLA CON BOTÓN DE BORRAR
    # ==============================
    st.subheader("📑 Movimientos")
    dff_reset = dff.reset_index()

    st.markdown("<div style='max-height:400px; overflow-y:auto;'>", unsafe_allow_html=True)
    for _, row in dff_reset.sort_values("date", ascending=False).iterrows():
        cols = st.columns([2,2,2,2,2,3,1])
        cols[0].write(row["date"].date())
        cols[1].write(row["type"])
        cols[2].write(row["category"])
        cols[3].write(row["method"])
        cols[4].write(f"${row['amount']:,.0f}")
        cols[5].write(row["description"])
        if cols[6].button("🗑️", key=f"del_{row['index']}"):
            df = df.drop(row["index"])
            save_data(df)
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # ==============================
    # EXPORTAR
    # ==============================
    st.download_button(
        label="⬇️ Descargar Excel",
        data=dff.to_csv(index=False).encode("utf-8"),
        file_name="movimientos_filtrados.csv",
        mime="text/csv"
    )


