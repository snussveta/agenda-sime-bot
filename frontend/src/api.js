// API client for Agenda SIME Mini App

const tg = window.Telegram?.WebApp;

export function getHeaders() {
  const initData = tg?.initData || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${initData}`,
    'X-Telegram-Init-Data': initData,
  };
}

export async function fetchProfile() {
  const res = await fetch('/api/me', { headers: getHeaders() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchGrades() {
  const res = await fetch('/api/grades', { headers: getHeaders() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchHomework() {
  const res = await fetch('/api/homework', { headers: getHeaders() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchTimetable() {
  const res = await fetch('/api/timetable', { headers: getHeaders() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function syncData() {
  const res = await fetch('/api/sync', { method: 'POST', headers: getHeaders() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function triggerHaptic(type = 'light') {
  try {
    if (tg?.HapticFeedback) {
      if (type === 'selection') tg.HapticFeedback.selectionChanged();
      else tg.HapticFeedback.impactOccurred(type);
    }
  } catch (e) {
    // Ignore in non-mobile
  }
}
