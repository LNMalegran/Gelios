from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import httpx

app = FastAPI()

# КРИТИЧЕСКИ ВАЖНО: Разрешаем фронтенду слать запросы
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Адрес твоего Next.js приложения
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# База данных оперативника в памяти сервера
CHARACTER_DB = {
    "pos": [54.9884, 73.3242],        # [Широта, Долгота] (Центр Омска)
    "stamina": 100.0,
    "last_stamina_update": datetime.now(timezone.utc),
    "status": "idle",                 # "idle" или "moving"
    "route_path": [],                 # Координаты улиц от OSRM
    "start_time": None,
    "arrival_time": None,
    "total_duration": 0.0
}

class MoveRequest(BaseModel):
    target_lat: float
    target_lng: float

def refresh_stamina():
    now = datetime.now(timezone.utc)
    if CHARACTER_DB["status"] == "idle":
        elapsed = (now - CHARACTER_DB["last_stamina_update"]).total_seconds()
        CHARACTER_DB["stamina"] = min(100.0, CHARACTER_DB["stamina"] + (elapsed * 0.1)) # 0.1% в сек
    CHARACTER_DB["last_stamina_update"] = now

@app.get("/api/character/status")
async def get_status():
    refresh_stamina()
    now = datetime.now(timezone.utc)
    
    if CHARACTER_DB["status"] == "idle" or not CHARACTER_DB["route_path"]:
        return {
            "status": "idle",
            "pos": CHARACTER_DB["pos"],
            "stamina": round(CHARACTER_DB["stamina"], 1),
            "time_left": 0,
            "route_path": []
        }
        
    if now >= CHARACTER_DB["arrival_time"]:
        CHARACTER_DB["status"] = "idle"
        CHARACTER_DB["pos"] = CHARACTER_DB["route_path"][-1]
        CHARACTER_DB["route_path"] = []
        return {
            "status": "idle",
            "pos": CHARACTER_DB["pos"],
            "stamina": round(CHARACTER_DB["stamina"], 1),
            "time_left": 0,
            "route_path": []
        }
        
    # Расчет текущей точки на основе пройденного времени
    total_sec = CHARACTER_DB["total_duration"]
    elapsed_sec = (now - CHARACTER_DB["start_time"]).total_seconds()
    progress = min(1.0, max(0.0, elapsed_sec / total_sec))
    
    path_len = len(CHARACTER_DB["route_path"])
    current_index = min(path_len - 1, int(progress * (path_len - 1)))
    current_pos = CHARACTER_DB["route_path"][current_index]
    CHARACTER_DB["pos"] = current_pos
    
    time_left = max(0, int((CHARACTER_DB["arrival_time"] - now).total_seconds()))
    
    return {
        "status": "moving",
        "pos": current_pos,
        "stamina": round(CHARACTER_DB["stamina"], 1),
        "time_left": time_left,
        "route_path": CHARACTER_DB["route_path"]
    }

@app.post("/api/character/move")
async def start_movement(req: MoveRequest):
    refresh_stamina()
    
    if CHARACTER_DB["status"] == "moving":
        raise HTTPException(status_code=400, detail="Оперативник уже в пути")
        
    current_pos = CHARACTER_DB["pos"]
    
    osrm_url = f"https://router.project-osrm.org/route/v1/foot/{current_pos[1]},{current_pos[0]};{req.target_lng},{req.target_lat}?overview=full&geometries=geojson"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(osrm_url)
            data = response.json()
        except Exception:
            raise HTTPException(status_code=502, detail="Ошибка навигации OSRM")
            
    if "routes" not in data or len(data["routes"]) == 0:
        raise HTTPException(status_code=400, detail="Маршрут не найден")
        
    route = data["routes"][0]
    raw_coords = route["geometry"]["coordinates"]
    route_path = [[coord[1], coord[0]] for coord in raw_coords]
    
    stamina_cost = route["distance"] / 20.0
    if CHARACTER_DB["stamina"] < stamina_cost:
        raise HTTPException(status_code=400, detail="Недостаточно выносливости")
        
    CHARACTER_DB["stamina"] -= stamina_cost
    CHARACTER_DB["last_stamina_update"] = datetime.now(timezone.utc)
    
    # Модификатор времени: 10.0 означает, что персонаж идет в 10 раз быстрее реального пешехода
    TIME_SPEED_MODIFIER = 10.0 
    simulated_duration = max(5.0, route["duration"] / TIME_SPEED_MODIFIER)
    
    now = datetime.now(timezone.utc)
    CHARACTER_DB["status"] = "moving"
    CHARACTER_DB["route_path"] = route_path
    CHARACTER_DB["start_time"] = now
    CHARACTER_DB["arrival_time"] = now + timedelta(seconds=simulated_duration)
    CHARACTER_DB["total_duration"] = simulated_duration
    
    return {"status": "started", "time_left": int(simulated_duration)}
