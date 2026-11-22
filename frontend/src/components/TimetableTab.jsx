import React from 'react';
import { Clock, MapPin, User, BookOpen } from 'lucide-react';

export default function TimetableTab({ timetable }) {
  const lessons = timetable || [];

  // Group lessons by date (YYYY-MM-DD or formatted)
  const grouped = lessons.reduce((acc, rawLesson) => {
    let dateKey = 'Сегодня';
    if (rawLesson.start_time) {
      if (rawLesson.start_time.includes('T')) {
        dateKey = rawLesson.start_time.split('T')[0];
      } else {
        dateKey = rawLesson.start_time.slice(0, 10);
      }
    }
    if (!acc[dateKey]) acc[dateKey] = [];

    // Fallback: If title has raw HTML from old cache, clean it
    let lesson = { ...rawLesson };
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

    acc[dateKey].push(lesson);
    return acc;
  }, {});

  const dates = Object.keys(grouped);

  return (
    <div className="space-y-4 pb-24">
      <h2 className="text-xs font-semibold tracking-wide uppercase text-slate-500 dark:text-zinc-400 px-1">
        Расписание занятий
      </h2>

      {dates.length === 0 ? (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-8 text-center border border-slate-200 dark:border-zinc-800">
          <p className="text-sm font-medium text-slate-700 dark:text-zinc-300">
            📅 Расписание отсутствует
          </p>
          <p className="text-xs text-slate-400 mt-1">
            На ближайшие дни уроки не найдены в системе
          </p>
        </div>
      ) : (
        dates.map((date) => (
          <div key={date} className="space-y-2">
            <div className="text-xs font-bold text-blue-600 dark:text-blue-400 px-1">
              🗓 {date}
            </div>
            <div className="space-y-2">
              {grouped[date].map((lesson, idx) => {
                let timeStr = '';
                if (lesson.start_time?.includes('T')) {
                  const s = lesson.start_time.split('T')[1]?.slice(0, 5);
                  const e = lesson.end_time?.split('T')[1]?.slice(0, 5);
                  timeStr = e ? `${s} - ${e}` : s;
                }

                return (
                  <div
                    key={lesson.id || idx}
                    className="p-3.5 bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm flex items-start space-x-3"
                  >
                    <div className="w-8 h-8 rounded-xl bg-blue-50 dark:bg-zinc-800 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0 font-bold text-xs mt-0.5">
                      {lesson.order || idx + 1}
                    </div>

                    <div className="space-y-1 flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold text-sm text-slate-900 dark:text-zinc-100">
                          {lesson.subject}
                        </h4>
                        {timeStr && (
                          <span className="flex items-center text-[11px] text-slate-400 font-medium">
                            <Clock className="w-3 h-3 mr-1" />
                            {timeStr}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500 dark:text-zinc-400">
                        {lesson.classroom && (
                          <span className="flex items-center">
                            <MapPin className="w-3 h-3 mr-1 text-slate-400" />
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
                        <p className="text-[11px] text-slate-400 dark:text-zinc-500 italic mt-0.5 flex items-center">
                          <BookOpen className="w-3 h-3 mr-1 shrink-0" />
                          {lesson.topic}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
