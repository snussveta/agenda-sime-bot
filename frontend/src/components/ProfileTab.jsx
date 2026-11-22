import React from 'react';
import { User, School, BookMarked, Calendar, CheckCircle } from 'lucide-react';

export default function ProfileTab({ student, absenceSummary, generalAverage }) {
  const presence = absenceSummary?.presence_percent ?? 100;

  return (
    <div className="space-y-4 pb-24">
      {/* Student ID Card */}
      <div className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white rounded-3xl p-5 shadow-lg space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <span className="text-[11px] font-medium uppercase tracking-wider text-blue-200">
              Карточка учащегося
            </span>
            <h2 className="text-xl font-bold mt-1">{student?.name || 'Ученик'}</h2>
            <p className="text-xs text-blue-100 mt-0.5">{student?.school_name}</p>
          </div>
          {generalAverage && (
            <div className="bg-white/20 backdrop-blur-md px-3 py-1.5 rounded-2xl text-center">
              <span className="text-[10px] uppercase font-bold text-blue-100 block">Балл</span>
              <span className="text-base font-extrabold">{generalAverage}</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/10 text-xs">
          <div>
            <span className="text-blue-200 block text-[10px]">Класс:</span>
            <span className="font-semibold">{student?.classroom || '—'}</span>
          </div>
          <div>
            <span className="text-blue-200 block text-[10px]">Классный руководитель:</span>
            <span className="font-semibold truncate block">{student?.class_master || '—'}</span>
          </div>
          <div>
            <span className="text-blue-200 block text-[10px]">Учебный год:</span>
            <span className="font-semibold">{student?.study_year || '2026-2027'}</span>
          </div>
          <div>
            <span className="text-blue-200 block text-[10px]">Семестр:</span>
            <span className="font-semibold">{student?.current_semester || 1}-й семестр</span>
          </div>
        </div>
      </div>

      {/* Attendance / Absences */}
      <div className="bg-white dark:bg-zinc-900 rounded-2xl p-4 border border-slate-200 dark:border-zinc-800 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-zinc-400">
            Посещаемость
          </h3>
          <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
            {presence}% присутствие
          </span>
        </div>

        <div className="w-full bg-slate-100 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
          <div
            className="bg-emerald-500 h-full rounded-full transition-all"
            style={{ width: `${presence}%` }}
          />
        </div>

        <div className="grid grid-cols-2 gap-2 pt-1 text-xs">
          <div className="p-3 bg-slate-50 dark:bg-zinc-800/60 rounded-xl">
            <span className="text-slate-400 block text-[10px]">Уважительные:</span>
            <span className="text-sm font-bold text-slate-800 dark:text-zinc-200">
              {absenceSummary?.total_motivated ?? 0} ч.
            </span>
          </div>
          <div className="p-3 bg-slate-50 dark:bg-zinc-800/60 rounded-xl">
            <span className="text-slate-400 block text-[10px]">Неуважительные:</span>
            <span className="text-sm font-bold text-rose-500">
              {absenceSummary?.total_unmotivated ?? 0} ч.
            </span>
          </div>
        </div>
      </div>

      {/* Info note */}
      <div className="p-4 bg-blue-50/50 dark:bg-zinc-900 rounded-2xl border border-blue-100 dark:border-zinc-800 text-xs text-slate-500 dark:text-zinc-400 space-y-1">
        <p className="font-semibold text-blue-700 dark:text-blue-400">ℹ️ О приложении</p>
        <p>Неофициальный клиент для системы Agenda SIME MD (Республика Молдова).</p>
        <p>Для выхода или изменения настроек воспользуйтесь ботом Telegram.</p>
      </div>
    </div>
  );
}
