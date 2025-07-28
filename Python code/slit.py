from waveLength import WaveLength
from serial import Serial
from time import sleep, time

class Slit:
    def __init__(self, numberOfSlits: int, value: WaveLength, offsetWL: WaveLength, coefWL: float, 
                 serialConnection: Serial = Serial(), step: int = 0, minStep: int = -1000, maxStep: int = 10000):
        self.number = numberOfSlits
        self.value = value
        self.offsetWL = offsetWL
        self.coefWL = coefWL
        self.serialConnection = serialConnection
        if step < minStep or step > maxStep:
            raise ValueError("Resolution must respect the specifications.")
        self.step = step
        self.minStep = minStep
        self.maxStep = maxStep
        self.updateWaveLength()

    def getValueFromStep(self, step: int) -> WaveLength:
        """
        Get the resolution value.
        """
        return WaveLength(self.offsetWL.value + self.coefWL * step)

    def getStepFromValue(self, value: WaveLength):
        """
        Set the resolution value.
        """
        return int((value.value - self.offsetWL.value) / self.coefWL)

    def updateWaveLength(self):
        """
        Update the wavelength value based on the current step count.
        """
        self.value = self.getValueFromStep(self.step)

    def findZero(self, timeout: float = 20.0):
        """
        Find the zero position of the monochromator.
        This is a placeholder implementation.
        """
        for i in range(1, self.number + 1):
            print(f"Finding zero position for SLIT {i}.")
            self.serialConnection.write(f"ZERO,SLIT{i}\n".encode())
            sleep(0.1)
            start = time()
            while True:
                if time() - start > timeout:
                    raise TimeoutError("Timed out waiting for ZERO,DONE")
                line = self.serialConnection.readline().decode().strip()
                if not line:
                    continue

                # expect "ZERO,DONE" or "ZERO,TIMEOUT" or "ERROR,UNKNOWN_MOTOR"
                print(f"Received line: {line}")
                parts = line.split(',', 2)
                if parts[0] == "ZERO" and parts[1] == "DONE":
                    self.step = 0
                    self.value = self.offsetWL
                    return
                if parts[0] == "ZERO" and parts[1] == "TIMEOUT":
                    raise TimeoutError("MCU reported zero-finding timeout")
                if parts[0] == "ERROR":
                    raise RuntimeError(f"ERROR SLIT{i}: {parts[1]}")
                sleep(0.01)

    def moveToValue(self, value: WaveLength, timeout: float = 20.0):
        """
        Move the monochromator to the specified wavelength value.
        """
        print(f"Moving to wavelength: {value.value} nm")
        newStep = self.getStepFromValue(value.value)
        if newStep < self.minStep or newStep > self.maxStep:
            raise ValueError(f"New wavelength step {newStep} is out of bounds ({self.minStep}, {self.maxStep}).")
        direction = newStep > self.step
        stepCount = abs(newStep - self.step)
        for i in range(1, self.number + 1):
            print(f"Name: SLIT{i}, Direction: {direction}, Step Count: {stepCount}")
            self.serialConnection.write(f"MOVE,SLIT{i},{stepCount},{direction}\n".encode())

            start = time()
            while True:
                if time() - start > timeout:
                    raise TimeoutError(f"Timed out waiting for MOVE,DONE for SLIT{i}")
                line = self.serialConnection.readline().decode().strip()
                if not line:
                    continue

                print(f"Received line: {line}")
                parts = line.split(',', 2)
                if parts[0] == "MOVE" and parts[1] == "DONE":
                    self.step = newStep
                    self.updateWaveLength()
                    return
                if parts[0] == "ERROR":
                    raise RuntimeError(f"ERROR SLIT{i}: {parts[1]}")
                sleep(0.01)
    
    def moveToPercentage(self, percentage: float, timeout: float = 20.0):
        """
        Move the monochromator to a specified percentage of the range.
        """
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100.")
        newStep = int(self.minStep + (self.maxStep - self.minStep) * (percentage / 100))
        if newStep < self.minStep or newStep > self.maxStep:
            raise ValueError(f"New wavelength step {newStep} is out of bounds ({self.minStep}, {self.maxStep}).")
        direction = newStep > self.step
        stepCount = abs(newStep - self.step)
        for i in range(1, self.number + 1):
            print(f"Name: SLIT{i}, Direction: {direction}, Step Count: {stepCount}")
            self.serialConnection.write(f"MOVE,SLIT{i},{stepCount},{direction}\n".encode())

            start = time()
            while True:
                if time() - start > timeout:
                    raise TimeoutError(f"Timed out waiting for MOVE,DONE for SLIT{i}")
                line = self.serialConnection.readline().decode().strip()
                if not line:
                    continue
                
                print(f"Received line: {line}")
                parts = line.split(',', 2)
                if parts[0] == "MOVE" and parts[1] == "DONE":
                    self.step = newStep
                    self.updateWaveLength()
                    return
                if parts[0] == "ERROR":
                    raise RuntimeError(f"ERROR SLIT{i}: {parts[1]}")
                sleep(0.01)