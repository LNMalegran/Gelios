"use client";

import { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMapEvents } from "react-leaflet";
import L from "leaflet";

const API_BASE = "http://localhost:8000";

// Безопасное создание кастомной иконки только в браузере
const createCharacterIcon = () => {
  if (typeof window === "undefined") return null;
  return L.divIcon({
    className: "custom-character-marker",
    html: `<div class="w-4 h-4 bg-emerald-400 rounded-full border-2 border-slate-950 animate-ping absolute"></div>
           <div class="w-4 h-4 bg-emerald-500 rounded-full border-2 border-white relative z-10 shadow-[0_0_10px_#10b981]"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
};

function MapClickHandler({ onMapClick, isMoving }: { onMapClick: (coords: [number, number]) => void; isMoving: boolean }) {
  useMapEvents({
    click(e) {
      if (isMoving) return;
      onMapClick([e.latlng.lat, e.latlng.lng]);
    },
  });
  return null;
}

export default function MapZone() {
  // Флаг полной загрузки клиента для предотвращения краша Next.js SSR
  const [mounted, setMounted] = useState(false);
  
  const [characterPos, setCharacterPos] = useState<[number, number]>([54.9884, 73.3242]);
  const [routePath, setRoutePath] = useState<[number, number][]>([]);
  const [stamina, setStamina] = useState<number>(100);
  const [status, setStatus] = useState<string>("idle");
  const [timeLeft, setTimeLeft] = useState<number>(0);

  // Сигнализируем, что компонент успешно смонтирован в браузере
  useEffect(() => {
    setMounted(true);
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/character/status`);
      if (!res.ok) return;
      const data = await res.json();
      
      // Строгая проверка структуры данных (строховка от пустых ответов)
      if (data && Array.isArray(data.pos) && data.pos.length === 2) {
        setCharacterPos([Number(data.pos[0]), Number(data.pos[1])]);
      }
      if (data && typeof data.stamina === "number") setStamina(data.stamina);
      if (data && typeof data.status === "string") setStatus(data.status);
      if (data && typeof data.time_left === "number") setTimeLeft(data.time_left);
      if (data && Array.isArray(data.route_path)) setRoutePath(data.route_path);
    } catch (err) {
      console.error("Сбой каналов связи с бэкендом ГЕЛИОС:", err);
    }
  };

  const handleMapClick = async (coords: [number, number]) => {
    try {
      const res = await fetch(`${API_BASE}/api/character/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_lat: coords[0], target_lng: coords[1] }),
      });
      
      if (!res.ok) {
        const errData = await res.json();
        alert(errData.detail || "Команда отклонена ядром");
        return;
      }
      
      await fetchStatus();
    } catch (err) {
      console.error("Ошибка передачи директивы движения:", err);
    }
  };

  // Запуск интервала синхронизации только после монтирования
  useEffect(() => {
    if (!mounted) return;
    fetchStatus();
    const interval = setInterval(fetchStatus, 1000);
    return () => clearInterval(interval);
  }, [mounted]);

  // Пока Next.js рендерит страницу на сервере, возвращаем заглушку
  if (!mounted) {
    return (
      <div className="w-full h-[500px] bg-slate-950 border border-cyan-500/20 rounded flex items-center justify-center font-mono text-xs text-cyan-400">
        [ПОДКЛЮЧЕНИЕ К СИСТЕМЕ НАБЛЮДЕНИЯ ГЕЛИОС...]
      </div>
    );
  }

  const icon = createCharacterIcon();
  const validLat = characterPos[0] || 54.9884;
  const validLng = characterPos[1] || 73.3242;

  const formatETA = (sec: number) => {
    if (isNaN(sec) || sec < 0) return "00:00:00";
    const h = Math.floor(sec / 3600).toString().padStart(2, "0");
    const m = Math.floor((sec % 3600) / 60).toString().padStart(2, "0");
    const s = Math.floor(sec % 60).toString().padStart(2, "0");
    return `${h}:${m}:${s}`;
  };

  return (
    <div className="w-full h-full min-h-[500px] relative">
      <MapContainer center={[validLat, validLng]} zoom={13} className="w-full h-full bg-slate-950" zoomControl={false}>
        <TileLayer
          attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        <MapClickHandler onMapClick={handleMapClick} isMoving={status === "moving"} />

        {Array.isArray(routePath) && routePath.length > 0 && (
          <Polyline 
            positions={routePath} 
            pathOptions={{ color: "#06b6d4", weight: 3, opacity: 0.6, dashArray: "4, 8" }} 
          />
        )}

        {icon && (
          <Marker position={[validLat, validLng]} icon={icon}>
            <Popup>
              <div className="p-1 font-mono text-xs bg-slate-900 text-emerald-400">
                <strong>ОПЕРАТИВНИК</strong>
                <p>Статус: {status === "moving" ? "МАРШ-БРОСОК" : "ДИСЛОКАЦИЯ"}</p>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* Интерфейс */}
      <div className="absolute bottom-4 left-4 right-4 z-[1000] bg-slate-900/95 border border-cyan-500/30 p-4 rounded font-mono text-xs flex flex-wrap justify-between items-center gap-4 shadow-[0_0_20px_rgba(6,182,212,0.1)]">
        <div>
          <span className="text-cyan-400 font-bold">// ГЕОПОЗИЦИЯ ОБЪЕКТА:</span>
          <div className="text-slate-300 mt-1">
            LAT: {validLat.toFixed(5)} | LNG: {validLng.toFixed(5)}
          </div>
        </div>

        <div className="w-48">
          <div className="flex justify-between text-emerald-400 mb-1">
            <span>ВЫНОСЛИВОСТЬ:</span>
            <span>{stamina.toFixed(0)}%</span>
          </div>
          <div className="w-full h-2 bg-slate-950 border border-emerald-500/20 rounded overflow-hidden">
            <div className="h-full bg-emerald-500" style={{ width: `${stamina}%` }} />
          </div>
        </div>

        <div className="text-right">
          <span className="text-cyan-400 font-bold">// РАСЧЕТНОЕ ВРЕМЯ (ETA):</span>
          <div className={`text-sm font-bold mt-1 ${status === "moving" ? "text-amber-400 animate-pulse" : "text-slate-400"}`}>
            {status === "moving" ? `ПРИБЫТИЕ ЧЕРЕЗ: ${formatETA(timeLeft)}` : "ОЖИДАНИЕ ПРИКАЗА СЕРВЕРА"}
          </div>
        </div>
      </div>
    </div>
  );
}
