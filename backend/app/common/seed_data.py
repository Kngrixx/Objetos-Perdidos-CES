# Datos iniciales del seed (enunciado: contexto inicial y sección 11).
# Todo es ficticio o genérico; no hay datos personales reales.

ROLES = [
    ("ADMIN", "Administra usuarios y catálogos, corrige, reactiva, consulta auditoría y exporta."),
    ("OPERADOR", "Recibe, edita, registra reclamaciones y devoluciones, inactiva errores y exporta."),
    ("CONSULTA", "Consulta inventario activo y detalles permitidos, sin datos personales."),
]

# Sedes y bloques iniciales. Sabaneta usa "Bloque principal" como nombre provisional editable.
CAMPUSES = {
    "Poblado": ["Bloque A", "Bloque B", "Bloque C"],
    "Sabaneta": ["Bloque principal"],
}

DEPARTMENTS = [
    "Facultad de Medicina",
    "Facultad de Ingeniería",
    "Facultad de Odontología",
    "Facultad de Psicología",
    "Facultad de Derecho",
    "Facultad de Ciencias Administrativas y Económicas",
    "Facultad de Fisioterapia",
    "Facultad de Enfermería",
    "Facultad de Medicina Veterinaria y Zootecnia",
    "Facultad de Ciencias y Biotecnología",
    "Biblioteca",
    "Bienestar Universitario",
    "Seguridad y Vigilancia",
    "Servicios Generales",
    "Admisiones y Registro",
]

# 12 categorías y 129 tipos (mínimo exigido: 10 categorías y 100 tipos).
OBJECT_TYPES = {
    "Tecnología": [
        "Celular", "Tableta", "Computador portátil", "Lector electrónico", "Reloj inteligente",
        "Calculadora", "Cámara", "Cámara web", "Mouse", "Teclado", "Lápiz digital",
    ],
    "Audio y accesorios": [
        "Audífonos de diadema", "Audífonos inalámbricos", "Audífonos de cable", "Estuche de audífonos",
        "Parlante portátil", "Micrófono", "Adaptador de audio", "Grabadora",
    ],
    "Cables y energía": [
        "Cargador de celular", "Cargador de portátil", "Cable USB C", "Cable micro USB",
        "Cable Lightning", "Cable HDMI", "Adaptador de corriente", "Batería externa",
        "Cable de red", "Cargador de reloj",
    ],
    "Documentos y tarjetas": [
        "Cédula", "Carné universitario", "Licencia de conducción", "Pasaporte", "Tarjeta bancaria",
        "Tarjeta de transporte", "Tarjeta de acceso", "Documento impreso", "Certificado",
        "Carpeta de documentos",
    ],
    "Llaves y acceso": [
        "Llave de vivienda", "Llave de vehículo", "Llave de motocicleta", "Llave de casillero",
        "Llavero", "Control de garaje", "Control remoto", "Candado",
    ],
    "Vestuario": [
        "Chaqueta", "Saco", "Buzo", "Camiseta", "Camisa", "Pantalón", "Falda", "Bata",
        "Uniforme clínico", "Gorra", "Sombrero", "Bufanda", "Guantes", "Cinturón", "Chaleco",
    ],
    "Bolsos y estuches": [
        "Morral", "Bolso", "Cartera", "Billetera", "Canguro", "Maletín", "Lonchera", "Cartuchera",
        "Estuche de gafas", "Funda de portátil", "Bolsa reutilizable",
    ],
    "Papelería y estudio": [
        "Cuaderno", "Libreta", "Agenda", "Libro", "Manual", "Carpeta académica", "Bolígrafo",
        "Lápiz", "Portaminas", "Marcador", "Resaltador", "Regla", "Compás", "Borrador",
        "Memoria USB", "Disco externo",
    ],
    "Salud y laboratorio": [
        "Estetoscopio", "Tensiómetro portátil", "Oxímetro", "Gafas de protección", "Careta",
        "Modelo anatómico", "Estuche de instrumental", "Termómetro", "Linterna clínica",
        "Protector facial",
    ],
    "Uso personal": [
        "Gafas formuladas", "Gafas de sol", "Reloj de pulsera", "Anillo", "Pulsera", "Collar",
        "Aretes", "Sombrilla", "Peine", "Cepillo", "Estuche de cosméticos", "Neceser",
    ],
    "Alimentación": [
        "Termo", "Botella reutilizable", "Taza", "Vaso", "Recipiente de alimentos",
        "Cubiertos reutilizables", "Bolsa térmica", "Cafetera portátil",
    ],
    "Deporte y movilidad": [
        "Balón", "Raqueta", "Casco de bicicleta", "Casco de motocicleta", "Rodillera",
        "Toalla deportiva", "Banda elástica", "Zapatillas", "Patines", "Luces de bicicleta",
    ],
}
