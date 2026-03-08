import React from 'react';
import { Download, RotateCcw } from 'lucide-react';

const ActionBar = ({ onDownload, onReset }) => {
    return (
        <div className="glass p-6 rounded-xl space-y-4">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Deployment Actions</h3>

            <button
                onClick={onDownload}
                className="w-full flex items-center justify-center p-4 bg-slate-800/80 hover:bg-slate-700 rounded-lg transition-all border border-white/5 group"
            >
                <span className="flex items-center gap-3 font-medium text-slate-200">
                    <Download className="w-5 h-5 text-blue-400 group-hover:scale-110 transition-transform" />
                    Download Report
                </span>
            </button>

            <div className="pt-4 border-t border-white/10 mt-4">
                <button
                    onClick={onReset}
                    className="w-full text-xs text-slate-500 hover:text-slate-300 flex items-center justify-center gap-2 py-2"
                >
                    <RotateCcw className="w-3 h-3" /> Start New Analysis
                </button>
            </div>
        </div>
    );
};

export default ActionBar;
