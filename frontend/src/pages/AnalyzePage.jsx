import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  Image as ImageIcon, 
  ScanLine, 
  AlertCircle, 
  CheckCircle2, 
  Trash2, 
  RefreshCw, 
  Zap, 
  Info, 
  ChevronRight, 
  Flame, 
  ShieldCheck, 
  Sparkles,
  Maximize2
} from 'lucide-react';
import WasteCategoryBadge from '../components/WasteCategoryBadge';
import { JURISDICTIONS } from '../components/Navbar';
import { apiService } from '../api/client';

export default function AnalyzePage({ defaultLocation = 'us_epa' }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [location, setLocation] = useState(defaultLocation);
  const [isContaminated, setIsContaminated] = useState(false);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeView, setActiveView] = useState('annotated'); // 'annotated' | 'original'

  const fileInputRef = useRef(null);

  const handleFileSelect = (selected) => {
    if (!selected) return;
    if (!selected.type.startsWith('image/')) {
      setError('Please upload a valid image file (JPEG, PNG, WebP).');
      return;
    }
    if (selected.size > 10 * 1024 * 1024) {
      setError('File size exceeds the 10 MB limit.');
      return;
    }
    setError(null);
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    setResult(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const data = await apiService.analyzeImage(file, location, isContaminated);
      setResult(data);
      setActiveView('annotated');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Analysis pipeline encountered an error. Please try another image.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="space-y-8 py-6 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold mb-2">
          <ScanLine className="w-3.5 h-3.5" />
          <span>Automated Vision Inspection</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Waste Analysis & Segregation</h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Upload waste photographs to trigger YOLO multi-object localization and MobileNetV3 material classification.
        </p>
      </div>

      {/* Main Grid: Upload & Analysis Parameters */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Drag & Drop / Preview (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm">
            {!previewUrl ? (
              /* Drop Zone */
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-2xl p-10 text-center cursor-pointer bg-slate-50/50 hover:bg-emerald-50/30 transition-all group"
              >
                <div className="w-16 h-16 rounded-3xl bg-white border border-slate-200 shadow-sm flex items-center justify-center mx-auto mb-4 group-hover:scale-110 group-hover:border-emerald-300 transition-transform">
                  <UploadCloud className="w-8 h-8 text-emerald-600" />
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-1">Click to upload or drag & drop</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto mb-4">
                  Supports JPEG, PNG, or WebP waste images up to 10 MB. High-resolution captures improve multi-object box localization.
                </p>
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 text-white text-xs font-semibold rounded-xl shadow-sm">
                  Browse Local Files
                </span>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleFileSelect(e.target.files?.[0])}
                  className="hidden"
                />
              </div>
            ) : (
              /* Image Preview / Result View */
              <div className="space-y-4">
                <div className="relative rounded-2xl overflow-hidden bg-slate-900 border border-slate-200 shadow-inner max-h-[460px] flex items-center justify-center">
                  <img
                    src={
                      activeView === 'annotated' && result?.annotated_image_url
                        ? result.annotated_image_url
                        : previewUrl
                    }
                    alt="Waste Subject"
                    className="w-full h-auto max-h-[440px] object-contain"
                  />

                  {/* Toggle between original and annotated if result exists */}
                  {result && (
                    <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-md rounded-xl p-1 flex gap-1 text-[11px] font-semibold text-white">
                      <button
                        onClick={() => setActiveView('annotated')}
                        className={`px-2.5 py-1 rounded-lg transition ${activeView === 'annotated' ? 'bg-emerald-600 text-white' : 'text-slate-300 hover:text-white'}`}
                      >
                        YOLO Detections
                      </button>
                      <button
                        onClick={() => setActiveView('original')}
                        className={`px-2.5 py-1 rounded-lg transition ${activeView === 'original' ? 'bg-emerald-600 text-white' : 'text-slate-300 hover:text-white'}`}
                      >
                        Original
                      </button>
                    </div>
                  )}

                  {/* Reset button */}
                  <button
                    onClick={handleReset}
                    className="absolute top-3 right-3 p-2 bg-slate-900/80 hover:bg-rose-600 text-white rounded-xl backdrop-blur-md transition-colors"
                    title="Remove and select another"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-500 px-1">
                  <span>{file?.name}</span>
                  <span>{(file?.size / (1024 * 1024)).toFixed(2)} MB</span>
                </div>
              </div>
            )}
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-start gap-3 text-xs text-rose-800">
              <AlertCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Inspection Error</p>
                <p className="mt-0.5">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Settings & Trigger (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-6">
            <h2 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3">Inspection Configuration</h2>

            {/* Jurisdiction Select */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Regional Recycling Profile
              </label>
              <select
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition cursor-pointer"
              >
                {JURISDICTIONS.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.flag} {loc.name}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-slate-400 mt-1">
                Calibrates recommended bin colors and curbside collection mandates.
              </p>
            </div>

            {/* Contamination Toggle */}
            <div className="p-4 bg-amber-50/60 border border-amber-200/80 rounded-2xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-900">Food / Grease Contamination</span>
                <input
                  type="checkbox"
                  id="contamination"
                  checked={isContaminated}
                  onChange={(e) => setIsContaminated(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded focus:ring-emerald-500 border-slate-300 cursor-pointer"
                />
              </div>
              <label htmlFor="contamination" className="text-[11px] text-amber-700 block leading-relaxed cursor-pointer">
                Check this if the item contains unwashed oils, melted cheese, or chemical residues. The engine will automatically evaluate if paper/cardboard fibers are ruined.
              </label>
            </div>

            {/* Run Button */}
            <button
              onClick={handleAnalyze}
              disabled={!file || loading}
              className={`w-full py-4 rounded-2xl font-bold text-sm shadow-md transition flex items-center justify-center gap-2 ${
                !file || loading
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                  : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/25 hover:-translate-y-0.5'
              }`}
            >
              {loading ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span>Processing YOLO & Classifier...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Run Waste Segregation Analysis</span>
                </>
              )}
            </button>
          </div>

          {/* Quick Guidance Box */}
          <div className="p-5 bg-emerald-50/70 border border-emerald-100 rounded-3xl text-xs text-emerald-900 space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-emerald-800">
              <ShieldCheck className="w-4 h-4" />
              <span>Offline ML Guarantee</span>
            </div>
            <p className="leading-relaxed text-emerald-700 text-[11px]">
              Every classification is computed by local neural networks: <strong>Model A (MobileNetV3)</strong> trained on TrashNet/RealWaste and <strong>Model B (YOLOv8)</strong> fine-tuned on TACO annotations.
            </p>
          </div>
        </div>
      </div>

      {/* Results Section (When Result is Available) */}
      {result && (
        <div className="space-y-6 pt-4 animate-in fade-in duration-300">
          {/* Summary Banner */}
          <div className="bg-gradient-to-r from-emerald-600 to-teal-700 text-white rounded-3xl p-6 sm:p-8 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="text-xs uppercase font-bold tracking-wider text-emerald-200">Analysis Summary</span>
                <h2 className="text-2xl font-black mt-1">
                  {result.summary.primary_category_display} • {result.summary.overall_recyclability}
                </h2>
                <p className="text-xs text-emerald-100 mt-1">
                  Detected {result.summary.total_objects_detected} object(s) in {result.summary.inference_latency_ms} ms using {result.location_profile.toUpperCase()} disposal rules.
                </p>
              </div>

              <div className="flex items-center gap-4 bg-white/10 backdrop-blur-md rounded-2xl p-4 self-start sm:self-auto">
                <div className="text-right">
                  <div className="text-xs text-emerald-200 font-semibold">CO2e Avoided</div>
                  <div className="text-2xl font-extrabold text-white">{result.summary.total_co2_saved_kg} kg</div>
                </div>
                <div className="w-px h-8 bg-white/20" />
                <div className="text-right">
                  <div className="text-xs text-emerald-200 font-semibold">Energy Saved</div>
                  <div className="text-2xl font-extrabold text-white">{result.summary.total_energy_saved_kwh} kWh</div>
                </div>
              </div>
            </div>
          </div>

          {/* Detected Objects Cards Grid */}
          <div>
            <h3 className="text-lg font-bold text-slate-900 mb-4">Detected Objects & Localized Instructions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {result.detections.map((det) => (
                <div 
                  key={det.object_id}
                  className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-4 hover:border-emerald-300 transition-colors"
                >
                  {/* Object Header */}
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-slate-900 text-white flex items-center justify-center text-xs font-bold">
                        #{det.object_id}
                      </span>
                      <h4 className="font-extrabold text-slate-900 text-base">{det.matched_item}</h4>
                    </div>
                    <WasteCategoryBadge category={det.category} size="md" />
                  </div>

                  {/* Material & Confidence */}
                  <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <div>
                      <span className="text-slate-400 block">Material</span>
                      <span className="font-bold text-slate-800">{det.material}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Model Confidence</span>
                      <span className="font-bold text-emerald-700">{(det.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>

                  {/* Recommended Bin */}
                  <div className="p-3.5 rounded-xl border border-blue-100 bg-blue-50/60 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-blue-700 block">Recommended Segregation Bin</span>
                    <span className="text-xs font-extrabold text-blue-900 block">{det.recommended_bin}</span>
                  </div>

                  {/* Preparation Instructions */}
                  <div className="space-y-1 text-xs">
                    <span className="font-bold text-slate-700 block">Preparation Instructions:</span>
                    <p className="text-slate-600 text-[11px] leading-relaxed bg-slate-50 p-2.5 rounded-xl">
                      {det.preparation_instructions}
                    </p>
                  </div>

                  {/* Recycling Method */}
                  <div className="space-y-1 text-xs">
                    <span className="font-bold text-slate-700 block">Reprocessing Method:</span>
                    <p className="text-slate-500 text-[11px] leading-relaxed">
                      {det.recycling_method}
                    </p>
                  </div>

                  {/* Contamination Alert if applicable */}
                  {det.contamination_assessment.is_contaminated && (
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 space-y-1">
                      <div className="flex items-center gap-1 font-bold text-amber-900">
                        <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                        <span>Contamination Impact</span>
                      </div>
                      <p className="text-[11px]">{det.contamination_assessment.action_taken}</p>
                    </div>
                  )}

                  {/* Environmental Impact Pill */}
                  <div className="flex items-center justify-between text-[11px] pt-3 border-t border-slate-100 text-slate-500">
                    <span>Assumed mass: {det.environmental_impact.assumed_weight_kg * 1000}g</span>
                    <span className="font-semibold text-emerald-700">
                      Savings: {det.environmental_impact.estimated_co2_saved_kg} kg CO2e • {det.environmental_impact.estimated_energy_saved_kwh} kWh
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

