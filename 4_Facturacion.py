import streamlit as st
from utils.database import (
    get_session, FacturaVenta, ItemFactura, Tercero, 
    Asiento, Movimiento, CuentaContable
)
from datetime import date
from decimal import Decimal
from sqlalchemy import func

st.set_page_config(page_title="Facturación — ContaPro", page_icon="🧾", layout="wide")

st.markdown("## 🧾 Facturación de Ventas")
st.caption("Cada factura genera automáticamente el asiento contable")

if "empresa_id" not in st.session_state or not st.session_state.empresa_id:
    st.warning("Primero selecciona una empresa en el menú lateral.")
    st.stop()

session = get_session()
empresa_id = st.session_state.empresa_id

tab1, tab2 = st.tabs(["Lista de facturas", "Nueva factura"])

with tab1:
    facturas = session.query(FacturaVenta).filter_by(
        empresa_id=empresa_id
    ).order_by(FacturaVenta.fecha.desc(), FacturaVenta.id.desc()).all()

    if not facturas:
        st.info("Aún no hay facturas registradas.")
    else:
        for f in facturas:
            color = "🟢" if f.estado == "Activa" else "🔴"
            with st.expander(f"{color} {f.numero} · {f.fecha.strftime('%d/%m/%Y')} · {f.tercero.razon_social} · $ {float(f.total):,.0f}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Cliente:** {f.tercero.razon_social}")
                    st.write(f"**Forma de pago:** {f.forma_pago}")
                with col2:
                    st.write(f"**Subtotal:** $ {float(f.subtotal):,.2f}")
                    st.write(f"**IVA:** $ {float(f.valor_iva):,.2f}")
                with col3:
                    st.write(f"**Total:** $ {float(f.total):,.2f}")
                    st.write(f"**Estado:** {f.estado}")
                    if f.asiento_id:
                        st.write(f"**Asiento:** #{f.asiento.numero}")

                st.write("**Ítems:**")
                for item in f.items:
                    st.write(f"- {item.descripcion} | Cant: {float(item.cantidad)} | Unit: $ {float(item.valor_unitario):,.0f} | IVA {float(item.porcentaje_iva)}% | Subtotal: $ {float(item.subtotal):,.0f}")

