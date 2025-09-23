from abc import ABC, abstractmethod

class Validator(ABC):
    @abstractmethod
    def validate(self, data):
        pass

class PlateFormatValidator(Validator):
    def validate(self, placa):
        if not placa or len(placa) != 3:
            raise ValueError("La placa debe tener exactamente 3 caracteres")
        return True

class PlateExistsValidator(Validator):
    def __init__(self, car_repository):
        self.car_repository = car_repository
    
    def validate(self, placa):
        cars = self.car_repository.get_all_cars()
        if any(car['placa'] == placa for car in cars):
            raise ValueError(f"El vehículo con placa {placa} ya está registrado")
        return True

class ValidationChain:
    def __init__(self):
        self.validators = []
    
    def add_validator(self, validator):
        self.validators.append(validator)
        return self
    
    def validate(self, data):
        for validator in self.validators:
            validator.validate(data)
        return True