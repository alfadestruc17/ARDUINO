from .conexion import Conexion

class CarRepository:
    def __init__(self, db_connection=None):
        self.db = db_connection or Conexion()

    def get_all_cars(self):
        return self.db.obtener_automoviles()

    def add_car(self, placa, saldo=50):
        self.db.registrar_automovil(placa, saldo)

    def update_balance(self, placa, nuevo_saldo):
        self.db.actualizar_saldo(placa, nuevo_saldo)

    def delete_car(self, placa):
        self.db.eliminar_automovil(placa)