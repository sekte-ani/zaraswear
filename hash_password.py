from passlib.hash import scrypt

password = "zaraswear2024"
hashed_password = scrypt.hash(password)

print("Hashed password:", hashed_password)
