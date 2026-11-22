import React, { useState, useMemo } from 'react';
import { Clock, MapPin, User, BookOpen, ChevronLeft, ChevronRight, Calendar, Sparkles } from 'lucide-react';
import { triggerHaptic } from '../api';

function getLocalDateStr(date) {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function formatDateDisplay(dateStr) {
  if (!dateStr) return '';
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

export default function TimetableTab({ timetable }) {
  const todayStr = useMemo(() => getLocalDateStr(new Date()), []);
  const [selectedDate, setSelectedDate] = useState(todayStr);

  // Group and sort lessons strictly by date and lesson order (1, 2, 3...)
  const grouped = useMemo(() => {
    const acc = {};
    (timetable || []).forEach((rawLesson) => {
      let dateKey = todayStr;
      if (rawLesson.start_time) {
        if (rawLesson.start_time.includes('T')) {
          dateKey = rawLesson.start_time.split('T')[0];
        } else {
          dateKey = rawLesson.start_time.slice(0, 10);
        }
      }

      let lesson = { ...rawLesson };
      // Fallback clean HTML from subject if any leaks from cache
      if (lesson.subject && lesson.subject.includes('<')) {
        try {
          const doc = new DOMParser().parseFromString(lesson.subject, 'text/html');
          const s = doc.querySelector('.lesson-text-wrap') || doc.querySelector('.lesson-line1');
          const r = doc.querySelector('.lesson-room');
          const t = doc.querySelector('.lesson-teacher') || doc.querySelector('.lesson-line2');
          const o = doc.querySelector('.lesson-order');
          const top = doc.querySelector('.lesson-homework') || doc.querySelector('.lesson-line3');

          if (s) {
            if (r) r.remove();
            lesson.subject = s.textContent.trim();
          } else {
            lesson.subject = doc.body.textContent.trim();
          }
          if (r && !lesson.classroom) lesson.classroom = r.textContent.trim();
          if (t && !lesson.teacher) lesson.teacher = t.textContent.trim();
          if (o && !lesson.order) lesson.order = o.textContent.trim();
          if (top && !lesson.topic) lesson.topic = top.textContent.trim();
        } catch (e) {}
      }

      if (lesson.classroom && (lesson.classroom.includes('fc-apex') || lesson.classroom.includes('apex-events'))) {
        lesson.classroom = null;
      }

      if (!acc[dateKey]) acc[dateKey] = [];
      acc[dateKey].push(lesson);
    });

    // Sort lessons within each date strictly by order (1, 2, 3...) or start time
    Object.keys(acc).forEach((d) => {
      acc[d].sort((a, b) => {
        const orderA = parseInt(a.order, 10);
        const orderB = parseInt(b.order, 10);
        if (!isNaN(orderA) && !isNaN(orderB)) return orderA - orderB;
        return (a.start_time || '').localeCompare(b.start_time || '');
      });
    });

    return acc;
  }, [timetable, todayStr]);

  const availableDates = useMemo(() => Object.keys(grouped).sort(), [grouped]);

  const changeDateByOffset = (offset) => {
    triggerHaptic('light');
    const [y, m, d] = selectedDate.split('-');
    const curr = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
    curr.setDate(curr.getDate() + offset);
    setSelectedDate(getLocalDateStr(curr));
  };

  const goToToday = () => {
    triggerHaptic('medium');
    setSelectedDate(todayStr);
  };

  const isToday = selectedDate === todayStr;
  const currentLessons = grouped[selectedDate] || [];

  // Find nearest date with lessons if current selected has none
  const nearestDate = useMemo(() => {
    if (availableDates.length === 0) return null;
    if (availableDates.includes(selectedDate)) return null;
    const future = availableDates.find((d) => d >= selectedDate);
    return future || availableDates[availableDates.length - 1];
  }, [availableDates, selectedDate]);

  return (
    <div className="space-y-3 pb-24">
      {/* Date Switcher Bar */}
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

        {/* Quick Date Chips */}
        {availableDates.length > 0 && (
          <div className="flex items-center space-x-1.5 overflow-x-auto py-1 text-xs">
            {availableDates.map((d) => {
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
                  <span>{formatDateDisplay(d).split(',')[0]}</span>
                  <span className="text-[10px] opacity-75">{d.slice(8)}</span>
                  {isTod && <span className="w-1.5 h-1.5 rounded-full bg-blue-500 inline-block"></span>}
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

      {/* Lesson List */}
      <div className="space-y-2">
        {currentLessons.length === 0 ? (
          <div className="bg-white dark:bg-zinc-900 rounded-2xl p-8 text-center border border-slate-200 dark:border-zinc-800 shadow-sm space-y-3">
            <p className="text-sm font-semibold text-slate-700 dark:text-zinc-300">
              🎉 На этот день уроков нет
            </p>
            <p className="text-xs text-slate-400">
              {isToday ? 'Сегодня в расписании занятий не запланировано.' : 'Выходной или каникулы.'}
            </p>
            {nearestDate && (
              <button
                onClick={() => {
                  triggerHaptic('light');
                  setSelectedDate(nearestDate);
                }}
                className="px-4 py-2 bg-blue-50 dark:bg-zinc-800 text-blue-600 dark:text-blue-400 text-xs font-semibold rounded-xl border border-blue-100 dark:border-zinc-700 active:scale-95 transition-all"
              >
                Посмотреть уроки на {formatDateDisplay(nearestDate)} →
              </button>
            )}
          </div>
        ) : (
          currentLessons.map((lesson, idx) => {
            let timeStr = '';
            if (lesson.start_time?.includes('T')) {
              const s = lesson.start_time.split('T')[1]?.slice(0, 5);
              const e = lesson.end_time?.split('T')[1]?.slice(0, 5);
              timeStr = e ? `${s} - ${e}` : s;
            }

            const lessonNumber = lesson.order || String(idx + 1);

            return (
              <div
                key={lesson.id || idx}
                className="p-3.5 bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm flex items-start space-x-3 transition-all"
              >
                <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0 font-extrabold text-xs mt-0.5 shadow-sm shadow-blue-500/20">
                  {lessonNumber}
                </div>

                <div className="space-y-1 flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-sm text-slate-900 dark:text-zinc-100">
                      {lesson.subject}
                    </h4>
                    {timeStr && (
                      <span className="flex items-center text-[11px] text-slate-500 dark:text-zinc-400 font-medium bg-slate-50 dark:bg-zinc-800 px-2 py-0.5 rounded-lg border border-slate-100 dark:border-zinc-700">
                        <Clock className="w-3 h-3 mr-1" />
                        {timeStr}
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500 dark:text-zinc-400">
                    {lesson.classroom && (
                      <span className="flex items-center font-medium text-slate-600 dark:text-zinc-300">
                        <MapPin className="w-3 h-3 mr-1 text-blue-500" />
                        Каб. {lesson.classroom}
                      </span>
                    )}
                    {lesson.teacher && (
                      <span className="flex items-center">
                        <User className="w-3 h-3 mr-1 text-slate-400" />
                        {lesson.teacher}
                      </span>
                    )}
                  </div>

                  {lesson.topic && (
                    <div className="text-[11px] text-slate-500 dark:text-zinc-400 mt-1 pt-1 border-t border-slate-100 dark:border-zinc-800/80 flex items-start gap-1">
                      <BookOpen className="w-3.5 h-3.5 text-blue-500 shrink-0 mt-0.5" />
                      <span className="italic">{lesson.topic}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
