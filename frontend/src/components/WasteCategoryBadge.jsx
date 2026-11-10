import React from 'react';
import { 
  Leaf, 
  FileText, 
  Package, 
  ShieldAlert, 
  Wine, 
  Cpu, 
  AlertTriangle, 
  Shirt, 
  Trash2,
  HelpCircle 
} from 'lucide-react';

export const CATEGORY_CONFIG = {
  organic_waste: {
    label: 'Organic Waste',
    color: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    dot: 'bg-emerald-500',
    icon: Leaf,
    binColor: '#2E8B57'
  },
  paper_waste: {
    label: 'Paper & Cardboard',
    color: 'bg-amber-100 text-amber-800 border-amber-300',
    dot: 'bg-amber-500',
    icon: FileText,
    binColor: '#CD853F'
  },
  plastic_waste: {
    label: 'Plastic Waste',
    color: 'bg-blue-100 text-blue-800 border-blue-300',
    dot: 'bg-blue-500',
    icon: Package,
    binColor: '#1E90FF'
  },
  metal_waste: {
    label: 'Metal Waste',
    color: 'bg-slate-200 text-slate-800 border-slate-300',
    dot: 'bg-slate-500',
    icon: Package,
    binColor: '#708090'
  },
  glass_waste: {
    label: 'Glass Waste',
    color: 'bg-cyan-100 text-cyan-800 border-cyan-300',
    dot: 'bg-cyan-500',
    icon: Wine,
    binColor: '#00BFFF'
  },
  electronic_waste: {
    label: 'Electronic Waste',
    color: 'bg-purple-100 text-purple-800 border-purple-300',
    dot: 'bg-purple-500',
    icon: Cpu,
    binColor: '#8A2BE2'
  },
  hazardous_waste: {
    label: 'Hazardous Waste',
    color: 'bg-rose-100 text-rose-800 border-rose-300',
    dot: 'bg-rose-500',
    icon: AlertTriangle,
    binColor: '#DC143C'
  },
  textile_waste: {
    label: 'Textile Waste',
    color: 'bg-fuchsia-100 text-fuchsia-800 border-fuchsia-300',
    dot: 'bg-fuchsia-500',
    icon: Shirt,
    binColor: '#DA70D6'
  },
  residual_waste: {
    label: 'Residual Waste',
    color: 'bg-zinc-200 text-zinc-700 border-zinc-300',
    dot: 'bg-zinc-500',
    icon: Trash2,
    binColor: '#696969'
  },
  uncertain: {
    label: 'Uncertain / Low Confidence',
    color: 'bg-slate-100 text-slate-700 border-slate-300',
    dot: 'bg-slate-400',
    icon: HelpCircle,
    binColor: '#64748B'
  }
};

export default function WasteCategoryBadge({ category, showIcon = true, size = 'md' }) {
  const norm = (category || 'residual_waste').toLowerCase().replace(' ', '_');
  const config = CATEGORY_CONFIG[norm] || CATEGORY_CONFIG['residual_waste'];
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs font-medium px-2.5 py-1 gap-1.5',
    lg: 'text-sm font-semibold px-3 py-1.5 gap-2'
  }[size];

  return (
    <span className={`inline-flex items-center rounded-full border ${config.color} ${sizeClasses}`}>
      {showIcon && <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />}
      <span>{config.label}</span>
    </span>
  );
}
