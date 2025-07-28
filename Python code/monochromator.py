from waveLength import WaveLength
from slit import Slit
from serial import Serial
from time import sleep, time
from math import sin, asin

"""
Abstract base class for monochromators. Not meant to be instantiated directly.
"""
class Monochromator:
    def __init__(self, wLValue: WaveLength, wLOffset: WaveLength, wLCoef: float, serialPort: str, serialBaudRate: int = 9600, 
                 wLStep: int = 0, minWLStep:int = 0, maxWLStep:int = 10000, em: bool = True, ex: bool = False, **kwargs):
        self.wLValue = wLValue
        self.wLOffset = wLOffset
        self.wLCoef = wLCoef

        self.serialPort = serialPort
        self.serialBaudRate = serialBaudRate
        self.serialConnection = Serial()
        try:
            self.serialConnection = Serial(self.serialPort, self.serialBaudRate, timeout=1)
        except Exception as e:
            print(f"Error connecting to serial port {self.serialPort}: {e}")

        if wLStep < minWLStep or wLStep > maxWLStep:
            raise ValueError(f"wLStep must be between {minWLStep} and {maxWLStep}.")
        self.wLStep = wLStep
        self.minWLStep = minWLStep
        self.maxWLStep = maxWLStep

        if (em and ex) or (not em and not ex):
            raise ValueError("Monochromator must be either emission (em) or excitation (ex), not both or neither.")
        self.em = em
        self.ex = ex

    def __str__(self):
        """
        Return a string representation of the Monochromator object.
        """
        return (f"Monochromator(wLValue={self.wLValue.value}, "
                f"wLOffset={self.wLOffset.value}, wLCoef={self.wLCoef}, "
                f"wLStep={self.wLStep}, minWLStep={self.minWLStep}, "
                f"maxWLStep={self.maxWLStep}, "
                f"serialPort={self.serialPort}, serialBaudRate={self.serialBaudRate}, "
                f"em={self.em}, ex={self.ex})")

    def findZero(self, timeout: float = 20.0):
        """
        Find the zero position of the monochromator.
        This is a placeholder implementation.
        """
        print("Finding zero position for Monochromator.")
        self.serialConnection.write(f"ZERO,WL\n".encode())
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
                self.wLStep = 0
                self.wLValue = self.wLOffset
                return
            if parts[0] == "ZERO" and parts[1] == "TIMEOUT":
                raise TimeoutError("Reported zero-finding timeout")
            if parts[0] == "ERROR":
                raise RuntimeError(f"ERROR WL: {parts[1]}")
            sleep(0.01)

    def getWaveLengthFromStep(self, wLStep: int) -> WaveLength:
        """ 
        Get the wavelength from the step count.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    def getStepFromWL(self, wl : WaveLength) -> int:
        """ 
        Get the step count from the wavelength.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    def updateWaveLength(self) -> WaveLength:
        """
        Update the current wavelength, based on the current step count.
        """
        self.wLValue = self.getWaveLengthFromStep(self.wLStep)
        return self.wLValue
    
    def moveToWaveLength(self, wL: WaveLength, timeout: float = 20.0):
        """
        Move to the specified wavelength.
        """
        print(f"Moving to wavelength: {wL.value} nm")
        newWLStep = self.getStepFromWL(wL)
        if newWLStep < self.minWLStep or newWLStep > self.maxWLStep:
            raise ValueError(f"New wavelength step {newWLStep} is out of bounds ({self.minWLStep}, {self.maxWLStep}).")
        direction = newWLStep > self.wLStep
        stepCount = abs(newWLStep - self.wLStep)
        self.serialConnection.write(f"MOVE,WL,{stepCount},{direction}\n".encode())

        start = time()
        while True:
            if time() - start > timeout:
                raise TimeoutError("Timed out waiting for MOVE,DONE for WL")
            line = self.serialConnection.readline().decode().strip()
            if not line:
                continue
            
            print(f"Received line: {line}")
            parts = line.split(',', 2)
            if parts[0] == "MOVE" and parts[1] == "DONE":
                self.wLStep = newWLStep
                self.updateWaveLength()
                return
            if parts[0] == "ERROR":
                raise RuntimeError(f"ERROR WL {parts[1]}")
            sleep(0.01)
        
    
    def openShutter(self):
        """
        Open the shutter of the monochromator.
        """
        self.serialConnection.write(f"SHUTTER, OPEN\n".encode())
        sleep(0.1)  # Allow some time for the shutter to open
        print("Shutter opened.")
    
    def closeShutter(self):
        """
        Close the shutter of the monochromator.
        """
        self.serialConnection.write(f"SHUTTER, CLOSE\n".encode())
        sleep(0.1)  # Allow some time for the shutter to close
        print("Shutter closed.")
    
    def setResolution(self, resolution: float):
        """
        Set the resolution of the monochromator.
        This is a placeholder implementation.
        """
        print(f"Mechanism to set resolution not implemented for this monochromator.")
        


