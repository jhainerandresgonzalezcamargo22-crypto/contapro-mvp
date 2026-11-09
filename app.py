import streamlit as st
from utils.database import init_db, get_session, crear_empresa_demo, Empresa
import os

st.set_page_config(
    page_title="ContaPro — Contabilidad Multi-Empresa",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e3a5f;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .stMetric {
        background: #f8fafc;
        padding: 12px 16px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    div[data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    div[data-testid="stSidebar"] .stSelectbox label {
        color: #94a3b8 !important;
    }
    .empresa-badge {
        background: #3b82f6;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar base de datos
init_db()

# Session state
if "empresa_id" not in st.session_state:
    st.session_state.empresa_id = None
if "empresa_nombre" not in st.session_state:
    st.session_state.empresa_nombre = None

session = get_session()

# Crear empresa demo si no existe
crear_empresa_demo(session)

# Sidebar
with st.sidebar:
    st.markdown("## 📊 ContaPro")
    st.caption("Contabilidad multi-empresa · Colombia")
    st.divider()

    empresas = session.query(Empresa).filter_by(activa=True).order_by(Empresa.razon_social).all()
    opciones = {f"{e.razon_social} ({e.nit})": e.id for e in empresas}

    if opciones:
        seleccion = st.selectbox(
            "Empresa activa",
            options=list(opciones.keys()),
            index=0 if st.session_state.empresa_id is None else 
                  list(opciones.values()).index(st.session_state.empresa_id) 
                  if st.session_state.empresa_id in opciones.values() else 0
        )
        st.session_state.empresa_id = opciones[seleccion]
        st.session_state.empresa_nombre = seleccion.split(" (")[0]
    else:
        st.warning("No hay empresas. Crea una en la sección Empresas.")
        st.session_state.empresa_id = None

    st.divider()
    st.markdown("### Menú")
    st.page_link("app.py", label="🏠 Inicio", icon="🏠")
    st.page_link("pages/1_Empresas.py", label="🏢 Empresas", icon="🏢")
    st.page_link("pages/2_Terceros.py", label="👥 Terceros", icon="👥")
    st.page_link("pages/3_Plan_de_Cuentas.py", label="📑 Plan de Cuentas", icon="📑")
    st.page_link("pages/4_Facturacion.py", label="🧾 Facturación", icon="🧾")
    st.page_link("pages/5_Asientos.py", label="📒 Asientos Contables", icon="📒")
    st.page_link("pages/6_Reportes.py", label="📈 Reportes", icon="📈")

    st.divider()
    st.caption("Versión MVP 1.0 · Hecho para contadores")

# Página principal
st.markdown('<p class="main-header">Panel de Control</p>', unsafe_allow_html=True)

if st.session_state.empresa_id:
    st.markdown(f'<span class="empresa-badge">{st.session_state.empresa_nombre}</span>', unsafe_allow_html=True)
    st.write("")

    from utils.database import FacturaVenta, Asiento, Tercero, CuentaContable
    from sqlalchemy import func
    from decimal import Decimal

    # Métricas rápidas
    col1, col2, col3, col4 = st.columns(4)

    total_facturas = session.query(func.count(FacturaVenta.id)).filter_by(
        empresa_id=st.session_state.empresa_id, estado="Activa"
    ).scalar() or 0

    total_ventas = session.query(func.coalesce(func.sum(FacturaVenta.total), 0)).filter_by(
        empresa_id=st.session_state.empresa_id, estado="Activa"
    ).scalar() or 0

    total_asientos = session.query(func.count(Asiento.id)).filter_by(
        empresa_id=st.session_state.empresa_id
    ).scalar() or 0

    total_terceros = session.query(func.count(Tercero.id)).filter_by(
        empresa_id=st.session_state.empresa_id, activo=True
    ).scalar() or 0

    with col1:
        st.metric("Facturas activas", f"{total_facturas}")
    with col2:
        st.metric("Total facturado", f"$ {float(total_ventas):,.0f}")
    with col3:
        st.metric("Asientos contables", f"{total_asientos}")
    with col4:
        st.metric("Terceros", f"{total_terceros}")

    st.divider()

    st.subheader("Accesos rápidos")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("➕ Nueva Factura de Venta", use_container_width=True):
            st.switch_page("pages/4_Facturacion.py")
    with c2:
        if st.button("📒 Nuevo Asiento Manual", use_container_width=True):
            st.switch_page("pages/5_Asientos.py")
    with c3:
        if st.button("📈 Ver Reportes", use_container_width=True):
            st.switch_page("pages/6_Reportes.py")

    st.divider()
    st.info("""
    **Cómo usar ContaPro (MVP)**  
    1. Selecciona o crea una **Empresa** en el menú lateral.  
    2. Carga **Terceros** (clientes / proveedores).  
    3. El **Plan de Cuentas** ya viene precargado con estructura tipo PUC Colombia.  
    4. Crea **Facturas de Venta** → automáticamente generan el asiento contable.  
    5. Consulta **Reportes** (Libro Diario, Balance de Prueba, Estado de Resultados).
    """)

else:
    st.warning("Selecciona o crea una empresa para comenzar.")
    st.page_link("pages/1_Empresas.py", label="Ir a Empresas →")

session.close()
