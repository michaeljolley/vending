# Valentine's Candy Machine 💝

A Raspberry Pi-powered candy vending machine for Valentine's Day! Drop an envelope in the box to earn credits, then choose a candy slot to dispense a treat.

## Hardware Required

- Raspberry Pi 4
- 7" Touchscreen Display
- MakerFocus PCA9685 16-Channel PWM Driver
- IR Break-Beam Sensor (5mm LED)
- 3-4x FS90R Continuous Rotation Servos
- 5V 2A Power Supply (for servos)
- 470µF 10V Capacitor
- Jumper Wires

## Wiring

### PCA9685 (I2C)
| PCA9685 | Raspberry Pi |
|---------|--------------|
| VCC     | 3.3V         |
| GND     | GND          |
| SDA     | GPIO 2 (SDA) |
| SCL     | GPIO 3 (SCL) |
| V+      | External 5V+ |
| GND     | External GND |

### IR Break-Beam Sensor
| Sensor | Raspberry Pi |
|--------|--------------|
| VCC    | 5V           |
| GND    | GND          |
| OUT    | GPIO 17      |

### Servos (to PCA9685)
- Slot 1 → Channel 0
- Slot 2 → Channel 1
- Slot 3 → Channel 2
- Slot 4 → Channel 3 (optional)

### Capacitor
- 470µF 10V across V+ and GND on PCA9685

## Installation on Raspberry Pi

1. **Clone or copy project to Pi:**
   ```bash
   cd ~
   git clone <your-repo> juke
   # or copy files to ~/juke
   ```

2. **Create virtual environment and install dependencies:**
   ```bash
   cd ~/juke
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Enable I2C on the Pi:**
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options → I2C → Enable
   ```

4. **Test the application:**
   ```bash
   source venv/bin/activate
   python backend/main.py
   ```
   Open `http://localhost:8000` in a browser.

5. **Install as a service (auto-start on boot):**
   ```bash
   sudo cp scripts/candy-machine.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable candy-machine
   sudo systemctl start candy-machine
   ```

6. **Setup kiosk mode (fullscreen browser on boot):**
   ```bash
   chmod +x scripts/setup-kiosk.sh
   ./scripts/setup-kiosk.sh
   sudo reboot
   ```

## Configuration

Edit `config.json` to customize:

```json
{
  "slots": [
    {
      "id": 1,
      "name": "Slot 1",
      "channel": 0,
      "spin_duration_ms": 2000,
      "enabled": true
    }
  ],
  "sensor": {
    "gpio_pin": 17,
    "cooldown_ms": 2000
  },
  "servo": {
    "speed": 0.5
  }
}
```

- **spin_duration_ms**: How long the motor spins (adjust for candy drop)
- **cooldown_ms**: Minimum time between envelope detections
- **speed**: Motor speed (0.1 to 1.0)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI |
| `/api/state` | GET | Get current credits and slots |
| `/api/dispense/{slot_id}` | POST | Dispense from a slot |
| `/api/simulate-envelope` | POST | Test: simulate envelope drop |
| `/ws` | WebSocket | Real-time state updates |

## Testing Without Hardware

The app runs in simulation mode on non-Pi systems. Use the simulate endpoint:

```bash
curl -X POST http://localhost:8000/api/simulate-envelope
```

## Troubleshooting

- **Servos not moving**: Check V+ power supply, I2C enabled, wiring
- **Sensor not triggering**: Check GPIO pin, wiring polarity
- **I2C not detected**: Run `sudo i2cdetect -y 1` to verify PCA9685 at 0x40

## License

MIT
