import React from 'react';
import { BookOpen, CheckSquare, Calendar, User } from 'lucide-react';
import { triggerHaptic } from '../api';

export default function Navigation({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'grades', label: 'Оценки', icon: BookOpen },
    { id: 'homework', label: 'Домашка', icon: CheckSquare },
    { id: 'timetable', label: 'Расписание', icon: Calendar },
    { id: 'profile', label: 'Профиль', icon: User },
  ];

  const handleTabChange = (tabId) => {
    triggerHaptic('selection');
    setActiveTab(tabId);
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-lg border-t border-slate-200 dark:border-zinc-800 pb-safe">
      <div className="grid grid-cols-4 max-w-md mx-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`flex flex-col items-center justify-center py-2.5 transition-colors relative ${
                isActive
                  ? 'text-blue-600 dark:text-blue-400 font-semibold'
                  : 'text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-zinc-200'
              }`}
            >
              <Icon className={`w-5 h-5 mb-1 ${isActive ? 'scale-110' : ''} transition-transform`} />
              <span className="text-[11px] leading-none">{tab.label}</span>
              {isActive && (
                <span className="absolute top-0 w-8 h-0.5 bg-blue-600 dark:bg-blue-400 rounded-full" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
