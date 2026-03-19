import React from 'react';
import { Download, RotateCcw } from 'lucide-react';

const ActionBar = ({ onDownload, onReset }) => {
    return (
        <div className="flex items-center gap-2">
            <button
                onClick={onDownload}
                aria-label="Download analysis report"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400 focus-visible:outline-offset-2"
                style={{
                    background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                    boxShadow: '0 2px 10px rgba(59,130,246,0.25)',
                }}
                onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 18px rgba(59,130,246,0.4)'}
                onMouseLeave={e => e.currentTarget.style.boxShadow = '0 2px 10px rgba(59,130,246,0.25)'}
            >
                <Download className="w-4 h-4" aria-hidden="true" />
                <span className="hidden sm:inline">Download Report</span>
            </button>

            <button
                onClick={onReset}
                aria-label="Start new analysis"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-slate-300 transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400 focus-visible:outline-offset-2"
                style={{
                    background: 'rgba(30,41,59,0.6)',
                    border: '1px solid rgba(255,255,255,0.08)',
                }}
                onMouseEnter={e => {
                    e.currentTarget.style.background = 'rgba(30,41,59,0.95)';
                    e.currentTarget.style.color = '#f1f5f9';
                }}
                onMouseLeave={e => {
                    e.currentTarget.style.background = 'rgba(30,41,59,0.6)';
                    e.currentTarget.style.color = '';
                }}
            >
                <RotateCcw className="w-4 h-4" aria-hidden="true" />
                <span className="hidden sm:inline">New Analysis</span>
            </button>
        </div>
    );
};

export default ActionBar;
