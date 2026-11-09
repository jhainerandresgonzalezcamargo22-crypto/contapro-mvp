import streamlit as st
from utils.database import get_session, CuentaContable

st.set_page_config(page_title="Plan de Cuentas — ContaPro", page_icon="📑", layout="wide")

st.markdown("## 📑 Plan de Cuentas")
st.caption("Estructura tipo PUC Colombia (personalizable por empresa)")

if "empresa_id" not in st.session_state or not st.session_state.empresa_id:
    st.warning("Primero selecciona una empresa en el menú lateral.")
    st.stop()

session = get_session()
empresa_id = st.session_state.empresa_id

cuentas = session.query(CuentaContable).filter_by(
    empresa_id=empresa_id, activa=True
).order_by(CuentaContable.codigo).all()

if not cuentas:
    st.warning("Esta empresa aún no tiene plan de cuentas cargado.")
else:
    # Filtros
    col1, col2 = st.columns([2, 1])
    with col1:
        buscar = st.text_input("Buscar por código o nombre", placeholder="Ej: 1105 o Caja")
    with col2:
        filtro_tipo = st.selectbox("Tipo", ["Todos", "Activo", "Pasivo", "Patrimonio", "Ingreso", "Gasto", "Costo"])

    filtradas = cuentas
    if buscar:
        buscar = buscar.lower()
        filtradas = [c for c in filtradas if buscar in c.codigo.lower() or buscar in c.nombre.lower()]
    if filtro_tipo != "Todos":
        filtradas = [c for c in filtradas if c.tipo == filtro_tipo]

    st.write(f"**{len(filtradas)}** cuentas mostradas")

    # Tabla
    data = []
    for c in filtradas:
        data.append({
            "Código": c.codigo,
            "Nombre": c.nombre,
            "Tipo": c.tipo,
            "Naturaleza": c.naturaleza,
            "Nivel": c.nivel,
            "Acepta movimiento": "Sí" if c.acepta_movimiento else "No"
        })
    st.dataframe(data, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Agregar cuenta nueva")
with st.form("nueva_cuenta"):
    col1, col2, col3 = st.columns(3)
    with col1:
        codigo = st.text_input("Código *", placeholder="110505")
        nombre = st.text_input("Nombre *")
    with col2:
        tipo = st.selectbox("Tipo", ["Activo", "Pasivo", "Patrimonio", "Ingreso", "Gasto", "Costo"])
        naturaleza = st.selectbox("Naturaleza", ["Debito", "Credito"])
    with col3:
        nivel = st.number_input("Nivel", min_value=1, max_value=6, value=4)
        acepta = st.checkbox("Acepta movimiento", value=True)

    if st.form_submit_button("Crear cuenta", type="primary"):
        if not codigo or not nombre:
            st.error("Código y nombre son obligatorios.")
        else:
            existe = session.query(CuentaContable).filter_by(empresa_id=empresa_id, codigo=codigo.strip()).first()
            if existe:
                st.error("Ya existe una cuenta con ese código.")
            else:
                c = CuentaContable(
                    empresa_id=empresa_id,
                    codigo=codigo.strip(),
                    nombre=nombre.strip().upper(),
                    tipo=tipo,
                    naturaleza=naturaleza,
                    nivel=nivel,
                    acepta_movimiento=acepta
                )
                session.add(c)
                session.commit()
                st.success(f"Cuenta {c.codigo} — {c.nombre} creada.")
                st.rerun()

session.close()
