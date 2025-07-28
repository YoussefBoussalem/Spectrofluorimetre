from spectro_signal import Signal
from monochromator import Monochromator
from waveLength import WaveLength, WLRange
from integrationTime import IntegrationTime
from time import sleep
from numpy import arange
from datetime import datetime

"""
Abstract base class for measures. Not meant to be instantiated directly.
"""

class Measure:
    def __init__(self, name: str, em_range, ex_range, integrationTime:IntegrationTime,
                ex_Monochromator: Monochromator, em_Monochromator: Monochromator, resolution: float = 0.1,
                measured_signal: Signal = Signal("Measured signal"), reference_signal: Signal = Signal("Reference signal"), 
                **kwargs):
        """
        Initialize the Measure class with the given parameters.
        """
        self.name = name
        self.em_range = em_range
        self.ex_range = ex_range
        self.integrationTime = integrationTime
        self.resolution = resolution

        if ex_Monochromator.ex ==False:
            raise ValueError("ex_Monochromator must be an excitation monochromator.")
        self.ex_monochromator = ex_Monochromator
        if em_Monochromator.em ==False:
            raise ValueError("em_Monochromator must be an emission monochromator.")
        self.em_monochromator = em_Monochromator

        self.measured_signal = Signal(f"{self.name} : Measured signal")
        self.reference_signal = Signal(f"{self.name} : Reference signal")

    def __str__(self):
        """
        Return a string representation of the Measure object.
        """
        return (f"Measure(name={self.name}, "
                f"em_range={self.em_range}, ex_range={self.ex_range}, "
                f"integrationTime={self.integrationTime.value} milliseconds, "
                f"measured_signal={self.measured_signal}, "
                f"reference_signal={self.reference_signal})")
    
    def measureSignal(self):
        """
        Abstract method to be implemented by subclasses.
        This method should contain the logic for on-time measurement.
        """
        sleep(self.integrationTime.to_seconds())
        return 32/self.integrationTime.to_seconds()
    
    def measureReference(self):
        """
        Not implemented yet.
        This method should contain the logic for measuring the reference signal.
        """
        return 32

    def measure(self, *args, **kwargs):
        """
        Abstract method to be implemented by subclasses.
        This method should contain the logic for measuring.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    def plot(self, *args, **kwargs):
        """
        Abstract method to be implemented by subclasses.
        This method should contain the logic for plotting the measure.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    def saveResults(self, *args, **kwargs):
        """
        Abstract method to be implemented by subclasses.
        This method should contain the logic for saving the measure.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
class uniqueWLMeasure(Measure):
    def __init__(self, name: str, em_range: WaveLength, ex_range: WaveLength, integrationTime: IntegrationTime,
                 ex_Monochromator: Monochromator, em_Monochromator: Monochromator, resolution: float = 0.1,
                 measured_signal: Signal = Signal("Measured signal"),
                 reference_signal: Signal = Signal("Reference signal")):
        super().__init__(name, em_range, ex_range, integrationTime,
                         ex_Monochromator, em_Monochromator, resolution,
                         measured_signal, reference_signal)
        self.em_range = em_range
        self.ex_range = ex_range
    
    def measure(self):
        """
        Implement the logic for measuring in the unique wavelength measure.
        """
        print(f"Measuring {self.name} at unique wavelengths.")
        self.ex_monochromator.moveToWaveLength(self.ex_range)
        self.em_monochromator.moveToWaveLength(self.em_range)
        self.ex_monochromator.setResolution(self.resolution)
        self.em_monochromator.setResolution(self.resolution)
        self.ex_monochromator.openShutter()
        self.em_monochromator.openShutter()
        self.measured_signal.append_signal(self.measureSignal())
        self.reference_signal.append_signal(self.measureReference())
        print(f"Measured signal: {self.measured_signal}, Reference signal: {self.reference_signal}")
        self.ex_monochromator.closeShutter()
        self.em_monochromator.closeShutter()

    def saveResults(self, folder:str = "source/Measure CSV"):
        """
        Save the results of the measurement to a CSV file.
        """
        import csv
        import os

        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = os.path.join(folder, f"{self.name}.csv")
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            now = datetime.now()
            writer.writerow(['Date :', now.strftime("%Y-%m-%d"), 'Time :', now.strftime("%H:%M:%S"), 'Name :', self.name])
            writer.writerow(['Ex Wavelength (nm)', 'Em Wavelength (nm)', 'Measured Signal', 'Reference Signal'])
            for i in range(len(self.measured_signal.signal)):
                writer.writerow([self.ex_range.value, self.em_range.value, self.measured_signal.signal[i], self.reference_signal.signal[i]])

        print(f"Results saved to {filename} in {folder}")        

class synchroScanMeasure(Measure):
    def __init__(self, name: str, em_range: WaveLength, ex_range: WLRange, integrationTime: IntegrationTime,
                 ex_Monochromator: Monochromator, em_Monochromator: Monochromator, resolution: float = 0.1,
                 measured_signal: Signal = Signal("Measured signal"),
                 reference_signal: Signal = Signal("Reference signal")):
        super().__init__(name, em_range, ex_range, integrationTime,
                         ex_Monochromator, em_Monochromator, resolution,
                         measured_signal, reference_signal)
        self.em_range = em_range
        self.ex_range = ex_range
    
    def measure(self):
        """
        Think of em-range as a wavelentgh offset for the synchronized scan and ex-range as a range of wavelengths.
        Implement the logic for measuring in the synchronized scan.
        """
        print(f"Measuring {self.name} with synchronized scan.")
        self.ex_monochromator.openShutter()
        self.em_monochromator.openShutter()
        self.ex_monochromator.setResolution(self.resolution)
        self.em_monochromator.setResolution(self.resolution)
        for i in arange(self.ex_range.wLMin.value, self.ex_range.wLMax.value+self.ex_range.wLStep.value, self.ex_range.wLStep.value):
            current_ex_wl = WaveLength(i)
            print(f"Moving to excitation wavelength: {current_ex_wl.value} nm")
            self.ex_monochromator.moveToWaveLength(current_ex_wl)
            print(f"Moving to emission wavelength: {current_ex_wl.value + self.em_range.value} nm")
            self.em_monochromator.moveToWaveLength(WaveLength(current_ex_wl.value + self.em_range.value))
            self.measured_signal.append_signal(self.measureSignal())
            self.reference_signal.append_signal(self.measureReference())
        self.ex_monochromator.closeShutter()
        self.em_monochromator.closeShutter()
    
    def saveResults(self, folder:str = "source/Measure CSV"):
        """
        Save the results of the measurement to a CSV file.
        """
        import csv
        import os

        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = os.path.join(folder, f"{self.name}.csv")
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            now = datetime.now()
            writer.writerow(['Date :', now.strftime("%Y-%m-%d"), 'Time :', now.strftime("%H:%M:%S"), 'Name :', self.name])
            writer.writerow(['Ex Wavelength (nm)', 'Em Wavelength (nm)', 'Measured Signal', 'Reference Signal'])
            for i in range(len(self.measured_signal.signal)):
                writer.writerow([self.ex_range.wLMin.value + i*self.ex_range.wLStep.value, self.ex_range.wLMin.value + i*self.ex_range.wLStep.value +self.em_range.value, self.measured_signal.signal[i], self.reference_signal.signal[i]])

        print(f"Results saved to {filename} in {folder}")

    
class ExScanMeasure(Measure):
    def __init__(self, name: str, em_range: WaveLength, ex_range: WLRange, integrationTime: IntegrationTime,
                 ex_Monochromator: Monochromator, em_Monochromator: Monochromator, resolution: float = 0.1,
                 measured_signal: Signal = Signal("Measured signal"),
                 reference_signal: Signal = Signal("Reference signal")):
        super().__init__(name, em_range, ex_range, integrationTime,
                         ex_Monochromator, em_Monochromator, resolution,
                         measured_signal, reference_signal)
        self.em_range = em_range
        self.ex_range = ex_range

    def measure(self):
        print(f"Measuring {self.name} with excitation scan.")
        self.em_monochromator.moveToWaveLength(self.em_range)
        self.ex_monochromator.openShutter()
        self.em_monochromator.openShutter()
        self.ex_monochromator.setResolution(self.resolution)
        self.em_monochromator.setResolution(self.resolution)
        for i in arange(self.ex_range.wLMin.value, self.ex_range.wLMax.value+self.ex_range.wLStep.value, self.ex_range.wLStep.value):
            current_ex_wl = WaveLength(i)
            print(f"Moving to excitation wavelength: {current_ex_wl.value} nm")
            self.ex_monochromator.moveToWaveLength(current_ex_wl)
            self.measured_signal.append_signal(self.measureSignal())
            self.reference_signal.append_signal(self.measureReference())
        self.ex_monochromator.closeShutter()
        self.em_monochromator.closeShutter()

    def saveResults(self, folder:str = "source/Measure CSV"):
        """
        Save the results of the measurement to a CSV file.
        """
        import csv
        import os

        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = os.path.join(folder, f"{self.name}.csv")
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            now = datetime.now()
            writer.writerow(['Date :', now.strftime("%Y-%m-%d"), 'Time :', now.strftime("%H:%M:%S"), 'Name :', self.name])
            writer.writerow(['Ex Wavelength (nm)', 'Em Wavelength (nm)', 'Measured Signal', 'Reference Signal'])
            for i in range(len(self.measured_signal.signal)):
                writer.writerow([self.ex_range.wLMin.value + i*self.ex_range.wLStep.value, self.em_range.value, self.measured_signal.signal[i], self.reference_signal.signal[i]])

        print(f"Results saved to {filename} in {folder}")

class EmScanMeasure(Measure):
    def __init__(self, name: str, em_range: WLRange, ex_range: WaveLength, integrationTime: IntegrationTime,
                 ex_Monochromator: Monochromator, em_Monochromator: Monochromator, resolution: float = 0.1,
                 measured_signal: Signal = Signal("Measured signal"),
                 reference_signal: Signal = Signal("Reference signal"), **kwargs):
        super().__init__(name, em_range, ex_range, integrationTime,
                         ex_Monochromator, em_Monochromator, resolution,
                         measured_signal, reference_signal, **kwargs)
        self.em_range = em_range
        self.ex_range = ex_range
    
    def measure(self):
        print(f"Measuring {self.name} with emission scan.")
        self.ex_monochromator.moveToWaveLength(self.ex_range)
        self.ex_monochromator.openShutter()
        self.em_monochromator.openShutter()
        self.ex_monochromator.setResolution(self.resolution)
        self.em_monochromator.setResolution(self.resolution)
        for i in arange(self.em_range.wLMin.value, self.em_range.wLMax.value+self.em_range.wLStep.value, self.em_range.wLStep.value):
            current_em_wl = WaveLength(i)
            print(f"Moving to emission wavelength: {current_em_wl.value} nm")
            self.em_monochromator.moveToWaveLength(current_em_wl)
            self.measured_signal.append_signal(self.measureSignal())
            self.reference_signal.append_signal(self.measureReference())
        self.ex_monochromator.closeShutter()
        self.em_monochromator.closeShutter()

    def saveResults(self, folder:str = "source/Measure CSV"):
        """
        Save the results of the measurement to a CSV file.
        """
        import csv
        import os

        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = os.path.join(folder, f"{self.name}.csv")
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            now = datetime.now()
            writer.writerow(['Date :', now.strftime("%Y-%m-%d"), 'Time :', now.strftime("%H:%M:%S"), 'Name :', self.name])
            writer.writerow(['Ex Wavelength (nm)', 'Em Wavelength (nm)', 'Measured Signal', 'Reference Signal'])
            for i in range(len(self.measured_signal.signal)):
                writer.writerow([self.ex_range.value, self.em_range.wLMin.value + i*self.em_range.wLStep.value, self.measured_signal.signal[i], self.reference_signal.signal[i]])

        print(f"Results saved to {filename} in {folder}")