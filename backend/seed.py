"""Seed inicial: roles, sedes y bloques, dependencias, 12 categorías, 129 tipos y el ADMIN de pruebas.

Uso (PowerShell, con el entorno virtual activo y dentro de backend):
    python seed.py

Se puede ejecutar varias veces: lo que ya existe no se duplica.
"""
from sqlalchemy import select, func
from app import create_app
from app.extensions import db
from app.models.object_type import ObjectType
from app.models.object_category import ObjectCategory
from app.services.seed_service import run_seed

app = create_app()

with app.app_context():
    summary = run_seed()
    print("Seed ejecutado. Registros NUEVOS en esta ejecución:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    total_categories = db.session.execute(select(func.count(ObjectCategory.id))).scalar_one()
    total_types = db.session.execute(select(func.count(ObjectType.id))).scalar_one()
    print(f"Totales en la base: {total_categories} categorías y {total_types} tipos de objeto.")
    print(f'Administrador de pruebas: {app.config["SEED_ADMIN_EMAIL"]}')
