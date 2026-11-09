import streamlit as st
from utils.database import get_session, Empresa, seed_plan_cuentas, crear_empresa_demo
from datetime import datetime

st.set_page_config(page_title="Empresas — ContaPro", page_icon="🏢", layout="wide")

st.markdown("## 🏢 Gestión de Empresas")
st.caption("Administra las empresas que atiendes como contador")

session = get_session()

tab1, tab2 = st.tabs(["Lista de empresas", "Nueva empresa"])

with tab1:
    empresas = session.query(Empresa).order_by(Empresa.razon_social).all()
    if not empresas:
        st.info("No hay empresas registradas todavía.")
    else:
        for e in empresas:
            with st.expander(f"{'✅' if e.activa else '❌'} {e.razon_social} — NIT {e.nit}-{e.dv or ''}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Nombre comercial:** {e.nombre_comercial or '—'}")
                    st.write(f"**Dirección:** {e.direccion or '—'}")
                    st.write(f"**Ciudad:** {e.ciudad or '—'}")
                with col2:
                    st.write(f"**Teléfono:** {e.telefono or '—'}")
                    st.write(f"**Email:** {e.email or '—'}")
                    st.write(f"**Régimen:** {e.regimen}")
                    st.write(f"**Creada:** {e.created_at.strftime('%d/%m/%Y') if e.created_at else '—'}")

                c1, c2 = st.columns(2)
                with c1:
                    if e.activa:
                        if st.button("Desactivar", key=f"des_{e.id}"):
                            e.activa = False
                            session.commit()
                            st.rerun()
                    else:
                        if st.button("Activar", key=f"act_{e.id}"):
                            e.activa = True
                            session.commit()
                            st.rerun()
                with c2:
                    if st.button("Seleccionar esta empresa", key=f"sel_{e.id}", type="primary"):
                        st.session_state.empresa_id = e.id
                        st.session_state.empresa_nombre = e.razon_social
                        st.success(f"Empresa activa: {e.razon_social}")
                        st.rerun()

with tab2:
    st.subheader("Registrar nueva empresa")
    with st.form("form_empresa"):
        col1, col2 = st.columns(2)
        with col1:
            nit = st.text_input("NIT *", placeholder="900123456")
            dv = st.text_input("DV", max_chars=1, placeholder="7")
            razon = st.text_input("Razón social *", placeholder="Mi Empresa S.A.S.")
            comercial = st.text_input("Nombre comercial")
        with col2:
            direccion = st.text_input("Dirección")
            ciudad = st.text_input("Ciudad", placeholder="Bogotá")
            telefono = st.text_input("Teléfono")
            email = st.text_input("Email")
            regimen = st.selectbox("Régimen", ["Común", "Simple", "Especial", "No responsable"])

        submitted = st.form_submit_button("Crear empresa", type="primary")
        if submitted:
            if not nit or not razon:
                st.error("NIT y Razón social son obligatorios.")
            else:
                existe = session.query(Empresa).filter_by(nit=nit.strip()).first()
                if existe:
                    st.error("Ya existe una empresa con ese NIT.")
                else:
                    emp = Empresa(
                        nit=nit.strip(),
                        dv=dv.strip() if dv else None,
                        razon_social=razon.strip(),
                        nombre_comercial=comercial.strip() or None,
                        direccion=direccion.strip() or None,
                        ciudad=ciudad.strip() or None,
                        telefono=telefono.strip() or None,
                        email=email.strip() or None,
                        regimen=regimen
                    )
                    session.add(emp)
                    session.commit()
                    session.refresh(emp)
                    seed_plan_cuentas(session, emp.id)
                    st.success(f"Empresa **{emp.razon_social}** creada correctamente. Se cargó el plan de cuentas básico.")
                    st.session_state.empresa_id = emp.id
                    st.session_state.empresa_nombre = emp.razon_social
                    st.rerun()

session.close()
