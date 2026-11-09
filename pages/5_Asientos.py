import streamlit as st
from utils.database import get_session, Asiento, Movimiento, CuentaContable, Tercero
from datetime import date
from decimal import Decimal
from sqlalchemy import func

st.set_page_config(page_title="Asientos — ContaPro", page_icon="📒", layout="wide")

st.markdown("## 📒 Asientos Contables")
st.caption("Consulta y crea asientos manuales")

if "empresa_id" not in st.session_state or not st.session_state.empresa_id:
    st.warning("Primero selecciona una empresa en el menú lateral.")
    st.stop()

session = get_session()
empresa_id = st.session_state.empresa_id

tab1, tab2 = st.tabs(["Libro de asientos", "Nuevo asiento manual"])

with tab1:
    asientos = session.query(Asiento).filter_by(
        empresa_id=empresa_id
    ).order_by(Asiento.fecha.desc(), Asiento.id.desc()).all()

    if not asientos:
        st.info("No hay asientos registrados todavía.")
    else:
        for a in asientos:
            with st.expander(f"{a.numero} · {a.fecha.strftime('%d/%m/%Y')} · {a.tipo} · {a.concepto[:60] if a.concepto else ''}"):
                st.write(f"**Concepto:** {a.concepto}")
                st.write(f"**Débitos:** $ {float(a.total_debito):,.2f}  |  **Créditos:** $ {float(a.total_credito):,.2f}")

                # Movimientos
                movs = []
                for m in a.movimientos:
                    movs.append({
                        "Cuenta": f"{m.cuenta.codigo} — {m.cuenta.nombre}",
                        "Detalle": m.detalle or "",
                        "Débito": f"$ {float(m.debito):,.2f}" if m.debito else "",
                        "Crédito": f"$ {float(m.credito):,.2f}" if m.credito else ""
                    })
                st.dataframe(movs, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Crear asiento manual")
    st.caption("El asiento debe cuadrar (total débitos = total créditos)")

    cuentas = session.query(CuentaContable).filter_by(
        empresa_id=empresa_id, acepta_movimiento=True, activa=True
    ).order_by(CuentaContable.codigo).all()
    cuenta_opts = {f"{c.codigo} — {c.nombre}": c.id for c in cuentas}

    if not cuenta_opts:
        st.warning("No hay cuentas que acepten movimiento.")
        st.stop()

    with st.form("form_asiento"):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=date.today())
            concepto = st.text_input("Concepto *", placeholder="Descripción del asiento")
        with col2:
            num_asientos = session.query(func.count(Asiento.id)).filter_by(empresa_id=empresa_id).scalar() or 0
            numero = st.text_input("Número", value=f"AS-{str(num_asientos + 1).zfill(5)}")

        st.markdown("#### Movimientos (máximo 6 líneas)")
        lineas = []
        for i in range(6):
            c1, c2, c3, c4 = st.columns([3, 2, 1.5, 1.5])
            with c1:
                cta = st.selectbox("Cuenta", ["—"] + list(cuenta_opts.keys()), key=f"cta_{i}")
            with c2:
                det = st.text_input("Detalle", key=f"det_{i}")
            with c3:
                deb = st.number_input("Débito", min_value=0.0, value=0.0, step=1000.0, key=f"deb_{i}")
            with c4:
                cre = st.number_input("Crédito", min_value=0.0, value=0.0, step=1000.0, key=f"cre_{i}")

            if cta != "—" and (deb > 0 or cre > 0):
                lineas.append({
                    "cuenta_id": cuenta_opts[cta],
                    "detalle": det,
                    "debito": Decimal(str(deb)),
                    "credito": Decimal(str(cre))
                })

        submitted = st.form_submit_button("Guardar asiento", type="primary")
        if submitted:
            if not concepto:
                st.error("El concepto es obligatorio.")
            elif not lineas:
                st.error("Debes agregar al menos un movimiento.")
            else:
                total_d = sum(l["debito"] for l in lineas)
                total_c = sum(l["credito"] for l in lineas)
                if total_d != total_c:
                    st.error(f"El asiento no cuadra. Débitos: $ {float(total_d):,.2f} | Créditos: $ {float(total_c):,.2f}")
                else:
                    asiento = Asiento(
                        empresa_id=empresa_id,
                        numero=numero.strip(),
                        fecha=fecha,
                        tipo="Manual",
                        concepto=concepto.strip(),
                        total_debito=total_d,
                        total_credito=total_c,
                        estado="Contabilizado"
                    )
                    session.add(asiento)
                    session.flush()

                    for l in lineas:
                        mov = Movimiento(
                            asiento_id=asiento.id,
                            cuenta_id=l["cuenta_id"],
                            debito=l["debito"],
                            credito=l["credito"],
                            detalle=l["detalle"] or None
                        )
                        session.add(mov)

                    session.commit()
                    st.success(f"Asiento **{asiento.numero}** creado correctamente.")
                    st.rerun()

session.close()
