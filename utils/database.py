from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, date
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "contabilidad.db")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Empresa(Base):
    __tablename__ = "empresas"
    id = Column(Integer, primary_key=True)
    nit = Column(String(20), unique=True, nullable=False)
    dv = Column(String(1))
    razon_social = Column(String(200), nullable=False)
    nombre_comercial = Column(String(200))
    direccion = Column(String(300))
    ciudad = Column(String(100))
    telefono = Column(String(50))
    email = Column(String(100))
    regimen = Column(String(50), default="Común")  # Común, Simple, etc.
    activa = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    terceros = relationship("Tercero", back_populates="empresa", cascade="all, delete-orphan")
    cuentas = relationship("CuentaContable", back_populates="empresa", cascade="all, delete-orphan")
    facturas = relationship("FacturaVenta", back_populates="empresa", cascade="all, delete-orphan")
    asientos = relationship("Asiento", back_populates="empresa", cascade="all, delete-orphan")
    centros_costo = relationship("CentroCosto", back_populates="empresa", cascade="all, delete-orphan")


class Tercero(Base):
    __tablename__ = "terceros"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    tipo = Column(String(20), nullable=False)  # Cliente, Proveedor, Ambos, Empleado
    nit = Column(String(20), nullable=False)
    dv = Column(String(1))
    razon_social = Column(String(200), nullable=False)
    nombre_comercial = Column(String(200))
    direccion = Column(String(300))
    ciudad = Column(String(100))
    telefono = Column(String(50))
    email = Column(String(100))
    regimen = Column(String(50), default="Común")
    retencion_fuente = Column(Float, default=0.0)
    iva_responsable = Column(Boolean, default=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="terceros")


class CuentaContable(Base):
    __tablename__ = "cuentas_contables"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(200), nullable=False)
    tipo = Column(String(30), nullable=False)  # Activo, Pasivo, Patrimonio, Ingreso, Gasto, Costo
    naturaleza = Column(String(10), nullable=False)  # Debito, Credito
    nivel = Column(Integer, default=1)
    cuenta_padre_id = Column(Integer, ForeignKey("cuentas_contables.id"), nullable=True)
    acepta_movimiento = Column(Boolean, default=True)
    activa = Column(Boolean, default=True)

    empresa = relationship("Empresa", back_populates="cuentas")
    padre = relationship("CuentaContable", remote_side=[id])


class CentroCosto(Base):
    __tablename__ = "centros_costo"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(150), nullable=False)
    activo = Column(Boolean, default=True)

    empresa = relationship("Empresa", back_populates="centros_costo")


class FacturaVenta(Base):
    __tablename__ = "facturas_venta"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    numero = Column(String(30), nullable=False)
    fecha = Column(Date, nullable=False, default=date.today)
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=False)
    subtotal = Column(Numeric(18, 2), default=0)
    descuento = Column(Numeric(18, 2), default=0)
    base_iva = Column(Numeric(18, 2), default=0)
    valor_iva = Column(Numeric(18, 2), default=0)
    retencion = Column(Numeric(18, 2), default=0)
    total = Column(Numeric(18, 2), default=0)
    forma_pago = Column(String(50), default="Contado")  # Contado, Crédito
    observaciones = Column(Text)
    estado = Column(String(20), default="Activa")  # Activa, Anulada
    asiento_id = Column(Integer, ForeignKey("asientos.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="facturas")
    tercero = relationship("Tercero")
    items = relationship("ItemFactura", back_populates="factura", cascade="all, delete-orphan")
    asiento = relationship("Asiento", foreign_keys=[asiento_id])


class ItemFactura(Base):
    __tablename__ = "items_factura"
    id = Column(Integer, primary_key=True)
    factura_id = Column(Integer, ForeignKey("facturas_venta.id"), nullable=False)
    descripcion = Column(String(300), nullable=False)
    cantidad = Column(Numeric(12, 2), default=1)
    valor_unitario = Column(Numeric(18, 2), default=0)
    descuento = Column(Numeric(18, 2), default=0)
    porcentaje_iva = Column(Numeric(5, 2), default=19.0)
    valor_iva = Column(Numeric(18, 2), default=0)
    subtotal = Column(Numeric(18, 2), default=0)

    factura = relationship("FacturaVenta", back_populates="items")


class Asiento(Base):
    __tablename__ = "asientos"
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    numero = Column(String(30), nullable=False)
    fecha = Column(Date, nullable=False, default=date.today)
    tipo = Column(String(30), default="Manual")  # Manual, Factura Venta, Compra, Nómina, etc.
    concepto = Column(String(400))
    total_debito = Column(Numeric(18, 2), default=0)
    total_credito = Column(Numeric(18, 2), default=0)
    estado = Column(String(20), default="Contabilizado")
    created_at = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="asientos")
    movimientos = relationship("Movimiento", back_populates="asiento", cascade="all, delete-orphan")


class Movimiento(Base):
    __tablename__ = "movimientos"
    id = Column(Integer, primary_key=True)
    asiento_id = Column(Integer, ForeignKey("asientos.id"), nullable=False)
    cuenta_id = Column(Integer, ForeignKey("cuentas_contables.id"), nullable=False)
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=True)
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"), nullable=True)
    debito = Column(Numeric(18, 2), default=0)
    credito = Column(Numeric(18, 2), default=0)
    detalle = Column(String(300))

    asiento = relationship("Asiento", back_populates="movimientos")
    cuenta = relationship("CuentaContable")
    tercero = relationship("Tercero")
    centro_costo = relationship("CentroCosto")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()


