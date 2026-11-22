import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { triggerHaptic } from '../api';

export default function GradesTab({ gradesData, recentGrades }) {
  const [expandedSubject, setExpandedSubject] = useState(null);

  const subjects = gradesData?.subjects || {};
  const subjectList = Object.entries(subjects);

  const toggleExpand = (name) => {
    triggerHaptic('light');
    setExpandedSubject(expandedSubject === name ? null : name);
  };

  const getGradeStyle = (grade) => {
    if (grade >= 9) return 'bg-emerald-500 text-white';
    if (grade >= 7) return 'bg-blue-500 text-white';
    if (grade >= 5) return 'bg-amber-500 text-white';
    return 'bg-rose-500 text-white';
  };

  const getAvgBadge = (avg) => {
    if (!avg) return 'bg-slate-100 dark:bg-zinc-800 text-slate-500 dark:text-zinc-400';
    if (avg >= 9) return 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800';
    if (avg >= 7) return 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800';
    if (avg >= 5) return 'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800';
    return 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800';
  };

  return (
    <div className="space-y-4 pb-24">
      {/* Recent Grades Section */}
      {recentGrades && recentGrades.length > 0 && (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-4 shadow-sm border border-slate-200 dark:border-zinc-800">
          <div className="flex items-center space-x-2 mb-3">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <h2 className="text-xs font-semibold tracking-wide uppercase text-slate-500 dark:text-zinc-400">
              Последние оценки
            </h2>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            {recentGrades.slice(0, 5).map((item, idx) => (
              <div
                key={idx}
                className="flex items-center space-x-2 px-3 py-2 bg-slate-50 dark:bg-zinc-800/60 rounded-xl shrink-0 border border-slate-100 dark:border-zinc-800"
              >
                <span className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${getGradeStyle(item.grade)}`}>
                  {item.grade}
                </span>
                <div className="text-left">
                  <p className="text-xs font-medium text-slate-800 dark:text-zinc-200 max-w-[100px] truncate">
                    {item.subject}
                  </p>
                  <p className="text-[10px] text-slate-400">{item.date_str}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Subjects List */}
      <div className="space-y-2">
        <h2 className="text-xs font-semibold tracking-wide uppercase text-slate-500 dark:text-zinc-400 px-1">
          Предметы ({subjectList.length})
        </h2>

        {subjectList.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            Нет данных об оценках
          </div>
        ) : (
          subjectList.map(([name, data]) => {
            const isExpanded = expandedSubject === name;
            const grades = data.grades || [];
            return (
              <div
                key={name}
                className="bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 overflow-hidden shadow-sm transition-all"
              >
                <div
                  onClick={() => toggleExpand(name)}
                  className="p-4 flex items-center justify-between cursor-pointer active:bg-slate-50 dark:active:bg-zinc-800/50"
                >
                  <div className="space-y-1 pr-2">
                    <h3 className="font-medium text-sm text-slate-900 dark:text-zinc-100">
                      {name}
                    </h3>
                    <div className="flex flex-wrap gap-1 items-center">
                      {grades.length > 0 ? (
                        grades.slice(0, 7).map((g, i) => (
                          <span
                            key={i}
                            className={`px-1.5 py-0.5 rounded text-[11px] font-semibold ${getGradeStyle(g)}`}
                          >
                            {g}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400">Нет оценок</span>
                      )}
                      {grades.length > 7 && (
                        <span className="text-xs text-slate-400">+{grades.length - 7}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <div className="text-right">
                      {data.average && (
                        <div className={`px-2 py-0.5 rounded-lg text-xs font-bold ${getAvgBadge(data.average)}`}>
                          {data.average}
                        </div>
                      )}
                      {data.semester_grade && (
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          Сем: {data.semester_grade}
                        </div>
                      )}
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </div>

                {isExpanded && (
                  <div className="px-4 pb-4 pt-1 border-t border-slate-100 dark:border-zinc-800/80 bg-slate-50/50 dark:bg-zinc-900/50">
                    <p className="text-xs font-medium text-slate-500 mb-2">Все оценки за период:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {grades.map((g, i) => (
                        <span
                          key={i}
                          className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs shadow-xs ${getGradeStyle(g)}`}
                        >
                          {g}
                        </span>
                      ))}
                    </div>
                    {data.semester_grade && (
                      <div className="mt-3 text-xs text-slate-600 dark:text-zinc-400">
                        Итоговая оценка за семестр: <span className="font-bold text-slate-900 dark:text-white">{data.semester_grade}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
