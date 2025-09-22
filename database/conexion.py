import _mysql.connector
from _mysql.connector import Error
import os
import sys

class databaseconnection:
    def __init__(self, host="localhost", user="root", password="", database="arduino_peaje"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None



    def connect(self):
        try: 
            self.connection = _mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            if self.connection.is_connected():
                print("Conexion exitosa a la base de datos")
        except Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            self.connection = None