
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

const steps = [
    { title: 'Code Parsing', description: 'Building CPG' },
    { title: 'AI Discovery', description: 'LLM Analysis' },
    { title: 'GNN Learning', description: 'Structural Embeddings' },
    { title: 'Service Clustering', description: 'Louvain Algorithm' },
    { title: 'Graph Metrics', description: 'Analyzing Topology' },
    { title: 'Report Generation', description: 'Finalizing Blueprint' }
];

const AnalysisStepper = ({ currentStep, message }) => {
    return (
        <div className="w-full max-w-xl mx-auto space-y-4">
            <div className="relative">
                {/* Connector Line */}
                <div className="absolute left-[19px] top-2 bottom-2 w-0.5 bg-slate-800" />

                <div className="space-y-6">
                    {steps.map((step, idx) => {
                        const isCompleted = currentStep > idx + 1;
                        const isCurrent = currentStep === idx + 1;
                        const isPending = currentStep < idx + 1;

                        return (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.1 }}
                                className="flex items-start gap-4 relative z-10"
                            >
                                <div className={clsx(
                                    "mt-1 flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-500",
                                    isCompleted ? "bg-emerald-500/20 text-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.2)]" :
                                        isCurrent ? "bg-blue-600 text-white shadow-[0_0_20px_rgba(37,99,235,0.4)]" :
                                            "bg-slate-900 border border-slate-800 text-slate-600"
                                )}>
                                    {isCompleted ? <CheckCircle2 className="w-6 h-6" /> :
                                        isCurrent ? <Loader2 className="w-6 h-6 animate-spin" /> :
                                            <Circle className="w-6 h-6" />}
                                </div>

                                <div className="flex-1 pt-1">
                                    <div className="flex items-center justify-between">
                                        <h4 className={clsx(
                                            "text-sm font-bold tracking-tight transition-colors",
                                            isPending ? "text-slate-500" : "text-slate-100"
                                        )}>
                                            {step.title}
                                        </h4>
                                        {isCurrent && (
                                            <span className="text-[10px] font-mono bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/20 animate-pulse">
                                                ACTIVE
                                            </span>
                                        )}
                                    </div>
                                    <p className={clsx(
                                        "text-xs mt-0.5 transition-colors",
                                        isCurrent ? "text-blue-400" : "text-slate-500"
                                    )}>
                                        {isCurrent ? message : step.description}
                                    </p>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default AnalysisStepper;
