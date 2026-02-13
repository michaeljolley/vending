"""
FastAPI backend for the Valentine's Candy Vending Machine.
"""
import json
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Set

from servo_controller import get_servo_controller
from sensor import init_sensor


# Load config
config_path = Path(__file__).parent.parent / "config.json"
with open(config_path) as f:
    config = json.load(f)


# Credit system
class CreditManager:
    def __init__(self):
        self.credits = 0
        self.websockets: Set[WebSocket] = set()
        self._loop = None
    
    def set_event_loop(self, loop):
        self._loop = loop
    
    def add_credits(self, amount: int = 1):
        self.credits += amount
        print(f"Credits added: {amount}. Total: {self.credits}")
        self._schedule_broadcast()
    
    def spend_credits(self, amount: int = 1) -> bool:
        if self.credits >= amount:
            self.credits -= amount
            print(f"Credits spent: {amount}. Remaining: {self.credits}")
            self._schedule_broadcast()
            return True
        return False
    
    def _schedule_broadcast(self):
        """Schedule broadcast on the main event loop (thread-safe)."""
        if self._loop:
            self._loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self.broadcast_state())
            )
    
    def get_credits(self) -> int:
        return self.credits
    
    async def broadcast_state(self):
        """Send current state to all connected WebSocket clients."""
        if not self.websockets:
            return
        
        servo = get_servo_controller()
        state = {
            "type": "state",
            "credits": self.credits,
            "slots": servo.get_enabled_slots(),
            "busy": servo.is_busy()
        }
        
        dead_sockets = set()
        for ws in self.websockets:
            try:
                await ws.send_json(state)
            except Exception:
                dead_sockets.add(ws)
        
        self.websockets -= dead_sockets
    
    def register_websocket(self, ws: WebSocket):
        self.websockets.add(ws)
    
    def unregister_websocket(self, ws: WebSocket):
        self.websockets.discard(ws)


credit_manager = CreditManager()


def on_envelope_detected():
    """Callback when the break-beam sensor is triggered."""
    credits_per_envelope = config["credits"].get("per_envelope", 1)
    credit_manager.add_credits(credits_per_envelope)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Valentine's Candy Machine...")
    # Set event loop for thread-safe callbacks
    credit_manager.set_event_loop(asyncio.get_running_loop())
    sensor = init_sensor(on_trigger=on_envelope_detected)
    sensor.start()
    yield
    # Shutdown
    print("Shutting down...")
    sensor.stop()
    sensor.cleanup()
    get_servo_controller().stop_all()


app = FastAPI(title="Valentine's Candy Machine", lifespan=lifespan)


# Serve static files (frontend)
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def root():
    """Serve the main UI."""
    return FileResponse(frontend_path / "index.html")


@app.get("/api/state")
async def get_state():
    """Get current machine state."""
    servo = get_servo_controller()
    return {
        "credits": credit_manager.get_credits(),
        "slots": servo.get_enabled_slots(),
        "busy": servo.is_busy()
    }


@app.post("/api/dispense/{slot_id}")
async def dispense(slot_id: int):
    """Dispense candy from a slot."""
    servo = get_servo_controller()
    
    if servo.is_busy():
        raise HTTPException(status_code=409, detail="Machine is busy")
    
    cost = config["credits"].get("cost_per_dispense", 1)
    if not credit_manager.spend_credits(cost):
        raise HTTPException(status_code=400, detail="Not enough credits")
    
    # Broadcast busy state
    await credit_manager.broadcast_state()
    
    # Run dispense in background to not block
    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(None, servo.dispense, slot_id)
    
    if not success:
        # Refund credits if dispense failed
        credit_manager.add_credits(cost)
        raise HTTPException(status_code=500, detail="Dispense failed")
    
    # Broadcast updated state after dispense
    await credit_manager.broadcast_state()
    
    return {"success": True, "credits_remaining": credit_manager.get_credits()}


@app.post("/api/simulate-envelope")
async def simulate_envelope():
    """Simulate an envelope drop for testing."""
    from sensor import get_sensor
    get_sensor().simulate_trigger()
    return {"success": True}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time state updates."""
    await websocket.accept()
    credit_manager.register_websocket(websocket)
    
    try:
        # Send initial state
        await credit_manager.broadcast_state()
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                # Handle any incoming messages if needed
            except WebSocketDisconnect:
                break
    finally:
        credit_manager.unregister_websocket(websocket)


if __name__ == "__main__":
    import uvicorn
    server_config = config.get("server", {})
    uvicorn.run(
        app,
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000)
    )
