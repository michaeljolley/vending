"""
IR break-beam sensor module for detecting envelopes.
"""
import json
import time
import asyncio
from pathlib import Path
from typing import Callable

# Will be None on non-Pi systems for development
try:
    import RPi.GPIO as GPIO
    PI_AVAILABLE = True
except (ImportError, RuntimeError):
    PI_AVAILABLE = False
    GPIO = None


class BreakBeamSensor:
    """Monitors IR break-beam sensor and triggers callbacks on detection."""
    
    def __init__(self, config_path: str = None, on_trigger: Callable = None):
        self.config = self._load_config(config_path)
        self.on_trigger = on_trigger
        self.last_trigger_time = 0
        self._running = False
        
        sensor_config = self.config["sensor"]
        self.gpio_pin = sensor_config["gpio_pin"]
        self.cooldown_ms = sensor_config.get("cooldown_ms", 2000)
        
        if PI_AVAILABLE:
            self._setup_gpio()
        else:
            print("Running in development mode - sensor will be simulated")
    
    def _load_config(self, config_path: str = None) -> dict:
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.json"
        with open(config_path) as f:
            return json.load(f)
    
    def _setup_gpio(self):
        """Initialize GPIO for the break-beam sensor."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print(f"Break-beam sensor initialized on GPIO {self.gpio_pin}")
    
    def _handle_beam_break(self, channel):
        """Callback for GPIO edge detection."""
        current_time = time.time() * 1000  # ms
        
        # Check cooldown to prevent double-triggers
        if current_time - self.last_trigger_time < self.cooldown_ms:
            return
        
        self.last_trigger_time = current_time
        print(f"Beam broken on GPIO {channel}!")
        
        if self.on_trigger:
            self.on_trigger()
    
    def start(self):
        """Start monitoring the sensor."""
        self._running = True
        
        if PI_AVAILABLE:
            # Use edge detection for instant response
            GPIO.add_event_detect(
                self.gpio_pin,
                GPIO.FALLING,  # Beam broken = signal goes LOW
                callback=self._handle_beam_break,
                bouncetime=200  # Debounce
            )
            print("Sensor monitoring started (GPIO interrupt)")
        else:
            print("Sensor monitoring started (simulation mode)")
    
    def stop(self):
        """Stop monitoring the sensor."""
        self._running = False
        
        if PI_AVAILABLE:
            GPIO.remove_event_detect(self.gpio_pin)
        print("Sensor monitoring stopped")
    
    def cleanup(self):
        """Clean up GPIO resources."""
        if PI_AVAILABLE:
            GPIO.cleanup(self.gpio_pin)
    
    def simulate_trigger(self):
        """Simulate a beam break for testing."""
        print("Simulating beam break...")
        self._handle_beam_break(self.gpio_pin)


# Singleton instance
_sensor: BreakBeamSensor | None = None

def get_sensor() -> BreakBeamSensor:
    global _sensor
    if _sensor is None:
        _sensor = BreakBeamSensor()
    return _sensor

def init_sensor(on_trigger: Callable) -> BreakBeamSensor:
    global _sensor
    _sensor = BreakBeamSensor(on_trigger=on_trigger)
    return _sensor
