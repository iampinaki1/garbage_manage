import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Leaf, 
  Zap, 
  Smartphone, 
  Car, 
  Trees, 
  ShieldCheck, 
  HelpCircle,
  TrendingUp,
  Download
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  Cell, 
  PieChart, 
  Pie 
} from 'recharts';
import WasteCategoryBadge from '../components/WasteCategoryBadge';
import { apiService } from '../api/client';

const BAR_COLORS = [
  '#2E8B57', '#CD853F', '#1E90FF', '#708090', '#00BFFF', 
  '#8A2BE2', '#DC143C', '#DA70D6', '#696969'
];

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        setLoading(true);
        const data = await apiService.getAnalytics();
        setAnalytics(data);
      } catch (err) {
        console.error('Failed to load analytics:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, []);

  const aggregate = analytics?.aggregate_impact || {};
  const equivalents = aggregate?.equivalents || {};
  const categories = analytics?.category_distribution || [];

  const chartData = categories.map((c) => ({
    name: c.category_display,
    co2: c.co2_saved_kg,
    energy: c.energy_saved_kwh,
    count: c.count
  }));

  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold mb-2">
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Life-Cycle Assessment Telemetry</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Environmental Impact Analytics</h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Documented greenhouse gas and electrical energy savings derived from EPA WARM v15 and European Environment Agency conversion factors.
        </p>
      </div>

      {/* Hero Environmental Impact Banner */}
      <div className="bg-gradient-to-br from-emerald-700 via-teal-800 to-slate-900 rounded-3xl p-6 sm:p-10 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-400/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          <div className="space-y-3">
            <span className="text-xs uppercase font-extrabold tracking-widest text-emerald-300">Cumulative Savings</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">
              {aggregate.total_co2_saved_kg || 0} <span className="text-2xl font-bold text-emerald-200">kg CO2e</span>
            </div>
            <p className="text-xs text-emerald-100 leading-relaxed max-w-md">
              Avoided carbon emissions across all verified recyclable items compared against standard municipal landfill decomposition baseline.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3 bg-white/10 backdrop-blur-md rounded-2xl p-4 sm:p-6 border border-white/10">
            <div className="text-center">
              <Trees className="w-5 h-5 text-emerald-300 mx-auto mb-1.5" />
              <div className="text-lg sm:text-xl font-black">{equivalents.trees_seedling_years_equivalent || 0}</div>
              <div className="text-[10px] text-emerald-200 mt-0.5">Urban Trees Planted (10y)</div>
            </div>
            <div className="text-center border-x border-white/10">
              <Smartphone className="w-5 h-5 text-cyan-300 mx-auto mb-1.5" />
              <div className="text-lg sm:text-xl font-black">{equivalents.smartphone_charges_equivalent || 0}</div>
              <div className="text-[10px] text-cyan-200 mt-0.5">Phone Charges Powered</div>
            </div>
            <div className="text-center">
              <Car className="w-5 h-5 text-amber-300 mx-auto mb-1.5" />
              <div className="text-lg sm:text-xl font-black">{equivalents.miles_driven_avoided || 0}</div>
              <div className="text-[10px] text-amber-200 mt-0.5">Vehicle Miles Avoided</div>
            </div>
          </div>
        </div>
      </div>

      {/* Chart: CO2 Avoided per Category */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-slate-900">Carbon Abatement per Waste Category</h2>
            <p className="text-xs text-slate-500">Kilograms of CO2e avoided through secondary raw material recycling</p>
          </div>
          <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-100 self-start sm:self-auto">
            EPA WARM Factors
          </span>
        </div>

        <div className="h-80 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 10, fill: '#64748b' }} 
                interval={0} 
                angle={-20} 
                textAnchor="end"
              />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                formatter={(val) => [`${val} kg CO2e`, 'Avoided']}
              />
              <Bar dataKey="co2" radius={[6, 6, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Material Breakdown Table */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Detailed Category Breakdown & Audit</h2>
            <p className="text-xs text-slate-500">Documented life-cycle impact parameters for each canonical stream</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100 uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-6">Canonical Category</th>
                <th className="py-3.5 px-6">Share (%)</th>
                <th className="py-3.5 px-6">Detections</th>
                <th className="py-3.5 px-6">Total CO2e Saved</th>
                <th className="py-3.5 px-6">Total Energy Saved</th>
                <th className="py-3.5 px-6">Documented Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
              {categories.map((c) => (
                <tr key={c.category} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-6">
                    <WasteCategoryBadge category={c.category} size="md" />
                  </td>
                  <td className="py-3.5 px-6 font-bold text-slate-900">
                    {c.percentage}%
                  </td>
                  <td className="py-3.5 px-6 font-semibold">
                    {c.count} items
                  </td>
                  <td className="py-3.5 px-6 font-mono font-bold text-emerald-700">
                    {c.co2_saved_kg} kg
                  </td>
                  <td className="py-3.5 px-6 font-mono text-cyan-700">
                    {c.energy_saved_kwh} kWh
                  </td>
                  <td className="py-3.5 px-6 text-[11px] text-slate-400">
                    EPA WARM v15 / EEA Model
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Scientific Transparency Notice */}
      <div className="p-5 bg-slate-100/80 rounded-2xl border border-slate-200 text-xs text-slate-600 flex items-start gap-3">
        <HelpCircle className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h4 className="font-bold text-slate-800">Life-Cycle Assessment Transparency Notice</h4>
          <p className="text-[11px] leading-relaxed">
            All carbon avoidance (kg CO2e) and electrical energy savings (kWh) displayed on this platform are deterministic calculations derived from published US EPA WARM v15 reports and European Environment Agency directives. Actual emissions reductions vary based on local municipal recovery efficiency and the energy mix of regional reprocessing smelters.
          </p>
        </div>
      </div>
    </div>
  );
}

