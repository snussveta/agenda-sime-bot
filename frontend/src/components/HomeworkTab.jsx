import React, { useState, useEffect } from 'react';
import { Calendar, CheckCircle2, Circle } from 'lucide-react';
import { triggerHaptic } from '../api';

export default function HomeworkTab({ homeworkList }) {
  const [completed, setCompleted] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('sime_hw_done') || '{}');
    } catch {
      return {};
    }
  });

  const toggleDone = (key) => {
    triggerHaptic('light');
    setCompleted((prev) => {
      const next = { ...prev, [key]: !prev[key] };
      localStorage.setItem('sime_hw_done', JSON.stringify(next));
      return next;
    });
  };

  const items = homeworkList || [];

  return (
    <div className="space-y-3 pb-24">
      <div className="flex items-center justify-between px-1">
        <h2 className="text-xs font-semibold tracking-wide uppercase text-slate-500 dark:text-zinc-400">
          Задания ({items.length})
        </h2>
      </div>

      {items.length === 0 ? (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-8 text-center border border-slate-200 dark:border-zinc-800">
          <p className="text-sm font-medium text-slate-700 dark:text-zinc-300">
            🎉 Все задания выполнены!
          </p>
          <p className="text-xs text-slate-400 mt-1">
            На ближайшие дни домашней работы нет
          </p>
        </div>
      ) : (
        items.map((hw, idx) => {
          const key = `${hw.subject}_${hw.due_date_str}_${idx}`;
          const isDone = !!completed[key];

          return (
            <div
              key={key}
              onClick={() => toggleDone(key)}
              className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                isDone
                  ? 'bg-slate-100/60 dark:bg-zinc-900/40 border-slate-200 dark:border-zinc-800/50 opacity-60'
                  : 'bg-white dark:bg-zinc-900 border-slate-200 dark:border-zinc-800 shadow-sm'
              }`}
            >
              <div className="flex items-start space-x-3">
                <button className="mt-0.5 text-blue-600 dark:text-blue-400 shrink-0">
                  {isDone ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  ) : (
                    <Circle className="w-5 h-5 text-slate-300 dark:text-zinc-600" />
                  )}
                </button>
                <div className="space-y-1 flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className={`text-sm font-semibold ${isDone ? 'line-through text-slate-400 dark:text-zinc-500' : 'text-slate-900 dark:text-zinc-100'}`}>
                      {hw.subject}
                    </h3>
                    {hw.due_date_str && (
                      <span className="flex items-center text-[11px] font-medium text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded-md border border-amber-200 dark:border-amber-800">
                        <Calendar className="w-3 h-3 mr-1" />
                        {hw.due_date_str}
                      </span>
                    )}
                  </div>
                  <p className={`text-xs leading-relaxed ${isDone ? 'line-through text-slate-400 dark:text-zinc-500' : 'text-slate-600 dark:text-zinc-300'}`}>
                    {hw.description}
                  </p>
                </div>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