def seed_plan_cuentas(session, empresa_id: int):
    """Carga un plan de cuentas básico estilo PUC Colombia"""
    cuentas_base = [
        # Activo
        ("1", "ACTIVO", "Activo", "Debito", 1, False),
        ("11", "DISPONIBLE", "Activo", "Debito", 2, False),
        ("1105", "CAJA", "Activo", "Debito", 3, True),
        ("1110", "BANCOS", "Activo", "Debito", 3, True),
        ("13", "DEUDORES", "Activo", "Debito", 2, False),
        ("1305", "CLIENTES", "Activo", "Debito", 3, True),
        ("14", "INVENTARIOS", "Activo", "Debito", 2, False),
        ("1435", "MERCANCIAS NO FABRICADAS", "Activo", "Debito", 3, True),
        ("15", "PROPIEDAD PLANTA Y EQUIPO", "Activo", "Debito", 2, False),
        ("1524", "EQUIPO DE OFICINA", "Activo", "Debito", 3, True),
        # Pasivo
        ("2", "PASIVO", "Pasivo", "Credito", 1, False),
        ("22", "PROVEEDORES", "Pasivo", "Credito", 2, False),
        ("2205", "NACIONALES", "Pasivo", "Credito", 3, True),
        ("23", "CUENTAS POR PAGAR", "Pasivo", "Credito", 2, False),
        ("2335", "COSTOS Y GASTOS POR PAGAR", "Pasivo", "Credito", 3, True),
        ("24", "IMPUESTOS GRAVAMENES Y TASAS", "Pasivo", "Credito", 2, False),
        ("2408", "IMPUESTO SOBRE LAS VENTAS POR PAGAR", "Pasivo", "Credito", 3, True),
        ("2412", "IMPUESTO DE RENTA Y COMPLEMENTARIOS", "Pasivo", "Credito", 3, True),
        ("25", "OBLIGACIONES LABORALES", "Pasivo", "Credito", 2, False),
        ("2505", "SALARIOS POR PAGAR", "Pasivo", "Credito", 3, True),
        # Patrimonio
        ("3", "PATRIMONIO", "Patrimonio", "Credito", 1, False),
        ("31", "CAPITAL SOCIAL", "Patrimonio", "Credito", 2, False),
        ("3105", "CAPITAL SUSCRITO Y PAGADO", "Patrimonio", "Credito", 3, True),
        ("36", "RESULTADOS DEL EJERCICIO", "Patrimonio", "Credito", 2, False),
        ("3605", "UTILIDAD DEL EJERCICIO", "Patrimonio", "Credito", 3, True),
        ("3610", "PERDIDA DEL EJERCICIO", "Patrimonio", "Debito", 3, True),
        # Ingresos
        ("4", "INGRESOS", "Ingreso", "Credito", 1, False),
        ("41", "OPERACIONALES", "Ingreso", "Credito", 2, False),
        ("4135", "COMERCIO AL POR MAYOR Y AL POR MENOR", "Ingreso", "Credito", 3, True),
        ("4175", "DEVOLUCIONES EN VENTAS", "Ingreso", "Debito", 3, True),
        # Gastos
        ("5", "GASTOS", "Gasto", "Debito", 1, False),
        ("51", "OPERACIONALES DE ADMINISTRACION", "Gasto", "Debito", 2, False),
        ("5105", "GASTOS DE PERSONAL", "Gasto", "Debito", 3, True),
        ("5110", "HONORARIOS", "Gasto", "Debito", 3, True),
        ("5120", "ARRENDAMIENTOS", "Gasto", "Debito", 3, True),
        ("5135", "SERVICIOS", "Gasto", "Debito", 3, True),
        ("5140", "GASTOS LEGALES", "Gasto", "Debito", 3, True),
        ("5195", "DIVERSOS", "Gasto", "Debito", 3, True),
        ("52", "OPERACIONALES DE VENTAS", "Gasto", "Debito", 2, False),
        ("5205", "GASTOS DE PERSONAL", "Gasto", "Debito", 3, True),
        ("53", "NO OPERACIONALES", "Gasto", "Debito", 2, False),
        ("5305", "FINANCIEROS", "Gasto", "Debito", 3, True),
        # Costos
        ("6", "COSTOS DE VENTAS", "Costo", "Debito", 1, False),
        ("61", "COSTO DE VENTAS Y DE PRESTACION DE SERVICIOS", "Costo", "Debito", 2, False),
        ("6135", "COMERCIO AL POR MAYOR Y AL POR MENOR", "Costo", "Debito", 3, True),
    ]

    for codigo, nombre, tipo, naturaleza, nivel, acepta in cuentas_base:
        existe = session.query(CuentaContable).filter_by(empresa_id=empresa_id, codigo=codigo).first()
        if not existe:
            c = CuentaContable(
                empresa_id=empresa_id,
                codigo=codigo,
                nombre=nombre,
                tipo=tipo,
                naturaleza=naturaleza,
                nivel=nivel,
                acepta_movimiento=acepta
            )
            session.add(c)
    session.commit()


