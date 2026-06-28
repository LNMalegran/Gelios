import random
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware

import models
from database import SessionLocal, engine

# Создаем таблицы в базе данных на основе моделей
models.Base.metadata.create_all(bind=engine)

# --- НАСТРОЙКИ БЕЗОПАСНОСТИ ---
SECRET_KEY = "OMSK_ZONE_SECRET_ULTRA_KEY_2026"  # В реальном продакшене выносится в .env файл
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # Токен будет жить 2 часа

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- ПРАВИЛА ДЕФОЛТОВ GURPS ---
GURPS_SKILLS_CONFIG = {
    "hacking": {"base_attr": "iq", "default_penalty": -5},
    "lockpicking": {"base_attr": "dx", "default_penalty": -5},
    "scouting": {"base_attr": "iq", "default_penalty": -4}
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ШИФРОВАНИЯ ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- ЗАВИСИМОСТЬ ДЛЯ ЗАЩИТЫ РОУТОВ (Автоматически достает юзера по токену) ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось валидировать токен доступа или сессия истекла",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    player = db.query(models.Player).filter(models.Player.username == username).first()
    if player is None:
        raise credentials_exception
    return player

def is_player_inside_district(lat, lng, district):
    return (district.min_lat <= lat <= district.max_lat) and (district.min_lng <= lng <= district.max_lng)


# --- СИДИНГ БАЗЫ ДАННЫХ ПРИ СТАРТЕ ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    
    # 1. Инициализация Стартового Района
    if not db.query(models.District).filter(models.District.id == 1).first():
        db.add(models.District(id=1, name="Стартовая зона (Омск)", min_lat=54.9800, max_lat=54.9950, min_lng=73.3100, max_lng=73.3400))
    
    # 2. Инициализация базовых предметов
    if not db.query(models.Item).filter(models.Item.id == 1).first():
        db.add(models.Item(id=1, name="Армейский сухпаёк", description="Восстанавливает 30 выносливости (FP)", item_type="consumable", rarity="common"))
    if not db.query(models.Item).filter(models.Item.id == 2).first():
        db.add(models.Item(id=2, name="Тяжелый бронежилет", description="Надежная защита от осколков", item_type="armor", rarity="rare"))
    if not db.query(models.Item).filter(models.Item.id == 3).first():
        db.add(models.Item(id=3, name="Зашифрованный инфопланшет", description="Содержит ценные данные о Зоне", item_type="misc", rarity="epic"))

    # 3. Создаем дефолтного игрока (Кирилл) с безопасным хэшем пароля "12345"
    if not db.query(models.Player).filter(models.Player.username == "kirill").first():
        db.add(models.Player(
            id="player_kirill", 
            username="kirill", 
            password_hash=hash_password("12345"), # Пароль зашифрован!
            stamina=100, current_district_id=1,
            st=10, dx=11, iq=13, ht=11,
            skill_hacking=14, skill_lockpicking=0, skill_scouting=0
        ))

    # 4. Инициализация Точек Интереса (Тайников)
    if not db.query(models.PointOfInterest).filter(models.PointOfInterest.id == 1).first():
        db.add(models.PointOfInterest(id=1, name="Заблокированный армейский терминал", lat=54.9880, lng=73.3220, poi_type="cache", item_id=3, is_looted=False, required_skill="hacking", difficulty_modifier=-1, stamina_cost=15))
    if not db.query(models.PointOfInterest).filter(models.PointOfInterest.id == 2).first():
        db.add(models.PointOfInterest(id=2, name="Старый сейф с механическим замком", lat=54.9830, lng=73.3150, poi_type="cache", item_id=2, is_looted=False, required_skill="lockpicking", difficulty_modifier=0, stamina_cost=10))

    db.commit()
    db.close()
    yield

app = FastAPI(lifespan=lifespan)

# НАСТРОЙКА CORS — разрешаем фронтенду доступ к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], # Адрес нашего Next.js
    allow_credentials=True,
    allow_methods=["*"], # Разрешаем любые методы (GET, POST и т.д.)
    allow_headers=["*"], # Разрешаем любые заголовки (включая наш Authorization Auth)
)


