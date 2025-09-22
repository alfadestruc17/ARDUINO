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
                print("✅ Conexión establecida con la base de datos")
        except Error as e:
            print(f"❌ Error al conectar con MySQL: {e}")
            self.connection = None