def crear_empresa_demo(session):
    """Crea una empresa de ejemplo con datos básicos"""
    emp = session.query(Empresa).filter_by(nit="900123456").first()
    if emp:
        return emp

    emp = Empresa(
        nit="900123456",
        dv="7",
        razon_social="Comercializadora El Éxito S.A.S.",
        nombre_comercial="El Éxito",
        direccion="Calle 100 # 15-20",
        ciudad="Bogotá",
        telefono="6011234567",
        email="contabilidad@elexito.com",
        regimen="Común"
    )
    session.add(emp)
    session.commit()
    session.refresh(emp)

    seed_plan_cuentas(session, emp.id)

    # Terceros de ejemplo
    clientes = [
        Tercero(empresa_id=emp.id, tipo="Cliente", nit="800123456", dv="1",
                razon_social="Distribuidora Andina Ltda", ciudad="Medellín",
                telefono="6049876543", email="compras@andina.com"),
        Tercero(empresa_id=emp.id, tipo="Cliente", nit="901234567", dv="8",
                razon_social="Juan Pérez", ciudad="Bogotá",
                telefono="3001234567", email="juan.perez@email.com"),
        Tercero(empresa_id=emp.id, tipo="Proveedor", nit="860123456", dv="3",
                razon_social="Proveedora Nacional S.A.", ciudad="Cali",
                telefono="6025551234", email="ventas@proveedora.com"),
    ]
    for t in clientes:
        session.add(t)

    # Centro de costo
    session.add(CentroCosto(empresa_id=emp.id, codigo="ADM", nombre="Administración"))
    session.add(CentroCosto(empresa_id=emp.id, codigo="VEN", nombre="Ventas"))

    session.commit()
    return emp
