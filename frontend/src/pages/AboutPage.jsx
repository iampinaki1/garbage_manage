import React from 'react';
import { 
  Info, 
  Cpu, 
  Layers, 
  Database, 
  ShieldCheck, 
  Award, 
  ExternalLink,
  Code2,
  Server,
  FileCheck
} from 'lucide-react';
import WasteCategoryBadge from '../components/WasteCategoryBadge';

export default function AboutPage() {
  const datasets = [
    {
      name: 'TrashNet',
      author: 'Gary Thung & Mindy Yang',
      size: '2,527 images',
      classes: 'Glass, Paper, Cardboard, Plastic, Metal, Trash',
      source: 'GitHub Academic Release',
      role: 'Primary laboratory classification baseline'
    },
    {
      name: 'RealWaste',
      author: 'UCI Machine Learning Repository',
      size: '4,752 images',
      classes: 'Cardboard, Food Organics, Glass, Metal, Miscellaneous Trash, Paper, Plastic, Textile, Vegetation',
      source: 'UCI ML Repository (CC BY 4.0)',
      role: 'Real-world landfill & organic diversity'
    },
    {
      name: 'TACO (Trash Annotations in Context)',
      author: 'Pedro F. Proença & Pedro Simões',
      size: '1,500 images / 4,784 bounding boxes',
      classes: '60 raw categories mapped into 9 canonical classes',
      source: 'COCO Annotation Format / Flickr',
      role: 'Multi-object localization in cluttered outdoor environments'
    }
  ];

  const techStack = [
    { name: 'FastAPI', role: 'High-performance Python asynchronous REST backend', badge: 'v0.115' },
    { name: 'PyTorch', role: 'CUDA 12.1 GPU accelerated deep learning engine', badge: 'v2.5.1+cu121' },
    { name: 'Ultralytics YOLOv8', role: 'Multi-object real-time bounding box detector', badge: 'v8.4' },
    { name: 'MobileNetV3', role: 'Efficient lightweight transfer learning backbone', badge: 'Small' },
    { name: 'React 18 & Vite', role: 'Component-driven reactive user interface', badge: 'v18.3' },
    { name: 'Tailwind CSS', role: 'Utility-first modern SaaS design system', badge: 'v3.4' },
    { name: 'MongoDB', role: 'Community Server 8.2 persistent document database', badge: 'v8.2' },
    { name: 'Recharts', role: 'Responsive SVG environmental telemetry charts', badge: 'v2.15' }
  ];

  return (
    <div className="space-y-12 py-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-800 text-xs font-semibold mb-2">
          <Info className="w-3.5 h-3.5" />
          <span>System Architecture & Scientific Basis</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">About EcoSort AI</h1>
        <p className="text-sm text-slate-500 mt-2 max-w-2xl">
          An end-to-end intelligent waste segregation system designed to eliminate contamination at the point of disposal using local computer vision and life-cycle carbon accounting.
        </p>
      </div>

      {/* Project Objectives */}
      <section className="bg-white rounded-3xl p-8 border border-slate-200/90 shadow-sm space-y-4">
        <h2 className="text-xl font-bold text-slate-900">Project Objectives</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-2">
            <span className="w-7 h-7 rounded-lg bg-emerald-600 text-white font-bold flex items-center justify-center text-xs">1</span>
            <h3 className="font-bold text-sm text-slate-800">Eliminate Cloud Vision APIs</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Ensure data privacy, offline resilience, and zero API costs by training and deploying localized PyTorch and YOLO models.
            </p>
          </div>
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-2">
            <span className="w-7 h-7 rounded-lg bg-teal-600 text-white font-bold flex items-center justify-center text-xs">2</span>
            <h3 className="font-bold text-sm text-slate-800">Multi-Object Localization</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Detect and classify multiple items in cluttered real-world photographs instead of requiring isolated laboratory captures.
            </p>
          </div>
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-2">
            <span className="w-7 h-7 rounded-lg bg-indigo-600 text-white font-bold flex items-center justify-center text-xs">3</span>
            <h3 className="font-bold text-sm text-slate-800">Actionable & Localized Advice</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Translate machine labels into regional bin colors (US, EU, UK, India) with explicit contamination warnings and EPA carbon metrics.
            </p>
          </div>
        </div>
      </section>

      {/* Deep Learning Models */}
      <section className="space-y-6">
        <h2 className="text-xl font-bold text-slate-900">Model Architectures & Evaluation</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Model A */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <span className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100">
                <Cpu className="w-5 h-5" />
              </span>
              <span className="text-xs font-bold px-2.5 py-1 bg-emerald-100 text-emerald-800 rounded-full">
                91.00% Test Accuracy
              </span>
            </div>
            <div>
              <h3 className="text-base font-extrabold text-slate-900">Model A: Fine-Grained Classifier</h3>
              <p className="text-xs text-slate-500 mt-1">MobileNetV3-Small transfer learning backbone</p>
            </div>
            <ul className="space-y-2 text-xs text-slate-600 border-t border-slate-100 pt-3">
              <li className="flex justify-between">
                <span>Validation Loss</span>
                <span className="font-mono font-bold text-slate-900">0.2971</span>
              </li>
              <li className="flex justify-between">
                <span>Macro Precision</span>
                <span className="font-mono font-bold text-slate-900">89.40%</span>
              </li>
              <li className="flex justify-between">
                <span>Macro Recall</span>
                <span className="font-mono font-bold text-slate-900">89.54%</span>
              </li>
              <li className="flex justify-between">
                <span>Macro F1-Score</span>
                <span className="font-mono font-bold text-slate-900">89.39%</span>
              </li>
              <li className="flex justify-between">
                <span>Inference Device</span>
                <span className="font-bold text-emerald-700">CUDA (RTX 4050) / CPU</span>
              </li>
            </ul>
          </div>

          {/* Model B */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <span className="p-2.5 bg-purple-50 text-purple-600 rounded-xl border border-purple-100">
                <Layers className="w-5 h-5" />
              </span>
              <span className="text-xs font-bold px-2.5 py-1 bg-purple-100 text-purple-800 rounded-full">
                YOLOv8 Nano
              </span>
            </div>
            <div>
              <h3 className="text-base font-extrabold text-slate-900">Model B: Multi-Object Detector</h3>
              <p className="text-xs text-slate-500 mt-1">Ultralytics YOLO fine-tuned on TACO annotations</p>
            </div>
            <ul className="space-y-2 text-xs text-slate-600 border-t border-slate-100 pt-3">
              <li className="flex justify-between">
                <span>mAP@50</span>
                <span className="font-mono font-bold text-slate-900">17.95%</span>
              </li>
              <li className="flex justify-between">
                <span>mAP@50-95</span>
                <span className="font-mono font-bold text-slate-900">14.63%</span>
              </li>
              <li className="flex justify-between">
                <span>Detector Precision</span>
                <span className="font-mono font-bold text-slate-900">79.05%</span>
              </li>
              <li className="flex justify-between">
                <span>Parameters</span>
                <span className="font-mono font-bold text-slate-900">3.13M (8.6 GFLOPs)</span>
              </li>
              <li className="flex justify-between">
                <span>Output Features</span>
                <span className="font-bold text-purple-700">Bounding boxes & ROI crops</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Datasets Employed */}
      <section className="bg-white rounded-3xl p-8 border border-slate-200/90 shadow-sm space-y-6">
        <h2 className="text-xl font-bold text-slate-900">Benchmark Datasets & Taxonomy</h2>
        <div className="space-y-4">
          {datasets.map((d, i) => (
            <div key={i} className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="space-y-0.5">
                <h3 className="font-extrabold text-slate-900 text-sm">{d.name}</h3>
                <p className="text-slate-500">{d.author} • {d.source}</p>
                <p className="text-[11px] text-emerald-700 font-semibold">{d.role}</p>
              </div>
              <div className="text-left sm:text-right shrink-0">
                <span className="inline-block px-2.5 py-1 bg-white border border-slate-200 rounded-lg font-bold text-slate-700">
                  {d.size}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Technology Stack Grid */}
      <section className="bg-white rounded-3xl p-8 border border-slate-200/90 shadow-sm space-y-6">
        <h2 className="text-xl font-bold text-slate-900">Technology Stack & Libraries</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {techStack.map((tech, idx) => (
            <div key={idx} className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-1 text-xs">
              <div className="flex items-center justify-between">
                <h3 className="font-extrabold text-slate-900">{tech.name}</h3>
                <span className="font-mono text-[10px] text-slate-400 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                  {tech.badge}
                </span>
              </div>
              <p className="text-slate-500 text-[11px] leading-relaxed">{tech.role}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

