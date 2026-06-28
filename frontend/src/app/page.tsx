'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '../utils/api';

export default function AuthPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(false);

    if (!username || !password) {
      setError('ЗАПОЛНИТЕ ВСЕ ИДЕНТИФИКАЦИОННЫЕ ПОЛЯ.');
      return;
    }

    setLoading(true);
    try {
      if (isLogin) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const data = await apiFetch('/login', {
          method: 'POST',
          body: formData,
        });
        localStorage.setItem('token', data.access_token);
        router.push('/dashboard');
      } else {
        await apiFetch('/register', {
          method: 'POST',
          body: JSON.stringify({ username, password }),
        });
        setMessage('РЕГИСТРАЦИЯ УСПЕШНО ЗАВЕРШЕНА. ВОЙДИТЕ В СИСТЕМУ.');
        setIsLogin(true);
      }
    } catch (err: any) {
      setError(err.message || 'ОШИБКА СИНХРОНИЗАЦИИ С СЕРВЕРОМ.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-sky-950/40 via-gray-950 to-black flex flex-col items-center justify-center p-4 font-mono select-none overflow-hidden">
      
      {/* Фоновая сетка для киберпанк-атмосферы */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293710_1px,transparent_1px),linear-gradient(to_bottom,#1f293710_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Главное окно Системы */}
      <div className="relative w-full max-w-lg bg-slate-950/80 backdrop-blur-md border border-sky-500/40 rounded-sm p-8 shadow-[0_0_30px_rgba(14,165,233,0.15)] animate-pulse-slow">
        
        {/* Высокотехнологичные угловые маркеры интерфейса */}
        <div className="absolute -top-[2px] -left-[2px] w-4 h-4 border-t-2 border-l-2 border-sky-400" />
        <div className="absolute -top-[2px] -right-[2px] w-4 h-4 border-t-2 border-r-2 border-sky-400" />
        <div className="absolute -bottom-[2px] -left-[2px] w-4 h-4 border-b-2 border-l-2 border-sky-400" />
        <div className="absolute -bottom-[2px] -right-[2px] w-4 h-4 border-b-2 border-r-2 border-sky-400" />

        {/* Кнопки управления окном в правом верхнем углу */}
        <div className="absolute top-3 right-4 flex space-x-1.5 opacity-60">
          <div className="w-3 h-0.5 bg-sky-400 mt-2" />
          <div className="w-2.5 h-2.5 border border-sky-400" />
          <div className="w-2.5 h-2.5 relative flex items-center justify-center">
            <span className="absolute text-[10px] text-sky-400 -top-1">×</span>
          </div>
        </div>

        {/* Заголовок сценария */}
        <div className="text-center mb-8 border-b border-sky-500/20 pb-4">
          <h1 className="text-sky-400 text-xl font-bold tracking-widest uppercase sm:text-2xl drop-shadow-[0_0_8px_rgba(56,189,248,0.5)]">
            {isLogin ? '[ИНИЦИАЛИЗАЦИЯ ПОЛЬЗОВАТЕЛЯ]' : '[РЕГИСТРАЦИЯ НОВОЙ СУЩНОСТИ]'}
          </h1>
          <p className="text-xs text-sky-500/60 mt-1.5 tracking-wider">
            ПОДКЛЮЧЕНИЕ К СЕТИ ОМСКОЙ ЗОНЫ // ВЕРСИЯ 2.6
          </p>
        </div>

        {/* Уведомления */}
        {error && (
          <div className="mb-6 bg-red-950/40 border border-red-500/50 text-red-400 text-xs p-3 text-center tracking-wide uppercase rounded-sm">
            [ВНИМАНИЕ: {error}]
          </div>
        )}
        {message && (
          <div className="mb-6 bg-emerald-950/40 border border-emerald-500/50 text-emerald-400 text-xs p-3 text-center tracking-wide uppercase rounded-sm">
            [{message}]
          </div>
        )}

        {/* Форма ввода данных */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-xs font-semibold text-sky-400/80 uppercase tracking-widest mb-2">
              Идентификатор (Позывной):
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Введите имя..."
              className="w-full bg-slate-900/60 border border-sky-500/30 rounded-sm px-4 py-2.5 text-sky-200 text-sm focus:outline-none focus:border-sky-400 focus:shadow-[0_0_10px_rgba(14,165,233,0.2)] transition-all placeholder-sky-800/60"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-sky-400/80 uppercase tracking-widest mb-2">
              Ключ доступа (Пароль):
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-900/60 border border-sky-500/30 rounded-sm px-4 py-2.5 text-sky-200 text-sm focus:outline-none focus:border-sky-400 focus:shadow-[0_0_10px_rgba(14,165,233,0.2)] transition-all placeholder-sky-800/60"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 bg-gradient-to-r from-sky-600/20 via-sky-500/30 to-sky-600/20 hover:from-sky-500/40 hover:to-sky-500/40 text-sky-300 font-bold py-3 px-4 rounded-sm border border-sky-400/50 tracking-widest uppercase text-xs transition-all duration-300 active:scale-[0.99] disabled:opacity-50 shadow-[inset_0_0_8px_rgba(56,189,248,0.2)] hover:shadow-[0_0_15px_rgba(14,165,233,0.4)]"
          >
            {loading ? 'СИНХРОНИЗАЦИЯ...' : isLogin ? 'УСТАНОВИТЬ СОЕДИНЕНИЕ' : 'СОЗДАТЬ ПРОФИЛЬ'}
          </button>
        </form>

        {/* Переключатель Вход / Регистрация */}
        <div className="mt-6 text-center border-t border-sky-500/10 pt-4">
          <button
            type="button"
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
              setMessage('');
            }}
            className="text-xs text-sky-500/70 hover:text-sky-400 transition-colors tracking-wide underline decoration-sky-500/30 underline-offset-4"
          >
            {isLogin ? 'Впервые в секторе? Регистрация устройства' : 'Уже в базе данных? Авторизоваться'}
          </button>
        </div>

      </div>
    </div>
  );
}
