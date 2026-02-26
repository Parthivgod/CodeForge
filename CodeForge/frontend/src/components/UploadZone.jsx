import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, GitBranch, Github, Loader2, X } from 'lucide-react';
import clsx from 'clsx';

const UploadZone = ({ onUpload, onGitAnalyze, loading, onBack }) => {
    const [activeTab, setActiveTab] = useState('upload');
    const [dragActive, setDragActive] = useState(false);
    const [gitUrl, setGitUrl] = useState('');

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            onUpload(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            onUpload(e.target.files[0]);
        }
    };

    return (
        <div className="w-full max-w-2xl mx-auto -mt-20 relative z-10 p-6">
            <div className="glass-card rounded-2xl p-2 md:p-8">

                {/* Tabs */}
                {onBack && (
                    <button
                        onClick={onBack}
                        className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-full transition-all z-20"
                        title="Go Back"
                    >
                        <X className="w-5 h-5" />
                    </button>
                )}

                <div className="flex bg-slate-900/50 p-1 rounded-xl mb-6 w-fit mx-auto border border-white/5">
                    <button
                        onClick={() => setActiveTab('upload')}
                        className={clsx(
                            "px-6 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                            activeTab === 'upload' ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-white"
                        )}
                    >
                        <Upload className="w-4 h-4" /> Upload ZIP
                    </button>
                    <button
                        onClick={() => setActiveTab('git')}
                        className={clsx(
                            "px-6 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                            activeTab === 'git' ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-white"
                        )}
                    >
                        <Github className="w-4 h-4" /> Git Repo
                    </button>
                </div>

                <AnimatePresence mode="wait">
                    {activeTab === 'upload' ? (
                        <motion.div
                            key="upload"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            className={clsx(
                                "relative border-2 border-dashed rounded-xl p-10 text-center transition-all min-h-[250px] flex flex-col items-center justify-center",
                                dragActive ? "border-blue-500 bg-blue-500/10" : "border-slate-700 hover:border-blue-500/50 hover:bg-slate-800/30",
                                loading && "opacity-50 pointer-events-none"
                            )}
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                        >
                            <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" onChange={handleChange} accept=".zip" />
                            <div className="bg-blue-600/20 p-4 rounded-full mb-4">
                                <Upload className="w-8 h-8 text-blue-500" />
                            </div>
                            <h3 className="text-xl font-bold mb-2">Drag & Drop Codebase</h3>
                            <p className="text-slate-400 mb-6 text-sm">Supports .zip archives (Max 50MB)</p>
                            {loading && <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm rounded-xl"><Loader2 className="w-10 h-10 animate-spin text-blue-500" /></div>}
                        </motion.div>
                    ) : (
                        <motion.div
                            key="git"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="min-h-[250px] flex flex-col items-center justify-center space-y-4"
                        >
                            <div className="w-full">
                                <label className="block text-sm font-medium text-slate-300 mb-2">Repository URL</label>
                                <div className="relative">
                                    <GitBranch className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                                    <input
                                        type="text"
                                        placeholder="https://github.com/org/repo.git"
                                        value={gitUrl}
                                        onChange={(e) => setGitUrl(e.target.value)}
                                        className="w-full bg-slate-900 border border-slate-700 rounded-xl py-4 pl-12 pr-4 text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                                    />
                                </div>
                            </div>
                            <button
                                onClick={() => onGitAnalyze(gitUrl)}
                                disabled={!gitUrl || loading}
                                className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl font-bold text-white shadow-lg hover:shadow-blue-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader2 className="animate-spin w-5 h-5" /> : 'Clone & Analyze'}
                            </button>
                            <p className="text-xs text-slate-500">Authentication token support coming soon.</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default UploadZone;
