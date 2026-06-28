from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class District(Base):
    __tablename__ = "districts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    min_lat = Column(Float, nullable=False)
    max_lat = Column(Float, nullable=False)
    min_lng = Column(Float, nullable=False)
    max_lng = Column(Float, nullable=False)

class Player(Base):
    __tablename__ = "players"
    id = Column(String, primary_key=True, index=True) # Здесь мы можем хранить UUID или тот же username
    username = Column(String, unique=True, nullable=False, index=True) # Сделали уникальным
    password_hash = Column(String, nullable=False) # Новое поле для хэша пароля
    
    stamina = Column(Integer, default=100)  
    lat = Column(Float, default=54.9850)
    lng = Column(Float, default=73.3200)
    current_district_id = Column(Integer, ForeignKey("districts.id"))
    
    # Характеристики GURPS
    st = Column(Integer, default=10)
    dx = Column(Integer, default=10)
    iq = Column(Integer, default=10)
    ht = Column(Integer, default=10)

    # Навыки GURPS
    skill_hacking = Column(Integer, default=0)       
    skill_lockpicking = Column(Integer, default=0)   
    skill_scouting = Column(Integer, default=0)      

    inventory = relationship("Inventory", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    item_type = Column(String, default="misc")  
    rarity = Column(String, default="common")    

class Inventory(Base):
    __tablename__ = "inventories"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String, ForeignKey("players.id", ondelete="CASCADE"))
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"))
    quantity = Column(Integer, default=1)
    item = relationship("Item")

class PointOfInterest(Base):
    __tablename__ = "points_of_interest"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    poi_type = Column(String, default="cache")  
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)  
    is_looted = Column(Boolean, default=False)  

    # --- ТРЕБОВАНИЯ ДЛЯ МИНИ-ИГРЫ ПО GURPS ---
    required_skill = Column(String, default="scouting")  # hacking, lockpicking, scouting
    difficulty_modifier = Column(Integer, default=0)     # Модификатор сложности задачи
    stamina_cost = Column(Integer, default=10)           # Сколько стамины (FP) тратит попытка

    item = relationship("Item")