class MonochromatorA(Monochromator):
    def __init__(self, wLValue: WaveLength, wLOffset: WaveLength, wLCoef: float, serialPort: str, serialBaudRate: int = 9600, 
                 wLStep: int = 0, minWLStep:int = 0, maxWLStep:int = 10000, em: bool = True, ex: bool = False):
        super().__init__(wLValue, wLOffset, wLCoef, serialPort, serialBaudRate, wLStep, minWLStep, maxWLStep, em, ex)
        self.serialConnection = Serial()
        try:
            self.serialConnection = Serial(self.serialPort, self.serialBaudRate, timeout=1)
        except Exception as e:
            print(f"Error connecting to serial port {self.serialPort}: {e}")

    def getWaveLengthFromStep(self, wLStep: int) -> WaveLength:
        return WaveLength(self.wLOffset.value + self.wLCoef * wLStep)
    
    def getStepFromWL(self, wl : WaveLength) -> int:
        return int((wl.value - self.wLOffset.value) / self.wLCoef)
    
    def initMotors(self, timeout: float = 100.0):
        """
        Initialize the motors of the monochromator.
        """
        start = time()
        while True:
            if time() - start > timeout:
                raise TimeoutError("Timed out waiting for Monochromator Control Initialized")
            line = self.serialConnection.readline().decode().strip()
            if not line:
                continue
            
            print(f"Received line: {line}")
            if line == "Monochromator Control Initialized":
                break
        sleep(0.1)
        print("Initializing Monochromator motors.")
        self.findZero()
        return
        
class MonochromatorB(Monochromator):
    def __init__(self, wLValue: WaveLength, wLOffset: WaveLength, wLCoef: float, phase: float,
                 slits: Slit, serialPort: str, serialBaudRate: int = 9600, 
                 wLStep: int = 0, minWLStep:int = 0, maxWLStep:int = 10000, em: bool = True, ex: bool = False):
        super().__init__(wLValue, wLOffset, wLCoef, serialPort, serialBaudRate, wLStep, minWLStep, maxWLStep, em, ex)
        self.slits = slits
        self.phase = phase
        self.serialConnection = Serial()
        try:
            self.serialConnection = Serial(self.serialPort, self.serialBaudRate, timeout=1)
        except Exception as e:
            print(f"Error connecting to serial port {self.serialPort}: {e}")
        slits.serialConnection = self.serialConnection

    def getWaveLengthFromStep(self, wLStep: int) -> WaveLength:
        return WaveLength(self.wLOffset.value + self.wLCoef * sin(self.phase * wLStep))

    def getStepFromWL(self, wl : WaveLength) -> int:
        return int(asin((wl.value - self.wLOffset.value) / self.wLCoef))

    def initMotors(self, timeout: float = 100.0):
        """
        Initialize the motors of the monochromator.
        """
        start = time()
        while True:
            if time() - start > timeout:
                raise TimeoutError("Timed out waiting for Monochromator Control Initialized")
            line = self.serialConnection.readline().decode().strip()
            if not line:
                continue
            
            print(f"Received line: {line}")
            if line == "Monochromator Control Initialized":
                break
        sleep(0.1)
        print("Initializing Monochromator motors.")
        self.findZero()
        self.slits.findZero()

    def setResolution(self, resolution: float):
        """
        Set the resolution of the monochromator.
        """
        self.resolution = resolution
        self.slits.moveToValue(WaveLength(resolution))
        
