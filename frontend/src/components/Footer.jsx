import React from 'react';
import { Leaf, ShieldCheck, Database, Award, ExternalLink } from 'lucide-react';

export default function Footer({ onNavigate }) {
  return (
    <footer className="bg-slate-900 text-slate-400 text-xs border-t border-slate-800 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Col 1 */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-white font-extrabold text-base">
              <span className="p-1.5 bg-emerald-600 rounded-lg text-sm text-white">🌱</span>
              <span>EcoSort AI</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Automated dual-model computer vision system for real-time waste classification, multi-object detection, localized bin segregation, and EPA WARM carbon impact tracking.
            </p>
            <div className="flex items-center gap-2 pt-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-emerald-950/80 text-emerald-400 border border-emerald-800 text-[10px] font-semibold">
                <ShieldCheck className="w-3 h-3" />
                Zero External Vision APIs
              </span>
            </div>
          </div>

          {/* Col 2: Navigation */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-3">Platform Navigation</h4>
            <ul className="space-y-2">
              <li><button onClick={() => onNavigate('landing')} className="hover:text-emerald-400 transition">Home & Overview</button></li>
              <li><button onClick={() => onNavigate('dashboard')} className="hover:text-emerald-400 transition">SaaS Dashboard</button></li>
              <li><button onClick={() => onNavigate('analyze')} className="hover:text-emerald-400 transition">Live Waste Analysis</button></li>
              <li><button onClick={() => onNavigate('history')} className="hover:text-emerald-400 transition">Inspection Logs</button></li>
              <li><button onClick={() => onNavigate('analytics')} className="hover:text-emerald-400 transition">Environmental Analytics</button></li>
            </ul>
          </div>

          {/* Col 3: Research & Datasets */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-3">Datasets & Backbones</h4>
            <ul className="space-y-2">
              <li className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span>TrashNet Benchmark (Gary Thung)</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                <span>RealWaste Dataset (UCI Repository)</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                <span>TACO Litter Contexts (COCO format)</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                <span>MobileNetV3 & YOLOv8 Architectures</span>
              </li>
            </ul>
          </div>

          {/* Col 4: Scientific Reference */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-3">Documented Metrics</h4>
            <p className="text-slate-400 leading-relaxed mb-3">
              Carbon and energy savings are derived from published peer-reviewed conversion factors:
            </p>
            <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/80 space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span>US EPA WARM v15</span>
                <span className="text-emerald-400 font-mono">Verified</span>
              </div>
              <div className="flex justify-between">
                <span>EEA Plastics Directives</span>
                <span className="text-emerald-400 font-mono">Verified</span>
              </div>
              <div className="flex justify-between">
                <span>WRAP UK Footwear & Textiles</span>
                <span className="text-emerald-400 font-mono">Verified</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-slate-500">
          <p>© 2026 EcoSort AI. All predictions computed with locally trained PyTorch models.</p>
          <div className="flex items-center gap-4">
            <span className="text-slate-400">FastAPI + React 18 + Tailwind CSS + MongoDB</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

