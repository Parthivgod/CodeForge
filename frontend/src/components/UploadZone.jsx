import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, GitBranch, Github, Loader2, ArrowLeft, CloudUpload } from 'lucide-react';
import clsx from 'clsx';

const UploadZone = ({ onUpload, onGitAnalyze, loading, onBack }) => {
    const [activeTab, setActiveTab] = useState('upload');
    const [dragActive, setDragActive] = useState(false);
    const [gitUrl, setGitUrl] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
        else if (e.type === 'dragleave') setDragActive(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        const file = e.dataTransfer.files?.[0];
        if (file) { setSelectedFile(file); onUpload(file); }
    };

    const handleChange = (e) => {
        const file = e.target.files?.[0];
        if (file) { setSelectedFile(file); onUpload(file); }
    };

    return (
        <div className="w-full max-w-2xl mx-auto">
            <div
                className="relative rounded-2xl p-6 md:p-8"
                style={{
                    background: 'linear-gradient(145deg, rgba(30,41,59,0.88), rgba(10,15,30,0.82))',
                    border: '1px solid rgba(255,255,255,0.07)',
                    backdropFilter: 'blur(14px)',
                    boxShadow: '0 16px 48px rgba(0,0,0,0.55), 0 0 1px rgba(255,255,255,0.05)',
                }}
            >
                {/* Back button */}
                {onBack && (
                    <button
                        onClick={onBack}
                        aria-label="Go back"
                        className="absolute top-4 left-4 inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-100 transition-colors duration-150 px-3 py-1.5 rounded-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
                        style={{ background: 'rgba(255,255,255,0.05)' }}
                    >
                        <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
                        Back
                    </button>
                )}

                {/* Tabs */}
                <div
                    className="flex p-1 rounded-xl mb-6 w-fit mx-auto"
                    role="tablist"
                    aria-label="Input method"
                    style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(255,255,255,0.06)' }}
                >
                    {[
                        { id: 'upload', icon: Upload,    label: 'Upload ZIP' },
                        { id: 'git',    icon: Github,    label: 'Git Repo' },
                    ].map(({ id, icon: Icon, label }) => (
                        <button
                            key={id}
                            role="tab"
                            aria-selected={activeTab === id}
                            aria-controls={`panel-${id}`}
                            id={`tab-${id}`}
                            onClick={() => setActiveTab(id)}
                            className={clsx(
                                'inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400',
                                activeTab === id
                                    ? 'text-white shadow-md'
                                    : 'text-slate-400 hover:text-slate-200'
                            )}
                            style={activeTab === id
                                ? { background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)', boxShadow: '0 2px 10px rgba(59,130,246,0.3)' }
                                : {}
                            }
                        >
                            <Icon className="w-4 h-4" aria-hidden="true" />
                            {label}
                        </button>
                    ))}
                </div>

                <AnimatePresence mode="wait">
                    {activeTab === 'upload' ? (
                        <motion.div
                            key="upload"
                            id="panel-upload"
                            role="tabpanel"
                            aria-labelledby="tab-upload"
                            initial={{ opacity: 0, x: -12 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 12 }}
                            transition={{ duration: 0.2 }}
                        >
                            <label
                                htmlFor="file-input"
                                className={clsx(
                                    'relative flex flex-col items-center justify-center rounded-xl p-10 text-center min-h-[240px] cursor-pointer transition-all duration-200',
                                    dragActive
                                        ? 'border-2 border-blue-500 bg-blue-500/08'
                                        : 'border-2 border-dashed hover:border-blue-500/50',
                                    loading && 'opacity-50 pointer-events-none'
                                )}
                                style={{
                                    borderColor: dragActive ? '#3b82f6' : 'rgba(100,116,139,0.4)',
                                    background: dragActive ? 'rgba(59,130,246,0.07)' : 'rgba(15,23,42,0.3)',
                                }}
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                            >
                                <input
                                    id="file-input"
                                    type="file"
                                    className="sr-only"
                                    onChange={handleChange}
                                    accept=".zip"
                                    aria-label="Upload ZIP archive"
                                    disabled={loading}
                                />

                                {loading ? (
                                    <div className="flex flex-col items-center gap-3">
                                        <Loader2 className="w-10 h-10 text-blue-500 animate-spin" aria-hidden="true" />
                                        <p className="text-sm text-blue-400 font-medium">Uploading…</p>
                                    </div>
                                ) : selectedFile ? (
                                    <div className="flex flex-col items-center gap-3">
                                        <div
                                            className="w-14 h-14 rounded-xl flex items-center justify-center"
                                            style={{ background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.25)' }}
                                            aria-hidden="true"
                                        >
                                            <CloudUpload className="w-7 h-7 text-emerald-400" />
                                        </div>
                                        <p className="text-base font-semibold text-slate-100">{selectedFile.name}</p>
                                        <p className="text-xs text-slate-500">
                                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB · Click to change
                                        </p>
                                    </div>
                                ) : (
                                    <>
                                        <div
                                            className="w-14 h-14 rounded-xl flex items-center justify-center mb-4"
                                            style={{ background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.2)' }}
                                            aria-hidden="true"
                                        >
                                            <Upload className="w-7 h-7 text-blue-400" />
                                        </div>
                                        <p className="text-lg font-semibold text-slate-100 mb-1">
                                            Drop your codebase here
                                        </p>
                                        <p className="text-sm text-slate-500 mb-4">or click to browse files</p>
                                        <span
                                            className="px-3 py-1 rounded-lg text-xs font-medium text-slate-400"
                                            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                                        >
                                            .zip · Max 50 MB
                                        </span>
                                    </>
                                )}
                            </label>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="git"
                            id="panel-git"
                            role="tabpanel"
                            aria-labelledby="tab-git"
                            initial={{ opacity: 0, x: 12 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -12 }}
                            transition={{ duration: 0.2 }}
                            className="min-h-[240px] flex flex-col justify-center space-y-4"
                        >
                            <div>
                                <label
                                    htmlFor="git-url"
                                    className="block text-sm font-medium text-slate-300 mb-2"
                                >
                                    Repository URL
                                </label>
                                <div className="relative">
                                    <GitBranch
                                        className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none"
                                        aria-hidden="true"
                                    />
                                    <input
                                        id="git-url"
                                        type="url"
                                        placeholder="https://github.com/org/repo.git"
                                        value={gitUrl}
                                        onChange={e => setGitUrl(e.target.value)}
                                        disabled={loading}
                                        autoComplete="url"
                                        className="w-full rounded-xl py-4 pl-11 pr-4 text-sm text-white placeholder-slate-600 transition-all duration-200 focus:outline-none disabled:opacity-50"
                                        style={{
                                            background: 'rgba(15,23,42,0.8)',
                                            border: '1px solid rgba(100,116,139,0.35)',
                                            boxShadow: 'inset 0 1px 4px rgba(0,0,0,0.3)',
                                        }}
                                        onFocus={e => e.currentTarget.style.borderColor = '#3b82f6'}
                                        onBlur={e => e.currentTarget.style.borderColor = 'rgba(100,116,139,0.35)'}
                                        aria-describedby="git-hint"
                                    />
                                </div>
                                <p id="git-hint" className="text-xs text-slate-600 mt-2">
                                    Authentication token support coming soon.
                                </p>
                            </div>

                            <button
                                onClick={() => onGitAnalyze(gitUrl)}
                                disabled={!gitUrl || loading}
                                aria-disabled={!gitUrl || loading}
                                className="w-full py-4 rounded-xl font-bold text-white text-sm transition-all duration-200 flex items-center justify-center gap-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400 focus-visible:outline-offset-2 disabled:opacity-40 disabled:cursor-not-allowed"
                                style={{
                                    background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                                    boxShadow: '0 4px 16px rgba(59,130,246,0.3)',
                                }}
                            >
                                {loading
                                    ? <><Loader2 className="animate-spin w-4 h-4" aria-hidden="true" /> Cloning…</>
                                    : 'Clone & Analyze'
                                }
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default UploadZone;
