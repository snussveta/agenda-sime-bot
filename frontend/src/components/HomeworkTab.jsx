import React, { useState, useMemo } from 'react';
import {
  Calendar,
  CheckCircle2,
  Circle,
  ChevronLeft,
  ChevronRight,
  ListFilter,
  Sparkles,
  BookOpen,
} from 'lucide-react';
import { triggerHaptic } from '../api';

function getLocalDateStr(date) {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function formatDateDisplay(dateStr) {
  if (!dateStr || dateStr === 'no-date') return 'Без конкретной даты';
  try {
    const [y, m, d] = dateStr.split('-');
    const dateObj = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
    return dateObj.toLocaleDateString('ru-RU', {
      weekday: 'short',
      day: 'numeric',
      month: 'long',
    });
  } catch (e) {
    return dateStr;
  }
}

function normalizeDateStr(rawStr) {
  if (!rawStr) return 'no-date';
  const clean = rawStr.trim();
  // Check YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}/.test(clean)) {
    return clean.slice(0, 10);
  }
  // Check DD.MM.YYYY
  const dmy = clean.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})/);
  if (dmy) {
    const d = dmy[1].padStart(2, '0');
    const m = dmy[2].padStart(2, '0');
    const y = dmy[3];
    return `${y}-${m}-${d}`;
  }
  // Check DD.MM (without year, default to current year)
  const dm = clean.match(/^(\d{1,2})\.(\d{1,2})/);
  if (dm) {
    const year = new Date().getFullYear();
    const d = dm[1].padStart(2, '0');
    const m = dm[2].padStart(2, '0');
    return `${year}-${m}-${d}`;
  }
  return clean;
}

