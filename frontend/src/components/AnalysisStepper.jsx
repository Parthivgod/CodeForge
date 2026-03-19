import { CheckCircle2, Circle, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

const steps = [
    { title: 'Code Parsing',      description: 'Building Code Property Graph' },
    { title: 'Risk Profiling',    description: 'Building Risk AST Profiles' },
    { title: 'AI Analysis',       description: 'Mapper, Linker & Sentinel' },
    { title: 'Edge Validation',   description: 'Validating Relationships' },
    { title: 'Embeddings',        description: 'Generating Node Embeddings' },
    { title: 'Graph Analysis',    description: 'Computing Statistics' },
    { title: 'Report Generation', description: 'Finalizing Results' },
];

const AnalysisStepper = ({ currentStep, message }) => {
    return (
        <div className="w-full max-w-xl mx-auto" role="list" aria-label="Analysis progress">
            <div className="relative">
                {/* Connector line */}
                <div
                    className="absolute left-5 top-5 bottom-5 w-px"
                    style={{ background: 'linear-gradient(180deg, rgba(59,130,246,0.3), rgba(30,41,59,0.4))' }}
                    aria-hidden="true"
                />

                <div className="space-y-5">
                    {steps.map((step, idx) => {
                        const isCompleted = currentStep > idx + 1;
                        const isCurrent   = currentStep === idx + 1;
                        const isPending   = currentStep < idx + 1;

                        return (
                            <motion.div
                                key={idx}
                                role="listitem"
                                aria-label={`${step.title}: ${isCompleted ? 'completed' : isCurrent ? 'in progress' : 'pending'}`}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.07 }}
                                className="flex items-start gap-4 relative z-10"
                            >
                                {/* Step icon */}
                                <div
                                    className={clsx(
                                        'mt-0.5 flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-400',
                                        isCompleted && 'shadow-[0_0_14px_rgba(16,185,129,0.25)]',
                                        isCurrent   && 'shadow-[0_0_20px_rgba(59,130,246,0.4)]',
                                    )}
                                    style={{
                                        background: isCompleted
                                            ? 'rgba(16,185,129,0.15)'
                                            : isCurrent
                                                ? 'linear-gradient(135deg, #3b82f6, #1d4ed8)'
                                                : 'rgba(30,41,59,0.8)',
                                        border: isCompleted
                                            ? '1px solid rgba(16,185,129,0.3)'
                                            : isCurrent
                                                ? 'none'
                                                : '1px solid rgba(71,85,105,0.5)',
                                    }}
                                    aria-hidden="true"
                                >
                                    {isCompleted
                                        ? <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                                        : isCurrent
                                            ? <Loader2 className="w-5 h-5 text-white animate-spin" />
                                            : <Circle className="w-5 h-5 text-slate-600" />
                                    }
                                </div>

                                {/* Step content */}
                                <div className="flex-1 pt-1.5 min-w-0">
                                    <div className="flex items-center justify-between gap-2">
                                        <h4 className={clsx(
                                            'text-sm font-semibold transition-colors truncate',
                                            isPending   ? 'text-slate-600' : 'text-slate-100',
                                        )}>
                                            {step.title}
                                        </h4>
                                        {isCurrent && (
                                            <span
                                                className="flex-shrink-0 text-[10px] font-bold font-mono px-2 py-0.5 rounded-full animate-pulse"
                                                style={{
                                                    background: 'rgba(59,130,246,0.12)',
                                                    color: '#93c5fd',
                                                    border: '1px solid rgba(59,130,246,0.25)',
                                                }}
                                                aria-label="Currently active"
                                            >
                                                ACTIVE
                                            </span>
                                        )}
                                        {isCompleted && (
                                            <span
                                                className="flex-shrink-0 text-[10px] font-bold font-mono px-2 py-0.5 rounded-full"
                                                style={{
                                                    background: 'rgba(16,185,129,0.1)',
                                                    color: '#6ee7b7',
                                                    border: '1px solid rgba(16,185,129,0.2)',
                                                }}
                                                aria-label="Completed"
                                            >
                                                DONE
                                            </span>
                                        )}
                                    </div>
                                    <p className={clsx(
                                        'text-xs mt-0.5 leading-relaxed transition-colors',
                                        isCurrent   ? 'text-blue-400'  : 'text-slate-600',
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
