import { useState } from 'react';
import { analyzeMonolith, getStatus, getResults } from './api';
import HeroSection from './components/HeroSection';
import HowItWorks from './components/HowItWorks';
import Footer from './components/Footer';
import UploadZone from './components/UploadZone';
import ResultsDashboard from './components/ResultsDashboard';
import AnalysisStepper from './components/AnalysisStepper';
import { Loader2, AlertTriangle, X } from 'lucide-react';

function App() {
    const [view,    setView]    = useState('hero');
    const [loading, setLoading] = useState(false);
    const [jobId,   setJobId]   = useState(null);
    const [status,  setStatus]  = useState(null);
    const [results, setResults] = useState(null);
    const [error,   setError]   = useState(null);

    const handleStart = () => setView('analysis');

    const handleAnalysis = async (input) => {
        setLoading(true);
        setError(null);
        setResults(null);
        try {
            const res = await analyzeMonolith(input);
            setJobId(res.job_id);
            pollStatus(res.job_id);
        } catch (e) {
            console.error(e);
            setError(e.response?.data?.error || e.message || 'Analysis failed. Please try again.');
            setLoading(false);
        }
    };

    const pollStatus = (id) => {
        let errorCount = 0;
        const maxErrors = 3;
        const interval = setInterval(async () => {
            try {
                const res = await getStatus(id);
                errorCount = 0;
                setStatus(res.status);
                if (res.status === 'Done') {
                    clearInterval(interval);
                    try {
                        const completeResults = await getResults(id);
                        setResults(completeResults);
                        setLoading(false);
                        setView('results');
                    } catch (fetchErr) {
                        console.error('Error fetching results:', fetchErr);
                        setError('Failed to download analysis results. The server may have restarted.');
                        setLoading(false);
                    }
                } else if (res.status.startsWith('Failed')) {
                    clearInterval(interval);
                    setLoading(false);
                    setError(res.status);
                }
            } catch (err) {
                console.error('Polling error:', err);
                if (++errorCount >= maxErrors) {
                    clearInterval(interval);
                    setLoading(false);
                    setError('Lost connection to backend. The server may have restarted. Please try again.');
                }
            }
        }, 2000);
    };

    const handleReset = () => {
        setView('hero');
        setResults(null);
        setJobId(null);
        setStatus(null);
        setError(null);
    };

    const getStepData = () => {
        if (!status) return { step: 0, message: 'Initializing…' };
        try {
            const parsed = JSON.parse(status);
            return { step: parsed.step, message: parsed.message };
        } catch {
            if (status === 'Done') return { step: 7, message: 'Complete' };
            return { step: 1, message: status };
        }
    };
    const { step, message } = getStepData();

    return (
        <div
            className="min-h-dvh text-white overflow-x-hidden"
            style={{ background: '#0a0f1e', fontFamily: "'Inter', 'SF Pro Display', system-ui, -apple-system, sans-serif" }}
        >
            {/* Global subtle grid layer */}
            <div className="fixed inset-0 bg-grid pointer-events-none z-0 opacity-60" aria-hidden="true" />

            <div className="relative z-10 w-full">
                {/* ── Hero view ──────────────────────────────────── */}
                {view === 'hero' && (
                    <>
                        <HeroSection onStart={handleStart} />
                        <HowItWorks />
                        <Footer />
                    </>
                )}

                {/* ── Analysis view ──────────────────────────────── */}
                {view === 'analysis' && (
                    <main
                        className="min-h-dvh flex flex-col items-center pt-20 pb-16 px-4"
                        aria-label="Code analysis"
                    >
                        {/* Page heading */}
                        <div className="text-center mb-12 max-w-2xl">
                            <h1 className="text-4xl md:text-5xl font-extrabold mb-4 leading-tight"
                                style={{
                                    backgroundImage: 'linear-gradient(135deg, #ffffff, #94a3b8)',
                                    backgroundClip: 'text',
                                    WebkitBackgroundClip: 'text',
                                    color: 'transparent',
                                    WebkitTextFillColor: 'transparent',
                                }}
                            >
                                Analyze Your Codebase
                            </h1>
                            <p className="text-slate-400 text-lg leading-relaxed">
                                Upload your code to generate a Code Property Graph, discover relationships,
                                and identify security risks with AI-powered analysis.
                            </p>
                        </div>

                        {/* Upload card */}
                        <UploadZone
                            onUpload={handleAnalysis}
                            onGitAnalyze={handleAnalysis}
                            onBack={() => setView('hero')}
                            loading={loading}
                        />

                        {/* Loading / stepper */}
                        {loading && (
                            <div className="mt-12 w-full max-w-2xl" role="status" aria-live="polite" aria-label="Analysis in progress">
                                <div className="flex flex-col items-center mb-8">
                                    <div className="relative">
                                        <div
                                            className="absolute inset-0 rounded-full"
                                            style={{ background: 'rgba(59,130,246,0.2)', filter: 'blur(16px)' }}
                                            aria-hidden="true"
                                        />
                                        <Loader2 className="w-12 h-12 text-blue-400 animate-spin relative z-10" aria-hidden="true" />
                                    </div>
                                    <p className="mt-4 text-blue-400 font-mono text-sm tracking-wide">
                                        Deep Code Analysis in Progress
                                    </p>
                                </div>

                                <div className="glass-card rounded-2xl p-8">
                                    <AnalysisStepper currentStep={step} message={message} />
                                </div>
                            </div>
                        )}

                        {/* Error state */}
                        {error && (
                            <div
                                className="mt-8 w-full max-w-2xl rounded-2xl p-5"
                                style={{
                                    background: 'rgba(239,68,68,0.07)',
                                    border: '1px solid rgba(239,68,68,0.22)',
                                }}
                                role="alert"
                                aria-live="assertive"
                            >
                                <div className="flex items-center gap-3 mb-3">
                                    <div
                                        className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
                                        style={{ background: 'rgba(239,68,68,0.15)' }}
                                        aria-hidden="true"
                                    >
                                        <AlertTriangle className="w-4 h-4 text-red-400" />
                                    </div>
                                    <h2 className="text-sm font-bold text-red-200">Analysis Failed</h2>
                                </div>

                                <pre
                                    className="text-xs font-mono text-red-300 leading-relaxed whitespace-pre-wrap break-words p-3 rounded-xl overflow-x-auto"
                                    style={{ background: 'rgba(0,0,0,0.25)' }}
                                >
                                    {error}
                                </pre>

                                <button
                                    onClick={() => setError(null)}
                                    aria-label="Dismiss error"
                                    className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-red-300 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-400"
                                    style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.2)' }}
                                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(239,68,68,0.2)'}
                                    onMouseLeave={e => e.currentTarget.style.background = 'rgba(239,68,68,0.12)'}
                                >
                                    <X className="w-3.5 h-3.5" aria-hidden="true" />
                                    Dismiss
                                </button>
                            </div>
                        )}
                    </main>
                )}

                {/* ── Results view ───────────────────────────────── */}
                {view === 'results' && results && (
                    <ResultsDashboard results={results} jobId={jobId} onReset={handleReset} />
                )}
            </div>
        </div>
    );
}

export default App;
