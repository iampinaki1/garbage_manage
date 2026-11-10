import React from 'react';
import { 
  ArrowRight, 
  ScanLine, 
  Layers, 
  Recycle, 
  Sparkles, 
  ShieldCheck, 
  MapPin, 
  Cpu, 
  Zap, 
  CheckCircle2, 
  BarChart3,
  Flame,
  Globe2
} from 'lucide-react';

export default function LandingPage({ onGetStarted }) {
  const steps = [
    {
      num: '01',
      title: 'Image Capture & Validation',
      desc: 'Upload any waste or litter photograph. The system verifies resolution, formats, and structural integrity.',
      icon: ScanLine,
      color: 'from-blue-500 to-cyan-500'
    },
    {
      num: '02',
      title: 'YOLO Multi-Object Localization',
      desc: 'Ultralytics YOLOv8 nano model detects multiple waste items simultaneously, computing pixel coordinates and bounding boxes.',
      icon: Layers,
      color: 'from-purple-500 to-indigo-500'
    },
    {
      num: '03',
      title: 'MobileNetV3 Classification',
      desc: 'Extracted object ROIs are passed through a MobileNetV3-Small classifier (91% accuracy) to identify material composition.',
      icon: Cpu,
      color: 'from-emerald-500 to-teal-500'
    },
    {
      num: '04',
      title: 'Localized Segregation & Carbon Accounting',
      desc: 'Guidance engine maps the item to your regional bin color (US, EU, UK, India) and calculates EPA WARM CO2 & kWh savings.',
      icon: Recycle,
      color: 'from-amber-500 to-orange-500'
    }
  ];

  const features = [
    {
      title: 'Locally Trained PyTorch Models',
      desc: 'Zero reliance on paid or external vision APIs. Inference runs entirely on local GPU/CPU hardware with verified validation curves.',
      icon: ShieldCheck,
      tag: 'Self-Contained'
    },
    {
      title: '9 Canonical Waste Categories',
      desc: 'Unified taxonomy harmonizing TrashNet, RealWaste, and TACO: Organic, Paper, Plastic, Metal, Glass, E-Waste, Hazardous, Textile, and Residual.',
      icon: Layers,
      tag: 'Comprehensive'
    },
    {
      title: 'Regional Bin Customization',
      desc: 'Configurable disposal rules dynamically adapt for US EPA, European Union Dual System, UK WRAP, and India CPCB standards.',
      icon: MapPin,
      tag: 'Localized'
    },
    {
      title: 'Contamination Risk Detection',
      desc: 'Prevents batch fouling at recycling centers by automatically detecting greasy pizza boxes, soiled wrappers, and non-recyclable polymers.',
      icon: Zap,
      tag: 'Safeguard'
    },
    {
      title: 'EPA WARM Carbon Calculations',
      desc: 'Transparent energy and greenhouse gas avoidance metrics based on documented life-cycle analysis factors with zero invented numbers.',
      icon: BarChart3,
      tag: 'Scientific'
    },
    {
      title: 'Full Audit Trail & Analytics',
      desc: 'Every scan is recorded in MongoDB with bounding box crops, confidence ratings, and aggregate landfill diversion telemetry.',
      icon: Globe2,
      tag: 'Data-Driven'
    }
  ];

  return (
    <div className="space-y-24 py-8">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-16">
        <div className="absolute inset-0 -z-10 flex items-center justify-center">
          <div className="w-[600px] h-[600px] bg-emerald-400/10 rounded-full blur-3xl pointer-events-none" />
          <div className="w-[400px] h-[400px] bg-teal-400/10 rounded-full blur-2xl pointer-events-none" />
        </div>

        <div className="max-w-4xl mx-auto text-center px-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-100/80 border border-emerald-200 text-emerald-800 text-xs font-semibold mb-6 shadow-sm">
            <Sparkles className="w-4 h-4 text-emerald-600" />
            <span>Dual-Model AI Architecture • 91.0% Test Accuracy • Zero Cloud APIs</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-black text-slate-900 tracking-tight leading-[1.1] mb-6">
            Autonomous Waste Segregation & <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600">Recycling Intelligence</span>
          </h1>

          <p className="text-lg sm:text-xl text-slate-600 leading-relaxed max-w-2xl mx-auto mb-10">
            A production-grade machine learning platform combining <strong>Ultralytics YOLO multi-object detection</strong>, <strong>MobileNetV3 material classification</strong>, and localized recycling instructions calibrated to documented EPA carbon reduction standards.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => onGetStarted('analyze')}
              className="w-full sm:w-auto px-8 py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-2xl shadow-lg shadow-emerald-600/25 flex items-center justify-center gap-2 transition hover:-translate-y-0.5"
            >
              <span>Start Waste Analysis</span>
              <ArrowRight className="w-5 h-5" />
            </button>
            <button
              onClick={() => onGetStarted('dashboard')}
              className="w-full sm:w-auto px-8 py-4 bg-white hover:bg-slate-50 text-slate-700 font-bold rounded-2xl border border-slate-200 shadow-sm transition"
            >
              View Analytics Dashboard
            </button>
          </div>
        </div>
      </section>

      {/* Trust & Model Badges */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-6 bg-white/70 backdrop-blur-md rounded-3xl border border-slate-200/80 shadow-sm text-center">
          <div>
            <div className="text-3xl font-black text-emerald-600">91.00%</div>
            <div className="text-xs font-medium text-slate-500 mt-1">Model A Classifier Accuracy</div>
          </div>
          <div>
            <div className="text-3xl font-black text-teal-600">9 Classes</div>
            <div className="text-xs font-medium text-slate-500 mt-1">Unified Waste Categories</div>
          </div>
          <div>
            <div className="text-3xl font-black text-indigo-600">YOLOv8</div>
            <div className="text-xs font-medium text-slate-500 mt-1">Multi-Object Detector</div>
          </div>
          <div>
            <div className="text-3xl font-black text-amber-600">EPA WARM</div>
            <div className="text-xs font-medium text-slate-500 mt-1">Life-Cycle Conversion Factors</div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">System Workflow</span>
          <h2 className="text-3xl font-bold text-slate-900 mt-2">How EcoSort AI Processes Waste</h2>
          <p className="text-slate-500 text-sm mt-2">
            A synchronized four-tier architecture turning raw visual inputs into actionable consumer preparation steps and real-world carbon diversion metrics.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <div key={step.num} className="relative bg-white rounded-3xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition">
                <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${step.color} text-white flex items-center justify-center mb-6 shadow-md`}>
                  <Icon className="w-6 h-6" />
                </div>
                <span className="text-xs font-extrabold text-slate-300 tracking-wider mb-2 block">{step.num}</span>
                <h3 className="text-base font-bold text-slate-900 mb-2">{step.title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{step.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Key Feature Highlights */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">Enterprise Capabilities</span>
          <h2 className="text-3xl font-bold text-slate-900 mt-2">Built for Real-World Environmental Impact</h2>
          <p className="text-slate-500 text-sm mt-2">
            Engineered to solve the primary bottlenecks in modern municipal recycling: inaccurate sorting, contamination, and opaque impact accounting.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <div key={idx} className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm hover:border-emerald-300 transition-colors">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl border border-emerald-100">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
                    {feat.tag}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-2">{feat.title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{feat.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* CTA Box */}
      <section className="max-w-5xl mx-auto px-4">
        <div className="bg-gradient-to-br from-emerald-600 via-teal-700 to-slate-900 text-white rounded-3xl p-8 sm:p-12 shadow-xl relative overflow-hidden">
          <div className="absolute right-0 top-0 translate-x-12 -translate-y-12 w-64 h-64 bg-white/10 rounded-full blur-2xl" />
          
          <div className="max-w-2xl">
            <span className="text-xs font-bold uppercase tracking-widest text-emerald-300 mb-2 block">Take Action Today</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold mb-4">Ready to Automate Your Waste Segregation?</h2>
            <p className="text-emerald-100 text-sm leading-relaxed mb-8">
              Upload an image of single or mixed litter items to receive instant bounding box overlays, localized bin routing, and quantified carbon emissions saved.
            </p>
            <button
              onClick={() => onGetStarted('analyze')}
              className="px-8 py-3.5 bg-white text-emerald-900 hover:bg-emerald-50 font-bold rounded-2xl shadow-lg transition flex items-center gap-2"
            >
              <span>Inspect an Item Now</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

