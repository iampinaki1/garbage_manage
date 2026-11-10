import React, { useState, useEffect } from 'react';
import { 
  History as HistoryIcon, 
  Search, 
  Filter, 
  Calendar, 
  ExternalLink, 
  RefreshCw, 
  Layers, 
  CheckCircle2, 
  XCircle,
  AlertTriangle,
  LayoutGrid,
  Table as TableIcon
} from 'lucide-react';
import WasteCategoryBadge from '../components/WasteCategoryBadge';
import { apiService } from '../api/client';

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'cards'
  const [totalCount, setTotalCount] = useState(0);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const catParam = categoryFilter !== 'all' ? categoryFilter : null;
      const data = await apiService.getHistory(50, 0, catParam);
      setHistory(data.items || []);
      setTotalCount(data.total_count || 0);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [categoryFilter]);

  const filteredItems = history.filter((item) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      item.primary_category.toLowerCase().includes(q) ||
      item.primary_category_display.toLowerCase().includes(q) ||
      item.analysis_id.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-xs font-semibold mb-2">
            <HistoryIcon className="w-3.5 h-3.5" />
            <span>Inspection Logs & Audit Trail</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Analysis History</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Historical log of all processed waste items, timestamps, and localized disposal classifications.
          </p>
        </div>

        <button
          onClick={fetchHistory}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Records</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-4 items-center justify-between">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ID or Category..."
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500 transition"
          />
        </div>

        {/* Filters & View Toggle */}
        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
          {/* Category Dropdown */}
          <div className="flex items-center gap-1.5 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-transparent font-medium text-slate-700 focus:outline-none cursor-pointer"
            >
              <option value="all">All Categories</option>
              <option value="organic_waste">Organic</option>
              <option value="paper_waste">Paper & Cardboard</option>
              <option value="plastic_waste">Plastic</option>
              <option value="metal_waste">Metal</option>
              <option value="glass_waste">Glass</option>
              <option value="electronic_waste">Electronic</option>
              <option value="hazardous_waste">Hazardous</option>
              <option value="textile_waste">Textile</option>
              <option value="residual_waste">Residual</option>
            </select>
          </div>

          {/* View toggle */}
          <div className="flex items-center bg-slate-100 p-1 rounded-xl">
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-lg transition ${viewMode === 'table' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-400'}`}
              title="Table View"
            >
              <TableIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`p-1.5 rounded-lg transition ${viewMode === 'cards' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-400'}`}
              title="Gallery View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="py-20 text-center text-slate-400">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 opacity-50" />
          <p className="text-xs font-semibold">Retrieving inspection records...</p>
        </div>
      ) : filteredItems.length > 0 ? (
        viewMode === 'table' ? (
          /* Table View */
          <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100 uppercase tracking-wider">
                  <tr>
                    <th className="py-3.5 px-6">Preview</th>
                    <th className="py-3.5 px-6">Analysis ID</th>
                    <th className="py-3.5 px-6">Timestamp</th>
                    <th className="py-3.5 px-6">Category</th>
                    <th className="py-3.5 px-6">Objects</th>
                    <th className="py-3.5 px-6">Recyclability</th>
                    <th className="py-3.5 px-6">CO2 Avoided</th>
                    <th className="py-3.5 px-6 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                  {filteredItems.map((item) => (
                    <tr key={item.analysis_id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-6">
                        {item.annotated_image_url ? (
                          <img
                            src={item.annotated_image_url}
                            alt="Annotated thumbnail"
                            className="w-12 h-12 object-cover rounded-xl border border-slate-200 bg-slate-900"
                          />
                        ) : (
                          <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400">
                            N/A
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-6 font-mono text-[11px] text-slate-500">
                        {item.analysis_id.slice(0, 8)}...
                      </td>
                      <td className="py-3 px-6 text-slate-500">
                        {item.timestamp ? new Date(item.timestamp).toLocaleString() : 'N/A'}
                      </td>
                      <td className="py-3 px-6">
                        <WasteCategoryBadge category={item.primary_category} size="sm" />
                      </td>
                      <td className="py-3 px-6 font-bold">
                        {item.total_objects} item(s)
                      </td>
                      <td className="py-3 px-6">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                          item.overall_recyclability === 'Recyclable'
                            ? 'bg-emerald-100 text-emerald-800'
                            : item.overall_recyclability === 'Partially Recyclable'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}>
                          {item.overall_recyclability === 'Recyclable' ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          {item.overall_recyclability}
                        </span>
                      </td>
                      <td className="py-3 px-6 font-mono font-bold text-emerald-700">
                        {item.total_co2_saved_kg ? `${item.total_co2_saved_kg} kg` : '0.00 kg'}
                      </td>
                      <td className="py-3 px-6 text-right">
                        {item.annotated_image_url && (
                          <a
                            href={item.annotated_image_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-emerald-600 hover:text-emerald-800 font-bold"
                          >
                            <span>Open</span>
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          /* Cards Gallery View */
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredItems.map((item) => (
              <div
                key={item.analysis_id}
                className="bg-white rounded-3xl p-5 border border-slate-200/90 shadow-sm space-y-4 hover:shadow-md transition"
              >
                <div className="relative rounded-2xl overflow-hidden bg-slate-900 aspect-video flex items-center justify-center">
                  {item.annotated_image_url ? (
                    <img
                      src={item.annotated_image_url}
                      alt="Annotated detection"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span className="text-slate-500 text-xs">No image stored</span>
                  )}
                  <div className="absolute top-2.5 left-2.5">
                    <WasteCategoryBadge category={item.primary_category} size="sm" />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-400">ID: {item.analysis_id.slice(0, 8)}</span>
                    <span className="text-slate-400">{new Date(item.timestamp).toLocaleDateString()}</span>
                  </div>
                  <h3 className="font-extrabold text-slate-900 text-sm">{item.primary_category_display}</h3>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="font-semibold text-emerald-700">
                    +{item.total_co2_saved_kg} kg CO2e
                  </span>
                  {item.annotated_image_url && (
                    <a
                      href={item.annotated_image_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-emerald-600 hover:underline flex items-center gap-1 font-bold text-[11px]"
                    >
                      <span>Full Image</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      ) : (
        <div className="bg-white rounded-3xl p-16 text-center text-slate-400 border border-slate-200">
          <HistoryIcon className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <h3 className="text-base font-bold text-slate-700">No Historical Records Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {search || categoryFilter !== 'all'
              ? 'Try adjusting your search criteria or resetting the category filter.'
              : 'Complete your first waste analysis to begin recording persistent inspection logs.'}
          </p>
        </div>
      )}
    </div>
  );
}

