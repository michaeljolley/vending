"""
Servo controller module for PCA9685-based continuous rotation servos.
"""
import time
import json
from pathlib import Path

# Will be None on non-Pi systems for development
try:
    from adafruit_servokit import ServoKit
    PI_AVAILABLE = True
except (ImportError, NotImplementedError):
    PI_AVAILABLE = False
    ServoKit = None


class ServoController:
    """Controls continuous rotation servos via PCA9685."""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.kit = None
        self._busy = False
        
        if PI_AVAILABLE:
            try:
                i2c_address = self.config["servo"].get("i2c_address", 0x40)
                self.kit = ServoKit(channels=16, address=i2c_address)
                print(f"PCA9685 initialized at address {hex(i2c_address)}")
            except Exception as e:
                print(f"Failed to initialize PCA9685: {e}")
        else:
            print("Running in development mode - servo commands will be simulated")
    
    def _load_config(self, config_path: str = None) -> dict:
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.json"
        with open(config_path) as f:
            return json.load(f)
    
    def get_slot_config(self, slot_id: int) -> dict | None:
        """Get configuration for a specific slot."""
        for slot in self.config["slots"]:
            if slot["id"] == slot_id and slot.get("enabled", True):
                return slot
        return None
    
    def get_enabled_slots(self) -> list[dict]:
        """Get all enabled slots."""
        return [s for s in self.config["slots"] if s.get("enabled", True)]
    
    def is_busy(self) -> bool:
        """Check if a dispense is currently in progress."""
        return self._busy
    
    def dispense(self, slot_id: int) -> bool:
        """
        Spin the servo for the specified slot to dispense candy.
        Returns True if successful, False if slot not found or busy.
        """
        if self._busy:
            print(f"Cannot dispense: already busy")
            return False
        
        slot = self.get_slot_config(slot_id)
        if not slot:
            print(f"Slot {slot_id} not found or disabled")
            return False
        
        channel = slot["channel"]
        duration_ms = slot.get("spin_duration_ms", 2000)
        speed = self.config["servo"].get("speed", 0.5)
        
        self._busy = True
        try:
            self._spin_servo(channel, speed, duration_ms)
            return True
        finally:
            self._busy = False
    
    def _spin_servo(self, channel: int, speed: float, duration_ms: int):
        """
        Spin a continuous rotation servo.
        Speed: -1.0 (full reverse) to 1.0 (full forward), 0 = stop
        """
        print(f"Spinning servo on channel {channel} at speed {speed} for {duration_ms}ms")
        
        if self.kit:
            # For continuous rotation servos:
            # throttle = -1.0 to 1.0, where 0 is stopped
            self.kit.continuous_servo[channel].throttle = speed
            time.sleep(duration_ms / 1000.0)
            self.kit.continuous_servo[channel].throttle = 0
        else:
            # Simulate on non-Pi systems
            time.sleep(duration_ms / 1000.0)
        
        print(f"Servo on channel {channel} stopped")
    
    def stop_all(self):
        """Emergency stop all servos."""
        if self.kit:
            for slot in self.config["slots"]:
                channel = slot["channel"]
                self.kit.continuous_servo[channel].throttle = 0
        self._busy = False
        print("All servos stopped")


# Singleton instance
_controller: ServoController | None = None

def get_servo_controller() -> ServoController:
    global _controller
    if _controller is None:
        _controller = ServoController()
    return _controller
