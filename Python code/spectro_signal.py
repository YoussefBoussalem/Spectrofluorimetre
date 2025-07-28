""" Base class for signals. """
class Signal:
    from typing import Optional, List, Any

    def __init__(self, name: str, signal: Optional[List[Any]] = None):
        self.name = name
        self.signal = [] if signal is None else signal

    def __str__(self):
        return f"Signal(signal={self.signal})"
    
    def add_signal(self, new_signal: list):
        """
        Add a new signal to the existing signal.
        """
        if not self.signal:
            self.signal = new_signal
        else:
            self.signal.extend(new_signal)
    
    def append_signal(self, value: float):
        """
        Append a single value to the existing signal.
        """
        if self.signal is None:
            self.signal = [value]
        else:
            self.signal.append(value)

    def clear_signal(self):
        """
        Clear the existing signal.
        """
        self.signal = []

    def __add__(self, other) -> 'Signal':
        """
        Overload the '+' operator to sum two signals.
        """
        if isinstance(other, Signal):
            new_signal = [a + b for a, b in zip(self.signal, other.signal)]
            new_name = f"{self.name} + {other.name}"
            return Signal(new_name, new_signal)
        return NotImplemented
    
    def __sub__(self, other) -> 'Signal':
        """
        Overload the '-' operator to subtract two signals.
        """
        if isinstance(other, Signal):
            new_signal = [a - b for a, b in zip(self.signal, other.signal)]
            new_name = f"{self.name} - {other.name}"
            return Signal(new_name, new_signal)
        return NotImplemented
    
    def __mul__(self, other) -> 'Signal':
        """
        Overload the '*' operator to multiply two signals.
        """
        if isinstance(other, Signal):
            new_signal = [a * b for a, b in zip(self.signal, other.signal)]
            new_name = f"{self.name} * {other.name}"
            return Signal(new_name, new_signal)
        return NotImplemented
    
    def __truediv__(self, other) -> 'Signal':
        """
        Overload the '/' operator to divide two signals.
        """
        if isinstance(other, Signal):
            new_signal = [a / b if b != 0 else 0 for a, b in zip(self.signal, other.signal)]
            new_name = f"{self.name} / {other.name}"
            return Signal(new_name, new_signal)
        return NotImplemented