export default function HomeworkTab({ homeworkList, timetable }) {
  const todayStr = useMemo(() => getLocalDateStr(new Date()), []);
  const [selectedDate, setSelectedDate] = useState(todayStr);
  const [viewMode, setViewMode] = useState('by-day'); // 'by-day' | 'all'

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

  // Combine homeworkList + homework topics embedded in timetable lessons
  const allTasks = useMemo(() => {
    const list = [];
    const seen = new Set();

    (homeworkList || []).forEach((hw) => {
      const normDate = normalizeDateStr(hw.due_date_str);
      const key = `${hw.subject}_${normDate}_${hw.description}`;
      if (!seen.has(key)) {
        seen.add(key);
        list.push({
          id: key,
          subject: hw.subject || 'Задание',
          description: hw.description,
          due_date_str: hw.due_date_str,
          dateKey: normDate,
          fromTimetable: false,
        });
      }
    });

    (timetable || []).forEach((lesson) => {
      if (lesson.topic && lesson.topic.trim()) {
        const rawDate = lesson.start_time?.includes('T')
          ? lesson.start_time.split('T')[0]
          : lesson.start_time?.slice(0, 10);
        const normDate = normalizeDateStr(rawDate);
        const key = `${lesson.subject}_${normDate}_${lesson.topic}`;
        if (!seen.has(key)) {
          seen.add(key);
          list.push({
            id: key,
            subject: lesson.subject || 'Урок',
            description: lesson.topic,
            due_date_str: rawDate,
            dateKey: normDate,
            fromTimetable: true,
          });
        }
      }
    });

    return list;
  }, [homeworkList, timetable]);

  // Group by date
  const grouped = useMemo(() => {
    const acc = {};
    allTasks.forEach((task) => {
      const k = task.dateKey;
      if (!acc[k]) acc[k] = [];
      acc[k].push(task);
    });
    return acc;
  }, [allTasks]);

  const datesWithHomework = useMemo(() => {
    return Object.keys(grouped)
      .filter((d) => d !== 'no-date')
      .sort();
  }, [grouped]);

  const changeDateByOffset = (offset) => {
    triggerHaptic('light');
    let baseDate = selectedDate;
    if (baseDate === 'no-date') baseDate = todayStr;
    const [y, m, d] = baseDate.split('-');
    const curr = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
    curr.setDate(curr.getDate() + offset);
    setSelectedDate(getLocalDateStr(curr));
  };

  const goToToday = () => {
    triggerHaptic('medium');
    setSelectedDate(todayStr);
  };

  const isToday = selectedDate === todayStr;
  const currentTasks = grouped[selectedDate] || [];

  // Nearest date with tasks
  const nearestDate = useMemo(() => {
    if (datesWithHomework.length === 0) return null;
    if (datesWithHomework.includes(selectedDate)) return null;
    const future = datesWithHomework.find((d) => d >= selectedDate);
    return future || datesWithHomework[datesWithHomework.length - 1];
  }, [datesWithHomework, selectedDate]);

  return (
    <div className="space-y-3 pb-24">
      {/* Header with Switcher mode */}
      <div className="flex items-center justify-between px-1">
        <h2 className="text-xs font-semibold tracking-wide uppercase text-slate-500 dark:text-zinc-400">
          Домашнее задание ({allTasks.length})
        </h2>
        <div className="flex items-center bg-slate-200/70 dark:bg-zinc-800 p-0.5 rounded-xl text-xs">
          <button
            onClick={() => {
              triggerHaptic('light');
              setViewMode('by-day');
            }}
            className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
              viewMode === 'by-day'
                ? 'bg-white dark:bg-zinc-900 text-blue-600 dark:text-blue-400 shadow-xs'
                : 'text-slate-600 dark:text-zinc-400'
            }`}
          >
            По дням
          </button>
          <button
            onClick={() => {
              triggerHaptic('light');
              setViewMode('all');
            }}
            className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
              viewMode === 'all'
                ? 'bg-white dark:bg-zinc-900 text-blue-600 dark:text-blue-400 shadow-xs'
                : 'text-slate-600 dark:text-zinc-400'
            }`}
          >
            Все ({allTasks.length})
          </button>
        </div>
      </div>

      {/* Date Switcher in 'by-day' mode */}
      {viewMode === 'by-day' && (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-3 border border-slate-200 dark:border-zinc-800 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <button
              onClick={() => changeDateByOffset(-1)}
              className="flex items-center px-2.5 py-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-zinc-800 active:scale-95 text-slate-700 dark:text-zinc-300 text-xs font-medium transition-all"
            >
              <ChevronLeft className="w-4 h-4 mr-0.5" />
              Вчера
            </button>

            <div className="text-center">
              <div className="text-xs font-bold text-slate-900 dark:text-zinc-100 flex items-center justify-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-blue-500" />
                <span className="capitalize">{formatDateDisplay(selectedDate)}</span>
              </div>
              {isToday ? (
                <span className="inline-block text-[10px] bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 font-bold px-2 py-0.2 rounded-md mt-0.5">
                  Сегодня
                </span>
              ) : (
                <span className="text-[10px] text-slate-400 block mt-0.5">{selectedDate}</span>
              )}
            </div>

            <button
              onClick={() => changeDateByOffset(1)}
              className="flex items-center px-2.5 py-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-zinc-800 active:scale-95 text-slate-700 dark:text-zinc-300 text-xs font-medium transition-all"
            >
              Завтра
              <ChevronRight className="w-4 h-4 ml-0.5" />
            </button>
          </div>

          {/* Quick Date Chips with task counts */}
          {datesWithHomework.length > 0 && (
            <div className="flex items-center space-x-1.5 overflow-x-auto py-1 text-xs">
              {datesWithHomework.map((d) => {
                const count = grouped[d]?.length || 0;
                const isSel = d === selectedDate;
                const isTod = d === todayStr;
                return (
                  <button
                    key={d}
                    onClick={() => {
                      triggerHaptic('light');
                      setSelectedDate(d);
                    }}
                    className={`px-2.5 py-1 rounded-xl text-xs font-semibold whitespace-nowrap transition-all active:scale-95 flex items-center gap-1 shrink-0 ${
                      isSel
                        ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/25'
                        : isTod
                        ? 'bg-blue-50 dark:bg-zinc-800 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-zinc-700'
                        : 'bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-zinc-400'
                    }`}
                  >
                    <span>{d.slice(5)}</span>
                    <span
                      className={`text-[10px] px-1 rounded-full ${
                        isSel ? 'bg-white/30 text-white' : 'bg-slate-200 dark:bg-zinc-700 text-slate-700 dark:text-zinc-300'
                      }`}
                    >
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {!isToday && (
            <div className="flex justify-center pt-1 border-t border-slate-100 dark:border-zinc-800/80">
              <button
                onClick={goToToday}
                className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
              >
                Вернуться на Сегодня ({formatDateDisplay(todayStr)})
              </button>
            </div>
          )}
        </div>
      )}

      {/* Homework List */}
      {viewMode === 'by-day' ? (
        currentTasks.length === 0 ? (
          <div className="bg-white dark:bg-zinc-900 rounded-2xl p-8 text-center border border-slate-200 dark:border-zinc-800 shadow-sm space-y-3">
            <p className="text-sm font-semibold text-slate-700 dark:text-zinc-300">
              🎉 На этот день заданий нет
            </p>
            <p className="text-xs text-slate-400">
              {isToday ? 'На сегодня домашняя работа не запланирована.' : 'Отдыхайте или проверьте другие дни.'}
            </p>
            <div className="flex flex-wrap gap-2 justify-center pt-2">
              {nearestDate && (
                <button
                  onClick={() => {
                    triggerHaptic('light');
                    setSelectedDate(nearestDate);
                  }}
                  className="px-3.5 py-2 bg-blue-50 dark:bg-zinc-800 text-blue-600 dark:text-blue-400 text-xs font-semibold rounded-xl border border-blue-100 dark:border-zinc-700 active:scale-95 transition-all"
                >
                  Задания на {formatDateDisplay(nearestDate)} →
                </button>
              )}
              {allTasks.length > 0 && (
                <button
                  onClick={() => {
                    triggerHaptic('light');
                    setViewMode('all');
                  }}
                  className="px-3.5 py-2 bg-slate-100 dark:bg-zinc-800 text-slate-700 dark:text-zinc-300 text-xs font-semibold rounded-xl active:scale-95 transition-all"
                >
                  Показать все ({allTasks.length})
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {currentTasks.map((hw) => {
              const isDone = !!completed[hw.id];
              return (
                <div
                  key={hw.id}
                  onClick={() => toggleDone(hw.id)}
                  className={`p-3.5 rounded-2xl border transition-all cursor-pointer ${
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
                        <h3
                          className={`text-sm font-semibold ${
                            isDone ? 'line-through text-slate-400 dark:text-zinc-500' : 'text-slate-900 dark:text-zinc-100'
                          }`}
                        >
                          {hw.subject}
                        </h3>
                        {hw.fromTimetable && (
                          <span className="flex items-center text-[10px] font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/40 px-1.5 py-0.5 rounded-md border border-blue-200 dark:border-blue-900">
                            Из урока
                          </span>
                        )}
                      </div>
                      <p
                        className={`text-xs leading-relaxed ${
                          isDone ? 'line-through text-slate-400 dark:text-zinc-500' : 'text-slate-600 dark:text-zinc-300'
                        }`}
                      >
                        {hw.description}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )
      ) : (
        /* 'all' mode: group by date */
        <div className="space-y-4">
          {Object.keys(grouped).length === 0 ? (
            <div className="bg-white dark:bg-zinc-900 rounded-2xl p-8 text-center border border-slate-200 dark:border-zinc-800">
              <p className="text-sm font-semibold text-slate-700 dark:text-zinc-300">
                🎉 Все задания выполнены!
              </p>
              <p className="text-xs text-slate-400 mt-1">
                В дневнике нет активных заданий
              </p>
            </div>
          ) : (
            Object.keys(grouped)
              .sort()
              .map((dateKey) => (
                <div key={dateKey} className="space-y-2">
                  <div className="text-xs font-bold text-blue-600 dark:text-blue-400 px-1 flex items-center justify-between">
                    <span>🗓 {formatDateDisplay(dateKey)}</span>
                    <span className="text-[11px] text-slate-400 font-normal">
                      {grouped[dateKey].length} зад.
                    </span>
                  </div>
                  <div className="space-y-2">
                    {grouped[dateKey].map((hw) => {
                      const isDone = !!completed[hw.id];
                      return (
                        <div
                          key={hw.id}
                          onClick={() => toggleDone(hw.id)}
                          className={`p-3.5 rounded-2xl border transition-all cursor-pointer ${
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
                                <h3
                                  className={`text-sm font-semibold ${
                                    isDone
                                      ? 'line-through text-slate-400 dark:text-zinc-500'
                                      : 'text-slate-900 dark:text-zinc-100'
                                  }`}
                                >
                                  {hw.subject}
                                </h3>
                                {hw.due_date_str && (
                                  <span className="flex items-center text-[10px] font-medium text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-1.5 py-0.5 rounded-md border border-amber-200 dark:border-amber-800">
                                    {hw.due_date_str}
                                  </span>
                                )}
                              </div>
                              <p
                                className={`text-xs leading-relaxed ${
                                  isDone
                                    ? 'line-through text-slate-400 dark:text-zinc-500'
                                    : 'text-slate-600 dark:text-zinc-300'
                                }`}
                              >
                                {hw.description}
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))
          )}
        </div>
      )}
    </div>
  );
}
