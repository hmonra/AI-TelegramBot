import bcrypt

password = "CONTRASEÑA"  # Reemplaza con tu contraseña real
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed)