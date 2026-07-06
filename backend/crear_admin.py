import os
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from auth import hashear_password

def crear_admin():
    db = SessionLocal()
    try:
        email = "admin@uandina.edu.pe"
        usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.correo == email).first()
        if not usuario:
            print(f"Creando usuario {email}...")
            nuevo_admin = models.UsuarioSistema(
                nombre_completo="Administrador Sistema",
                correo=email,
                rol="Admin",
                activo=True,
                password_hash=hashear_password("Admin123")
            )
            db.add(nuevo_admin)
            db.commit()
            print("Usuario creado con éxito!")
        else:
            print(f"El usuario {email} ya existe.")
            # Asegurar que tenga la contraseña correcta
            usuario.password_hash = hashear_password("Admin123")
            db.commit()
            print("Contraseña reseteada a Admin123")
    finally:
        db.close()

if __name__ == "__main__":
    crear_admin()
