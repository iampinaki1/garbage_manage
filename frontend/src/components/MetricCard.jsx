import React from 'react';

export default function MetricCard({ title, value, unit, icon: Icon, color = 'eco', change, changeText, subtext }) {
  const colorMap = {
    eco: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    purple: 'bg-purple-50 text-purple-600 border-purple-100',
    rose: 'bg-rose-50 text-rose-600 border-rose-100',
    slate: 'bg-slate-100 text-slate-700 border-slate-200'
  };

  const badgeClass = colorMap[color] || colorMap.eco;

  return (
    <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-slate-500">{title}</span>
        {Icon && (
          <div className={`p-2.5 rounded-xl border ${badgeClass}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
      
      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-3xl font-extrabold text-slate-900 tracking-tight">{value}</span>
        {unit && <span className="text-sm font-semibold text-slate-500">{unit}</span>}
      </div>

      <div className="flex items-center gap-2 text-xs">
        {change !== undefined && (
          <span className={`font-semibold px-1.5 py-0.5 rounded ${change >= 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
            {change >= 0 ? `+${change}%` : `${change}%`}
          </span>
        )}
        <span className="text-slate-500">{changeText || subtext || 'System verified'}</span>
      </div>
    </div>
  );
}

