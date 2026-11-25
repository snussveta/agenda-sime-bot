// API client for Agenda SIME Mini App

export function getTg() {
  return typeof window !== 'undefined' ? window.Telegram?.WebApp : null;
}

export function getHeaders() {
  const tg = getTg();
  const initData = tg?.initData || '';
  const userId = tg?.initDataUnsafe?.user?.id || '';

  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${initData}`,
    'X-Telegram-Init-Data': initData,
    'X-Telegram-User-Id': String(userId),
  };
}

async function handleResponse(res) {
  if (!res.ok) {
    let msg = 'Ошибка загрузки данных';
    try {
      const data = await res.json();
      if (data?.detail) msg = data.detail;
    } catch {
      try {
        msg = await res.text();
      } catch {}
    }
    throw new Error(msg);
  }
  return res.json();
}

export async function fetchProfile() {
  const res = await fetch('/api/me', { headers: getHeaders() });
  return handleResponse(res);
}

export async function fetchGrades() {
  const res = await fetch('/api/grades', { headers: getHeaders() });
  return handleResponse(res);
}

export async function fetchHomework() {
  const res = await fetch('/api/homework', { headers: getHeaders() });
  return handleResponse(res);
}

export async function fetchTimetable() {
  const res = await fetch('/api/timetable', { headers: getHeaders() });
  return handleResponse(res);
}

export async function syncData() {
  const res = await fetch('/api/sync', { method: 'POST', headers: getHeaders() });
  return handleResponse(res);
}

export function triggerHaptic(type = 'light') {
  try {
    const tg = getTg();
    if (tg?.HapticFeedback) {
      if (type === 'selection') tg.HapticFeedback.selectionChanged();
      else tg.HapticFeedback.impactOccurred(type);
    }
  } catch (e) {
    // Ignore in non-mobile
  }
}
