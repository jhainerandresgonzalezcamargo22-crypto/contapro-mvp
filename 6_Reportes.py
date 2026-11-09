import streamlit as st
from utils.database import get_session, Asiento, Movimiento, CuentaContable, FacturaVenta
from sqlalchemy import func
from decimal import Decimal
from collections import defaultdict
from datetime import date

st.set_page_config(page_title="Reportes — ContaPro", page_icon="📈", layout="wide")

st.markdown("## 📈 Reportes Contables")

if "empresa_id" not in st.session_state or not st.session_state.empresa_id:
    st.warning("Primero selecciona una empresa en el menú lateral.")
    st.stop()

session = get_session()
empresa_id = st.session_state.empresa_id

reporte = st.selectbox(
    "Selecciona el reporte",
    ["Balance de Prueba", "Estado de Resultados", "Libro Diario", "Resumen de Ventas"]
)

st.divider()

if reporte == "Balance de Prueba":
    st.subheader("Balance de Prueba")
    st.caption("Saldos de todas las cuentas con movimiento")

    # Obtener todos los movimientos
    movimientos = session.query(Movimiento).join(Asiento).filter(
        Asiento.empresa_id == empresa_id
    ).all()

    saldos = defaultdict(lambda: {"debito": Decimal("0"), "credito": Decimal("0"), "cuenta": None})

    for m in movimientos:
        key = m.cuenta_id
        saldos[key]["debito"] += m.debito or Decimal("0")
        saldos[key]["credito"] += m.credito or Decimal("0")
        saldos[key]["cuenta"] = m.cuenta

    data = []
    total_d = Decimal("0")
    total_c = Decimal("0")

    for cuenta_id, info in sorted(saldos.items(), key=lambda x: x[1]["cuenta"].codigo if x[1]["cuenta"] else ""):
        c = info["cuenta"]
        if not c:
            continue
        debito = info["debito"]
        credito = info["credito"]
        saldo = debito - credito

        # Según naturaleza
        if c.naturaleza == "Debito":
            saldo_final = saldo
        else:
            saldo_final = -saldo

        data.append({
            "Código": c.codigo,
            "Cuenta": c.nombre,
            "Tipo": c.tipo,
            "Débitos": f"$ {float(debito):,.2f}",
            "Créditos": f"$ {float(credito):,.2f}",
            "Saldo": f"$ {float(abs(saldo_final)):,.2f} {'D' if saldo_final >= 0 else 'C'}"
        })
        total_d += debito
        total_c += credito

    if data:
        st.dataframe(data, use_container_width=True, hide_index=True)
        st.write(f"**Totales → Débitos: $ {float(total_d):,.2f}  |  Créditos: $ {float(total_c):,.2f}**")
        if total_d == total_c:
            st.success("✅ El Balance de Prueba cuadra.")
        else:
            st.error("⚠️ El Balance de Prueba no cuadra. Revisa los asientos.")
    else:
        st.info("No hay movimientos contables todavía.")

elif reporte == "Estado de Resultados":
    st.subheader("Estado de Resultados (Pérdidas y Ganancias)")

    movimientos = session.query(Movimiento).join(Asiento).filter(
        Asiento.empresa_id == empresa_id
    ).all()

    ingresos = Decimal("0")
    gastos = Decimal("0")
    costos = Decimal("0")

    detalle_ing = []
    detalle_gas = []
    detalle_cos = []

    for m in movimientos:
        c = m.cuenta
        if not c:
            continue
        if c.tipo == "Ingreso":
            # Créditos aumentan ingresos
            valor = (m.credito or Decimal("0")) - (m.debito or Decimal("0"))
            ingresos += valor
            if valor != 0:
                detalle_ing.append({"Cuenta": f"{c.codigo} {c.nombre}", "Valor": float(valor)})
        elif c.tipo == "Gasto":
            valor = (m.debito or Decimal("0")) - (m.credito or Decimal("0"))
            gastos += valor
            if valor != 0:
                detalle_gas.append({"Cuenta": f"{c.codigo} {c.nombre}", "Valor": float(valor)})
        elif c.tipo == "Costo":
            valor = (m.debito or Decimal("0")) - (m.credito or Decimal("0"))
            costos += valor
            if valor != 0:
                detalle_cos.append({"Cuenta": f"{c.codigo} {c.nombre}", "Valor": float(valor)})

    utilidad = ingresos - gastos - costos

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ingresos", f"$ {float(ingresos):,.0f}")
    with col2:
        st.metric("Gastos + Costos", f"$ {float(gastos + costos):,.0f}")
    with col3:
        st.metric("Utilidad / (Pérdida)", f"$ {float(utilidad):,.0f}",
                  delta_color="normal" if utilidad >= 0 else "inverse")

    if detalle_ing:
        st.markdown("#### Ingresos")
        st.dataframe(detalle_ing, use_container_width=True, hide_index=True)
    if detalle_gas:
        st.markdown("#### Gastos")
        st.dataframe(detalle_gas, use_container_width=True, hide_index=True)
    if detalle_cos:
        st.markdown("#### Costos")
        st.dataframe(detalle_cos, use_container_width=True, hide_index=True)

elif reporte == "Libro Diario":
    st.subheader("Libro Diario")

    asientos = session.query(Asiento).filter_by(
        empresa_id=empresa_id
    ).order_by(Asiento.fecha, Asiento.id).all()

    if not asientos:
        st.info("No hay asientos registrados.")
    else:
        for a in asientos:
            st.markdown(f"**{a.numero}** | {a.fecha.strftime('%d/%m/%Y')} | *{a.tipo}*")
            st.caption(a.concepto)
            movs = []
            for m in a.movimientos:
                movs.append({
                    "Cuenta": f"{m.cuenta.codigo} — {m.cuenta.nombre}",
                    "Detalle": m.detalle or "",
                    "Débito": float(m.debito) if m.debito else None,
                    "Crédito": float(m.credito) if m.credito else None
                })
            st.dataframe(movs, use_container_width=True, hide_index=True)
            st.divider()

elif reporte == "Resumen de Ventas":
    st.subheader("Resumen de Facturación")

    facturas = session.query(FacturaVenta).filter_by(
        empresa_id=empresa_id, estado="Activa"
    ).order_by(FacturaVenta.fecha.desc()).all()

    if not facturas:
        st.info("No hay facturas activas.")
    else:
        total = sum(float(f.total) for f in facturas)
        iva = sum(float(f.valor_iva) for f in facturas)
        st.metric("Total facturado", f"$ {total:,.0f}")
        st.metric("IVA generado", f"$ {iva:,.0f}")

        data = []
        for f in facturas:
            data.append({
                "Número": f.numero,
                "Fecha": f.fecha.strftime("%d/%m/%Y"),
                "Cliente": f.tercero.razon_social,
                "Subtotal": float(f.subtotal),
                "IVA": float(f.valor_iva),
                "Total": float(f.total),
                "Forma pago": f.forma_pago
            })
        st.dataframe(data, use_container_width=True, hide_index=True)

session.close()
