from .validation_service import ValidationChain, PlateFormatValidator, PlateExistsValidator

class CarService:
    INITIAL_BALANCE = 50
    REGISTRATION_FEE = 10

    def __init__(self, car_repository):
        self.car_repository = car_repository
        self.validation_chain = ValidationChain()
        self._setup_validators()

    def _setup_validators(self):
        self.validation_chain.add_validator(PlateFormatValidator())
        self.validation_chain.add_validator(PlateExistsValidator(self.car_repository))

    def register_car(self, placa):
        """
        Registra un nuevo vehículo con el saldo inicial menos la cuota de registro
        """
        # Validar la placa
        placa = placa.strip().upper()
        self.validation_chain.validate(placa)
        
        # Calcular saldo inicial después del descuento
        final_balance = self.INITIAL_BALANCE - self.REGISTRATION_FEE
        
        # Registrar el vehículo
        self.car_repository.add_car(placa, final_balance)
        
        return {
            'placa': placa,
            'saldo_inicial': self.INITIAL_BALANCE,
            'costo_registro': self.REGISTRATION_FEE,
            'saldo_final': final_balance
        }

    def update_balance(self, placa, amount):
        """
        Actualiza el saldo de un vehículo
        """
        placa = placa.strip().upper()
        cars = self.car_repository.get_all_cars()
        car = next((c for c in cars if c['placa'] == placa), None)
        
        if not car:
            raise ValueError(f"No se encontró el vehículo con placa {placa}")
            
        if amount <= 0:
            raise ValueError("El monto debe ser mayor a 0")
            
        new_balance = car['saldo'] + amount
        self.car_repository.update_balance(placa, new_balance)
        
        return {
            'placa': placa,
            'saldo_anterior': car['saldo'],
            'monto_recarga': amount,
            'nuevo_saldo': new_balance
        }