import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Navigation from './components/Navigation';
import GradesTab from './components/GradesTab';
import HomeworkTab from './components/HomeworkTab';
import TimetableTab from './components/TimetableTab';
import ProfileTab from './components/ProfileTab';
import { fetchProfile, fetchGrades, fetchHomework, fetchTimetable, syncData } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('grades');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);

  const [profile, setProfile] = useState(null);
  const [gradesData, setGradesData] = useState(null);
  const [homeworkList, setHomeworkList] = useState([]);
  const [timetable, setTimetable] = useState([]);

  // Initialize Telegram WebApp
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      if (tg.setHeaderColor) tg.setHeaderColor('#ffffff');
    }
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [profRes, gradesRes, hwRes, ttRes] = await Promise.all([
        fetchProfile().catch(() => null),
        fetchGrades().catch(() => null),
        fetchHomework().catch(() => null),
        fetchTimetable().catch(() => null),
      ]);

      if (profRes) setProfile(profRes);
      if (gradesRes) setGradesData(gradesRes);
      if (hwRes?.homework) setHomeworkList(hwRes.homework);
      if (ttRes?.timetable) setTimetable(ttRes.timetable);

      if (!profRes && !gradesRes) {
        setError('Не удалось загрузить данные. Убедитесь, что вы авторизовались через бота /start.');
      }
    } catch (err) {
      setError('Ошибка соединения с сервером.');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    if (syncing) return;
    setSyncing(true);
    try {
      await syncData();
      await loadAllData();
    } catch (err) {
      console.error('Sync failed', err);
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <div className="w-12 h-12 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-slate-600 dark:text-zinc-400">
          Загрузка дневника...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center">
        <div className="w-16 h-16 bg-rose-100 dark:bg-rose-950/40 text-rose-500 rounded-2xl flex items-center justify-center text-2xl mb-4">
          ⚠️
        </div>
        <h2 className="text-base font-bold text-slate-800 dark:text-zinc-100 mb-2">
          Требуется вход
        </h2>
        <p className="text-xs text-slate-500 dark:text-zinc-400 mb-6 max-w-xs">
          {error}
        </p>
        <button
          onClick={loadAllData}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all active:scale-95"
        >
          Повторить попытку
        </button>
      </div>
    );
  }

  const student = profile?.student;
  const generalAvg = gradesData?.general_average || profile?.general_average;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-zinc-950">
      <Header
        student={student}
        generalAverage={generalAvg}
        onSync={handleSync}
        syncing={syncing}
      />

      <main className="flex-1 p-4 max-w-md mx-auto w-full">
        {activeTab === 'grades' && (
          <GradesTab
            gradesData={gradesData}
            recentGrades={gradesData?.recent_grades}
          />
        )}
        {activeTab === 'homework' && (
          <HomeworkTab homeworkList={homeworkList} />
        )}
        {activeTab === 'timetable' && (
          <TimetableTab timetable={timetable} />
        )}
        {activeTab === 'profile' && (
          <ProfileTab
            student={student}
            absenceSummary={profile?.absence_summary}
            generalAverage={generalAvg}
          />
        )}
      </main>

      <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  );
}
