import React from 'react';
import { RefreshCw, GraduationCap } from 'lucide-react';
import { triggerHaptic } from '../api';

export default function Header({ student, generalAverage, onSync, syncing }) {
  const getBadgeColor = (avg) => {
    if (!avg) return 'bg-slate-200 dark:bg-zinc-800 text-slate-700 dark:text-zinc-300';
    if (avg >= 9.0) return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30';
    if (avg >= 7.0) return 'bg-blue-500/15 text-blue-700 dark:text-blue-400 border border-blue-500/30';
    if (avg >= 5.0) return 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30';
    return 'bg-rose-500/15 text-rose-700 dark:text-rose-400 border border-rose-500/30';
  };

  const handleSyncClick = () => {
    triggerHaptic('medium');
    onSync();
  };

  return (
    <header className="sticky top-0 z-30 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md border-b border-slate-200 dark:border-zinc-800 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="w-10 h-10 rounded-full bg-blue-600/10 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div className="overflow-hidden">
            <h1 className="font-semibold text-sm truncate text-slate-900 dark:text-white">
              {student?.name || 'Загрузка...'}
            </h1>
            <p className="text-xs text-slate-500 dark:text-zinc-400 truncate">
              {student?.school_name ? `${student.school_name} (${student.classroom || ''})` : 'Agenda SIME MD'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          {generalAverage && (
            <div className={`px-2.5 py-1 rounded-full text-xs font-bold tracking-tight ${getBadgeColor(generalAverage)}`}>
              ⭐ {generalAverage}
            </div>
          )}
          <button
            onClick={handleSyncClick}
            disabled={syncing}
            className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 text-slate-600 dark:text-zinc-400 active:scale-95 transition-all"
            title="Синхронизировать"
          >
            <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin text-blue-500' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
}