# --- PUDANTIC СХЕМЫ ---
class UserRegister(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class MoveRequest(BaseModel):
    new_lat: float
    new_lng: float

class UseItemRequest(BaseModel):
    item_id: int

class LootPOIRequest(BaseModel):
    poi_id: int


# ==========================================
# 1. ЭНДПОИНТЫ АВТОРИЗАЦИИ (ОТКРЫТЫЕ)
# ==========================================

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(models.Player).filter(models.Player.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже зарегистрирован")
    
    new_player = models.Player(
        id=f"player_{user_data.username}",
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        stamina=100,
        current_district_id=1,
        st=10, dx=10, iq=10, ht=10  # Стартовые средние характеристики GURPS
    )
    db.add(new_player)
    db.commit()
    return {"status": "success", "message": "Регистрация завершена! Добро пожаловать в Систему."}

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.username == form_data.username).first()
    if not player or not verify_password(form_data.password, player.password_hash):
        raise HTTPException(status_code=400, detail="Неверное имя пользователя или пароль")
    
    # Генерируем JWT-токен, закладывая туда имя пользователя
    access_token = create_access_token(data={"sub": player.username})
    return {"access_token": access_token, "token_type": "bearer"}


# ==========================================
# 2. ИГРОВЫЕ ЭНДПОИНТЫ (ЗАЩИЩЕННЫЕ TOKEN)
# ==========================================

@app.get("/player/me/profile")
async def get_player_profile(current_user: models.Player = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "stamina_fp": current_user.stamina,
        "coordinates": [current_user.lat, current_user.lng],
        "attributes": {"ST": current_user.st, "DX": current_user.dx, "IQ": current_user.iq, "HT": current_user.ht},
        "skills": {
            "Hacking (Взлом систем)": f"{current_user.skill_hacking if current_user.skill_hacking > 0 else 'Не изучен (Дефолт)'}",
            "Lockpicking (Взлом замков)": f"{current_user.skill_lockpicking if current_user.skill_lockpicking > 0 else 'Не изучен (Дефолт)'}",
            "Scouting (Наблюдательность)": f"{current_user.skill_scouting if current_user.skill_scouting > 0 else 'Не изучен (Дефолт)'}"
        }
    }

@app.post("/move")
async def move_player(req: MoveRequest, current_user: models.Player = Depends(get_current_user), db: Session = Depends(get_db)):
    district = db.query(models.District).filter(models.District.id == current_user.current_district_id).first()
    if not is_player_inside_district(req.new_lat, req.new_lng, district):
        raise HTTPException(status_code=400, detail="Действие заблокировано: выход за границы сценария")
    if current_user.stamina < 10:
        raise HTTPException(status_code=400, detail="Недостаточно выносливости для перемещения!")
    
    current_user.stamina -= 10
    current_user.lat = req.new_lat
    current_user.lng = req.new_lng
    db.commit()
    return {"status": "Успешное перемещение", "stamina_fp": current_user.stamina, "coordinates": [current_user.lat, current_user.lng]}

@app.get("/player/me/inventory")
async def get_inventory(current_user: models.Player = Depends(get_current_user), db: Session = Depends(get_db)):
    inv = db.query(models.Inventory).filter(models.Inventory.player_id == current_user.id).all()
    return [{"item_id": i.item_id, "name": i.item.name, "quantity": i.quantity, "type": i.item.item_type, "rarity": i.item.rarity} for i in inv]

@app.post("/inventory/use")
async def use_item(req: UseItemRequest, current_user: models.Player = Depends(get_current_user), db: Session = Depends(get_db)):
    entry = db.query(models.Inventory).filter(models.Inventory.player_id == current_user.id, models.Inventory.item_id == req.item_id).first()
    if not entry or entry.quantity <= 0:
        raise HTTPException(status_code=404, detail="У вас нет этого предмета")
    
    if entry.item.id == 1:  # Сухпаёк
        if current_user.stamina >= 100: 
            raise HTTPException(status_code=400, detail="Выносливость уже на максимуме")
        current_user.stamina = min(100, current_user.stamina + 30)
        entry.quantity -= 1
        if entry.quantity == 0: 
            db.delete(entry)
        db.commit()
        return {"status": "success", "message": "Вы использовали сухпаёк", "stamina_fp": current_user.stamina}
    raise HTTPException(status_code=400, detail="Этот предмет нельзя использовать")

@app.get("/poi/nearby")
async def get_nearby_poi(current_user: models.Player = Depends(get_current_user), db: Session = Depends(get_db)):
    all_pois = db.query(models.PointOfInterest).filter(models.PointOfInterest.is_looted == False).all()
    nearby = []
    for poi in all_pois:
        if abs(current_user.lat - poi.lat) <= 0.005 and abs(current_user.lng - poi.lng) <= 0.005:
            nearby.append({"poi_id": poi.id, "name": poi.name, "skill_needed": poi.required_skill, "fp_cost": poi.stamina_cost})
    return {"visible_pois": nearby}

@app.post("/poi/loot")
async def loot_poi(req: LootPOIRequest, current_user: models.Player = Depends(get_current_user), db: Session = Depends(get_db)):
    poi = db.query(models.PointOfInterest).filter(models.PointOfInterest.id == req.poi_id).first()
    if not poi: 
        raise HTTPException(status_code=404, detail="Объект не найден")
    if poi.is_looted: 
        raise HTTPException(status_code=400, detail="Этот объект уже исследован")
    if abs(current_user.lat - poi.lat) > 0.005 or abs(current_user.lng - poi.lng) > 0.005:
        raise HTTPException(status_code=400, detail="Вы слишком далеко от объекта")

    if current_user.stamina < poi.stamina_cost:
        raise HTTPException(status_code=400, detail=f"Вы слишком измотаны. Требуется {poi.stamina_cost} FP")
    
    current_user.stamina -= poi.stamina_cost

    # Расчет кубиков GURPS
    skill_name = poi.required_skill
    player_trained_skill = getattr(current_user, f"skill_{skill_name}")
    is_using_default = False
    
    if player_trained_skill > 0:
        base_target = player_trained_skill
    else:
        is_using_default = True
        config = GURPS_SKILLS_CONFIG[skill_name]
        associated_attribute_value = getattr(current_user, config["base_attr"])
        base_target = associated_attribute_value + config["default_penalty"]

    effective_target = base_target + poi.difficulty_modifier
    d1, d2, d3 = random.randint(1, 6), random.randint(1, 6), random.randint(1, 6)
    total_roll = d1 + d2 + d3
    is_success = total_roll <= effective_target

    if total_roll == 18 or (total_roll == 17 and effective_target <= 15):
        poi.is_looted = True
        db.commit()
        return {"result": "CRITICAL_FAILURE", "roll": f"{d1}+{d2}+{d3} = {total_roll}", "message": "Критический провал! Схрон сломан безвозвратно."}

    if not is_success:
        db.commit()
        return {"result": "FAILURE", "roll": f"{d1}+{d2}+{d3} = {total_roll}", "target": effective_target, "message": f"Неудача! {'(Использован штраф дефолта)' if is_using_default else ''}"}

    if poi.item_id:
        inv_entry = db.query(models.Inventory).filter(models.Inventory.player_id == current_user.id, models.Inventory.item_id == poi.item_id).first()
        if inv_entry: 
            inv_entry.quantity += 1
        else: 
            db.add(models.Inventory(player_id=current_user.id, item_id=poi.item_id, quantity=1))

    poi.is_looted = True
    db.commit()
    return {"result": "SUCCESS", "roll": f"{d1}+{d2}+{d3} = {total_roll}", "reward": poi.item.name if poi.item else "Данные"}

from datetime import datetime, timezone
from fastapi import FastAPI

@app.get("/api/character/status")
def get_character_status():
    # 1. Берем данные из БД (пример статичных данных)
    start_time = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    arrival_time = datetime(2026, 6, 28, 14, 0, 0, tzinfo=timezone.utc) # Идти 2 часа
    
    start_coords = (54.9884, 73.3242)
    dest_coords = (55.0261, 73.2622)
    
    now = datetime.now(timezone.utc)
    
    # 2. Если текущее время больше времени прибытия — он уже пришел
    if now >= arrival_time:
        return {
            "status": "idle",
            "current_coords": dest_coords,
            "stamina": 45
        }
        
    # 3. Если он еще идет — вычисляем точный прогресс математически!
    total_duration = (arrival_time - start_time).total_seconds()
    elapsed_duration = (now - start_time).total_seconds()
    
    progress = elapsed_duration / total_duration # Значение от 0.0 до 1.0
    
    # Лерпим координаты прямо в момент запроса
    current_lat = start_coords[0] + (dest_coords[0] - start_coords[0]) * progress
    current_lng = start_coords[1] + (dest_coords[1] - start_coords[1]) * progress
    
    return {
        "status": "moving",
        "current_coords": (current_lat, current_lng),
        "destination_coords": dest_coords,
        "time_left_seconds": (arrival_time - now).total_seconds()
    }

