const BASE_URL = 'http://127.0.0.1:8000';

export const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const headers = {
    ...((options.headers as Record<string, string>) || {}),
  };

  // Если мы не отправляем Form Data (например, при логине), ставим JSON заголовок
  if (!(options.body instanceof URLSearchParams) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}/${endpoint.replace(/^\//, '')}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Произошла ошибка при запросе к серверу');
  }

  return response.json();
};
