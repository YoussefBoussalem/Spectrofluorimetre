class WaveLength():
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f"WaveLength({self.value}nm)"

    def to_waveNumber(self):
        """
        Convert wavelength to wavenumber.
        Wavenumber (cm^-1) = 10^4 / wavelength (nm)
        """
        if self.value == 0:
            raise ValueError("Wavelength cannot be zero for wavenumber conversion.")
        return 10**4 / self.value
    
    def to_frequency(self):
        """
        Convert wavelength to frequency.
        Frequency (Hz) = speed of light (m/s) / wavelength (m)
        """
        speed_of_light = 299792458
        if self.value == 0:
            raise ValueError("Wavelength cannot be zero for frequency conversion.")
        return speed_of_light / self.value

    def __add__(self, other: float) -> 'WaveLength':
        return WaveLength(self.value + other)
    
    def __radd__(self, other: float) -> 'WaveLength':
        return WaveLength(other + self.value)
    
    def __sub__(self, other: float) -> 'WaveLength':
        return WaveLength(self.value - other)

class WLRange:
    def __init__(self, wLMin:WaveLength, wLMax: WaveLength, wLStep: WaveLength):
        self.wLStep = wLStep
        if wLMin.value >= wLMax.value:
            raise ValueError("Minimum wavelength must be less than maximum wavelength.")
        self.wLMin = wLMin
        self.wLMax = wLMax
        
    def __str__(self):
        return f"WLRange(wLMin={self.wLMin.value}, wLMax={self.wLMax.value}, wLStep={self.wLStep.value})"
