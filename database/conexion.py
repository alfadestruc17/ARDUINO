import mysql.connector
from mysql.connector import Error

class Conexion:
    def __init__(self, host="localhost", database="arduino_peaje", user="root", password=""):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.conectar()

    def conectar(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            if self.connection.is_connected():
                print(" Conexión establecida con la base de datos")
        except Error as e:
            print(f" Error al conectar con MySQL: {e}")
            self.connection = None

    def cerrar(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print(" Conexión cerrada")


    def obtener_automoviles(self):
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT id, placa, saldo FROM automovil")
            resultados = cursor.fetchall()
            return resultados
        except Exception as e:
            print("Error:", e)
            return []  # o maneja el error como prefieras
        finally:
            if cursor:
                cursor.close()


    def registrar_automovil(self, placa, saldo=50):
        """Registra un automóvil con saldo inicial (50 por defecto)"""
        if self.connection is None:
            raise Exception("No hay conexión a la base de datos")
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("INSERT INTO automovil (placa, saldo) VALUES (%s, %s)", (placa.upper(), saldo))
            self.connection.commit()
        except Error as e:
            print(f" Error al registrar automóvil: {e}")
            raise  # re-raise to propagate to app.py
        finally:
            if cursor:
                cursor.close()

    def eliminar_automovil(self, placa):
        """Elimina un automóvil por placa"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM automovil WHERE placa = %s", (placa.upper(),))
            self.connection.commit()
        except Error as e:
            print(f" Error al eliminar automóvil: {e}")
        finally:
            if cursor:
                cursor.close()

    def actualizar_saldo(self, placa, nuevo_saldo):
        """Actualiza el saldo de un automóvil"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE automovil SET saldo = %s WHERE placa = %s", (nuevo_saldo, placa.upper()))
            self.connection.commit()
        except Error as e:
            print(f" Error al actualizar saldo: {e}")
        finally:
            if cursor:
                cursor.close()

