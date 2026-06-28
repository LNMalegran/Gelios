"use client";

import dynamic from "next/dynamic";

// Динамически загружаем карту, отключая рендеринг на сервере (SSR)
const MapZone = dynamic(() => import("../../components/MapZone"), {
  ssr: false,
  loading: () => (  
    <div className="w-full h-full flex items-center justify-center text-cyan-500 font-mono animate-pulse">
      ПОДКЛЮЧЕНИЕ К СПУТНИКАМ ГЕОЛОКАЦИИ...
    </div>
  ),
});

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-cyan-500 p-4 font-mono flex flex-col gap-4">
      {/* Шапка */}
      <header className="border border-cyan-500/30 bg-slate-900/50 p-4 flex justify-between items-center shadow-[0_0_15px_rgba(6,182,212,0.15)]">
        <div className="text-xl font-bold tracking-widest animate-pulse">
          СЕКТОР МОНИТОРИНГА «ГЕЛИОС» // ОМСК
        </div>
        <div className="text-sm text-emerald-400">● СИНХРОНИЗАЦИЯ С БЭКЕНДОМ УСПЕШНА</div>
      </header>

      {/* Контентная зона */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Левая панель */}
        <aside className="border border-cyan-500/20 bg-slate-900/30 p-4 lg:col-span-1 flex flex-col gap-2">
          <h3 className="text-sm uppercase tracking-wider text-cyan-400 border-b border-cyan-500/20 pb-2">Активные Сигналы</h3>
          <div className="text-xs space-y-2 mt-2 text-slate-400">
            <div className="p-2 border border-cyan-500/10 bg-slate-900/40">
              <span className="text-cyan-400">Объект "Авангард"</span><br />
              Центральный округ
            </div>
            <div className="p-2 border border-red-500/20 bg-slate-900/40">
              <span className="text-red-400 font-bold">Аномалия "Нефтяники"</span><br />
              Повышенный радиационный фон
            </div>
          </div>
        </aside>

        {/* Центр: НАША КАРТА */}
        <main className="border border-cyan-500/40 bg-slate-950 lg:col-span-2 relative min-h-[500px] rounded overflow-hidden">
          <MapZone />
        </main>

        {/* Правая панель */}
        <aside className="border border-cyan-500/20 bg-slate-900/30 p-4 lg:col-span-1 flex flex-col">
          <h3 className="text-sm uppercase tracking-wider text-cyan-400 border-b border-cyan-500/20 pb-2">Лог терминала</h3>
          <div className="font-mono text-[11px] text-cyan-600/80 space-y-1 mt-2 overflow-y-auto flex-1">
            <p>[SYSTEM]: Авторизация успешна.</p>
            <p>[MAP]: Загружен темный слой CartoDB.</p>
            <p>[GPS]: Координатная сетка Омска развернута.</p>
          </div>
        </aside>
      </div>
    </div>
  );
}
