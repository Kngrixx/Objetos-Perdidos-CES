# Valores fijos del negocio. Se usan en modelos, servicios y pruebas.

# Roles
ADMIN = "ADMIN"
OPERADOR = "OPERADOR"
CONSULTA = "CONSULTA"
ROLE_NAMES = [ADMIN, OPERADOR, CONSULTA]

# Estado del objeto (situación física). is_active es otro eje: validez del registro.
DISPONIBLE = "DISPONIBLE"
DEVUELTO = "DEVUELTO"
OBJECT_STATUSES = [DISPONIBLE, DEVUELTO]

# Estado de las reclamaciones
PENDIENTE = "PENDIENTE"
ACEPTADA = "ACEPTADA"
RECHAZADA = "RECHAZADA"
CLAIM_STATUSES = [PENDIENTE, ACEPTADA, RECHAZADA]

# Tipo de vinculación de la persona que entrega o reclama
AFFILIATION_TYPES = ["ESTUDIANTE", "EMPLEADO", "CONTRATISTA", "PROVEEDOR", "VISITANTE"]

# Mecanismo de recepción elegido para la devolución
RECEIPT_METHOD = "CONFIRMACION_DIGITAL"
