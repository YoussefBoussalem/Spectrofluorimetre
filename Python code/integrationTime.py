class IntegrationTime:
    def __init__(self, value: float = 1000):
        if value <= 0:
            raise ValueError("Integration time must be a positive value.")
        if value > 1000000:
            raise ValueError("Integration time must not exceed 1000000 ms.")
        self.value = value

    def set_integration_time(self, value: float):
        if value <= 0:
            raise ValueError("Integration time must be a positive value.")
        if value > 1000000:
            raise ValueError("Integration time must not exceed 1000000 ms.")
        self.value = value

    def __str__(self):
        return f"Integration Time: {self.value} ms"
    
    def to_seconds(self) -> float:
        """
        Convert integration time from milliseconds to seconds.
        """
        return self.value / 1000.0