with tab2:
    st.subheader("Crear factura de venta")

    # Clientes
    clientes = session.query(Tercero).filter(
        Tercero.empresa_id == empresa_id,
        Tercero.activo == True,
        Tercero.tipo.in_(["Cliente", "Ambos"])
    ).order_by(Tercero.razon_social).all()

    if not clientes:
        st.warning("No hay clientes registrados. Ve a **Terceros** y crea al menos uno.")
        st.stop()

    cliente_opts = {f"{c.razon_social} ({c.nit})": c.id for c in clientes}

    with st.form("form_factura"):
        col1, col2, col3 = st.columns(3)
        with col1:
            cliente_sel = st.selectbox("Cliente *", list(cliente_opts.keys()))
            fecha = st.date_input("Fecha", value=date.today())
        with col2:
            forma_pago = st.selectbox("Forma de pago", ["Contado", "Crédito 30 días", "Crédito 60 días"])
            # Número automático simple
            ultimo = session.query(func.count(FacturaVenta.id)).filter_by(empresa_id=empresa_id).scalar() or 0
            numero = st.text_input("Número de factura", value=f"FV-{str(ultimo + 1).zfill(5)}")
        with col3:
            observaciones = st.text_area("Observaciones", height=68)

        st.markdown("#### Ítems de la factura")
        st.caption("Puedes agregar hasta 5 ítems en esta versión MVP")

        items_data = []
        for i in range(5):
            with st.expander(f"Ítem {i+1}", expanded=(i == 0)):
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                with c1:
                    desc = st.text_input("Descripción", key=f"desc_{i}", placeholder="Producto o servicio")
                with c2:
                    cant = st.number_input("Cantidad", min_value=0.0, value=1.0, step=1.0, key=f"cant_{i}")
                with c3:
                    vunit = st.number_input("Valor unitario", min_value=0.0, value=0.0, step=1000.0, key=f"vu_{i}")
                with c4:
                    piva = st.selectbox("% IVA", [19.0, 5.0, 0.0], key=f"iva_{i}")

                if desc and cant > 0 and vunit > 0:
                    subtotal_item = Decimal(str(cant)) * Decimal(str(vunit))
                    iva_item = subtotal_item * Decimal(str(piva)) / Decimal("100")
                    items_data.append({
                        "descripcion": desc,
                        "cantidad": Decimal(str(cant)),
                        "valor_unitario": Decimal(str(vunit)),
                        "porcentaje_iva": Decimal(str(piva)),
                        "valor_iva": iva_item,
                        "subtotal": subtotal_item
                    })

        submitted = st.form_submit_button("Crear factura y generar asiento", type="primary")

        if submitted:
            if not items_data:
                st.error("Debes agregar al menos un ítem válido.")
            else:
                subtotal = sum(i["subtotal"] for i in items_data)
                valor_iva = sum(i["valor_iva"] for i in items_data)
                total = subtotal + valor_iva

                # Crear factura
                factura = FacturaVenta(
                    empresa_id=empresa_id,
                    numero=numero.strip(),
                    fecha=fecha,
                    tercero_id=cliente_opts[cliente_sel],
                    subtotal=subtotal,
                    valor_iva=valor_iva,
                    total=total,
                    forma_pago=forma_pago,
                    observaciones=observaciones.strip() or None,
                    estado="Activa"
                )
                session.add(factura)
                session.flush()

                for it in items_data:
                    item = ItemFactura(
                        factura_id=factura.id,
                        descripcion=it["descripcion"],
                        cantidad=it["cantidad"],
                        valor_unitario=it["valor_unitario"],
                        porcentaje_iva=it["porcentaje_iva"],
                        valor_iva=it["valor_iva"],
                        subtotal=it["subtotal"]
                    )
                    session.add(item)

                # === GENERAR ASIENTO AUTOMÁTICO ===
                # Buscar cuentas necesarias
                cuenta_clientes = session.query(CuentaContable).filter_by(
                    empresa_id=empresa_id, codigo="1305"
                ).first()
                cuenta_ingresos = session.query(CuentaContable).filter_by(
                    empresa_id=empresa_id, codigo="4135"
                ).first()
                cuenta_iva = session.query(CuentaContable).filter_by(
                    empresa_id=empresa_id, codigo="2408"
                ).first()
                cuenta_caja = session.query(CuentaContable).filter_by(
                    empresa_id=empresa_id, codigo="1105"
                ).first()

                if not all([cuenta_clientes, cuenta_ingresos, cuenta_iva]):
                    st.error("Faltan cuentas contables básicas (1305, 4135, 2408). Revisa el Plan de Cuentas.")
                    session.rollback()
                else:
                    # Número de asiento
                    num_asientos = session.query(func.count(Asiento.id)).filter_by(empresa_id=empresa_id).scalar() or 0
                    asiento = Asiento(
                        empresa_id=empresa_id,
                        numero=f"AS-{str(num_asientos + 1).zfill(5)}",
                        fecha=fecha,
                        tipo="Factura Venta",
                        concepto=f"Factura de venta {numero} — {cliente_sel.split(' (')[0]}",
                        total_debito=total,
                        total_credito=total,
                        estado="Contabilizado"
                    )
                    session.add(asiento)
                    session.flush()

                    # Movimientos
                    # Débito: Clientes (o Caja si contado)
                    if "Contado" in forma_pago and cuenta_caja:
                        mov_debito = Movimiento(
                            asiento_id=asiento.id,
                            cuenta_id=cuenta_caja.id,
                            tercero_id=cliente_opts[cliente_sel],
                            debito=total,
                            credito=0,
                            detalle=f"Pago factura {numero}"
                        )
                    else:
                        mov_debito = Movimiento(
                            asiento_id=asiento.id,
                            cuenta_id=cuenta_clientes.id,
                            tercero_id=cliente_opts[cliente_sel],
                            debito=total,
                            credito=0,
                            detalle=f"Factura {numero}"
                        )
                    session.add(mov_debito)

                    # Crédito: Ingresos
                    mov_ingreso = Movimiento(
                        asiento_id=asiento.id,
                        cuenta_id=cuenta_ingresos.id,
                        debito=0,
                        credito=subtotal,
                        detalle=f"Venta factura {numero}"
                    )
                    session.add(mov_ingreso)

                    # Crédito: IVA por pagar (si hay)
                    if valor_iva > 0 and cuenta_iva:
                        mov_iva = Movimiento(
                            asiento_id=asiento.id,
                            cuenta_id=cuenta_iva.id,
                            debito=0,
                            credito=valor_iva,
                            detalle=f"IVA factura {numero}"
                        )
                        session.add(mov_iva)

                    factura.asiento_id = asiento.id
                    session.commit()

                    st.success(f"✅ Factura **{numero}** creada correctamente.")
                    st.success(f"📒 Asiento **{asiento.numero}** generado automáticamente.")
                    st.balloons()
                    st.rerun()

session.close()
