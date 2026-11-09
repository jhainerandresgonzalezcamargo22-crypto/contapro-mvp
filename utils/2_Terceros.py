import streamlit as st
from utils.database import get_session, Tercero, Empresa

st.set_page_config(page_title="Terceros — ContaPro", page_icon="👥", layout="wide")

st.markdown("## 👥 Terceros (Clientes y Proveedores)")

if "empresa_id" not in st.session_state or not st.session_state.empresa_id:
    st.warning("Primero selecciona una empresa en el menú lateral.")
    st.stop()

session = get_session()
empresa_id = st.session_state.empresa_id

tab1, tab2 = st.tabs(["Lista de terceros", "Nuevo tercero"])

with tab1:
    filtro = st.selectbox("Filtrar por tipo", ["Todos", "Cliente", "Proveedor", "Ambos", "Empleado"])
    query = session.query(Tercero).filter_by(empresa_id=empresa_id, activo=True)
    if filtro != "Todos":
        query = query.filter_by(tipo=filtro)
    terceros = query.order_by(Tercero.razon_social).all()

    if not terceros:
        st.info("No hay terceros registrados para esta empresa.")
    else:
        for t in terceros:
            with st.expander(f"{t.tipo} · {t.razon_social} — NIT {t.nit}-{t.dv or ''}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Nombre comercial:** {t.nombre_comercial or '—'}")
                    st.write(f"**Dirección:** {t.direccion or '—'}")
                    st.write(f"**Ciudad:** {t.ciudad or '—'}")
                with col2:
                    st.write(f"**Teléfono:** {t.telefono or '—'}")
                    st.write(f"**Email:** {t.email or '—'}")
                    st.write(f"**Régimen:** {t.regimen}")
                    st.write(f"**IVA responsable:** {'Sí' if t.iva_responsable else 'No'}")

with tab2:
    st.subheader("Registrar nuevo tercero")
    with st.form("form_tercero"):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo *", ["Cliente", "Proveedor", "Ambos", "Empleado"])
            nit = st.text_input("NIT / Cédula *")
            dv = st.text_input("DV", max_chars=1)
            razon = st.text_input("Razón social / Nombre *")
            comercial = st.text_input("Nombre comercial")
        with col2:
            direccion = st.text_input("Dirección")
            ciudad = st.text_input("Ciudad")
            telefono = st.text_input("Teléfono")
            email = st.text_input("Email")
            regimen = st.selectbox("Régimen", ["Común", "Simple", "Especial", "No responsable"])
            iva_resp = st.checkbox("Responsable de IVA", value=True)

        submitted = st.form_submit_button("Guardar tercero", type="primary")
        if submitted:
            if not nit or not razon:
                st.error("NIT y Razón social son obligatorios.")
            else:
                t = Tercero(
                    empresa_id=empresa_id,
                    tipo=tipo,
                    nit=nit.strip(),
                    dv=dv.strip() if dv else None,
                    razon_social=razon.strip(),
                    nombre_comercial=comercial.strip() or None,
                    direccion=direccion.strip() or None,
                    ciudad=ciudad.strip() or None,
                    telefono=telefono.strip() or None,
                    email=email.strip() or None,
                    regimen=regimen,
                    iva_responsable=iva_resp
                )
                session.add(t)
                session.commit()
                st.success(f"Tercero **{t.razon_social}** creado correctamente.")
                st.rerun()

session.close()
