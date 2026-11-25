// API client for Agenda SIME Mini App

export function getTg() {
  return typeof window !== 'undefined' ? window.Telegram?.WebApp : null;
}

export function getHeaders() {
  const tg = getTg();
  const initData = tg?.initData || '';

  // Extract URL parameters if passed via button (?uid=...&token=...)
  const urlParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
  const urlUid = urlParams?.get('uid') || urlParams?.get('user_id');
  const urlToken = urlParams?.get('token') || urlParams?.get('auth_token');

  if (urlUid) {
    try { sessionStorage.setItem('sime_uid', urlUid); } catch {}
  }
  if (urlToken) {
    try { sessionStorage.setItem('sime_token', urlToken); } catch {}
  }
  if (initData) {
    try { sessionStorage.setItem('sime_init_data', initData); } catch {}
  }

  let storedUid = '';
  let storedToken = '';
  let storedInitData = '';
  try {
    storedUid = sessionStorage.getItem('sime_uid') || '';
    storedToken = sessionStorage.getItem('sime_token') || '';
    storedInitData = sessionStorage.getItem('sime_init_data') || '';
  } catch {}

  const finalInitData = initData || storedInitData || '';
  const finalUserId = String(tg?.initDataUnsafe?.user?.id || urlUid || storedUid || '');
  const finalToken = urlToken || storedToken || '';

  const headers = {
    'Content-Type': 'application/json',
  };

  if (finalInitData) {
    headers['Authorization'] = `Bearer ${finalInitData}`;
    headers['X-Telegram-Init-Data'] = finalInitData;
  }
  if (finalUserId) {
    headers['X-Telegram-User-Id'] = finalUserId;
  }
  if (finalToken) {
    headers['X-Telegram-Auth-Token'] = finalToken;
  }

  return headers;
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
