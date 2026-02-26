import { useState } from 'react';
import { analyzeMonolith, getStatus, getResults } from './api';
import HeroSection from './components/HeroSection';
import UploadZone from './components/UploadZone';
import ResultsDashboard from './components/ResultsDashboard';
import AnalysisStepper from './components/AnalysisStepper';
import { Loader2 } from 'lucide-react';

function App() {
  // State
  const [view, setView] = useState('hero'); // 'hero', 'analysis', 'results'
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // Actions
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
      const msg = e.response?.data?.error || e.message || "Analysis failed. Please try again.";
      setError(msg);
      setLoading(false);
    }
  };

  const pollStatus = async (id) => {
    const interval = setInterval(async () => {
      try {
        const res = await getStatus(id);
        setStatus(res.status);

        if (res.status === 'Done') {
          clearInterval(interval);
          try {
            const completeResults = await getResults(id);
            setResults(completeResults);
            setLoading(false);
            setView('results');
          } catch (fetchErr) {
            console.error("Error fetching final results:", fetchErr);
            setError("Failed to download analysis results. The server may have restarted.");
            setLoading(false);
          }
        } else if (res.status.startsWith('Failed')) {
          clearInterval(interval);
          setLoading(false);
          setError(res.status);
        }
      } catch (err) {
        // Handle polling connection errors
        console.error("Polling error:", err);
        // Only stop polling if it's a persistent error
      }
    }, 2000);
  };


  const handleReset = () => {
    setView('hero');
    setResults(null);
    setJobId(null);
    setStatus(null);
  };

  const getStepData = () => {
    if (!status) return { step: 0, message: "Initializing..." };
    try {
      const parsed = JSON.parse(status);
      return { step: parsed.step, message: parsed.message };
    } catch {
      if (status === 'Done') return { step: 7, message: "Complete" };
      return { step: 1, message: status }; // Fallback for simple strings
    }
  };

  const { step, message } = getStepData();


  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-blue-500/30 overflow-x-hidden">

      {/* Background Noise/Grid (Optional Polish) */}
      <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none z-0"></div>

      <main className="relative z-10 w-full">
        {view === 'hero' && (
          <HeroSection onStart={handleStart} />
        )}

        {view === 'analysis' && (
          <div className="min-h-screen flex flex-col items-center pt-20 px-4">
            <h2 className="text-4xl font-bold mb-4">Upload Codebase</h2>
            <p className="text-slate-400 mb-10 text-center max-w-lg">
              We'll analyze your dependencies, generate a Code Property Graph, and identify microservice boundaries.
            </p>
            <UploadZone
              onUpload={handleAnalysis}
              onGitAnalyze={handleAnalysis}
              onBack={() => setView('hero')}
              loading={loading}
            />

            {loading && (
              <div className="mt-12 w-full max-w-2xl">
                <div className="flex flex-col items-center mb-10">
                  <div className="relative">
                    <div className="absolute inset-0 bg-blue-500 blur-xl opacity-20 rounded-full"></div>
                    <Loader2 className="w-12 h-12 text-blue-500 animate-spin relative z-10" />
                  </div>
                  <p className="mt-4 text-blue-400 font-mono text-sm">Deep Code Analysis in Progress</p>
                </div>

                <div className="glass-card rounded-2xl p-8 border border-white/5">
                  <AnalysisStepper currentStep={step} message={message} />
                </div>
              </div>
            )}

            {error && (
              <div className="mt-8 p-6 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl max-w-2xl w-full">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-red-500/20 rounded-full">
                    <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-bold text-red-100">Analysis Failed</h3>
                </div>
                <p className="font-mono text-sm bg-black/30 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap">
                  {error}
                </p>
                <button
                  onClick={() => setError(null)}
                  className="mt-4 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 text-sm font-medium rounded-lg transition-colors"
                >
                  Dismiss
                </button>
              </div>
            )}
          </div>
        )}

        {view === 'results' && results && (
          <ResultsDashboard results={results} jobId={jobId} onReset={handleReset} />
        )}
      </main>
    </div>
  );
}

export default App;
