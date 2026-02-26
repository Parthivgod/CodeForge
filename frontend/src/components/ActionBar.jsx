import React from 'react';
import { Download, Rocket, RotateCcw } from 'lucide-react';

const ActionBar = ({ onDeploy, onDownload, onReset }) => {
    return (
        <div className="glass p-6 rounded-xl space-y-4">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Deployment Actions</h3>

            <button
                onClick={onDownload}
                className="w-full flex items-center justify-between p-4 bg-slate-800/80 hover:bg-slate-700 rounded-lg transition-all border border-white/5 group"
            >
                <span className="flex items-center gap-3 font-medium text-slate-200">
                    <Download className="w-5 h-5 text-blue-400 group-hover:scale-110 transition-transform" />
                    Download Report
                </span>
            </button>

            <button
                onClick={onDeploy}
                className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 rounded-lg transition-all shadow-lg hover:shadow-blue-500/25 group"
            >
                <span className="flex items-center gap-3 font-bold text-white">
                    <Rocket className="w-5 h-5 text-white group-hover:-translate-y-1 transition-transform" />
                    Deploy to Azure
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
