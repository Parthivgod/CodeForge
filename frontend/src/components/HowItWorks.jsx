import { motion } from 'framer-motion';
import { Code, GitBranch, Brain, Shield, BarChart3, Eye, Cpu, TreePine, TrendingUp, Zap } from 'lucide-react';

const HowItWorks = () => {
    const steps = [
        {
            icon: Code,
            title: 'Multi-Language Parsing',
            description: 'AST parsing for Python, JavaScript, TypeScript, Java, and Go using Tree-sitter.',
            accentHex: '#3b82f6',
        },
        {
            icon: GitBranch,
            title: 'Graph Construction',
            description: 'Build a Code Property Graph mapping functions, classes, and their relationships.',
            accentHex: '#8b5cf6',
        },
        {
            icon: Brain,
            title: 'AI Analysis — 3 Models',
            description: 'Mapper classifies nodes, Linker extracts relationships, Sentinel performs deep risk analysis.',
            accentHex: '#6366f1',
        },
        {
            icon: Shield,
            title: 'Security Assessment',
            description: 'Identify vulnerabilities, injection points, and security hotspots with AI reasoning.',
            accentHex: '#ef4444',
        },
        {
            icon: BarChart3,
            title: 'Feature Engineering',
            description: 'Generate 128-dimensional embeddings combining structural and semantic features.',
            accentHex: '#10b981',
        },
        {
            icon: Eye,
            title: 'Interactive Visualization',
            description: 'Explore your codebase with Sigma.js powered graphs and smart filtering.',
            accentHex: '#f97316',
        },
    ];

    const techStack = [
        { icon: Cpu,       name: 'AWS Bedrock',  sub: 'Multi-Model AI' },
        { icon: TreePine,  name: 'Tree-sitter',  sub: 'AST Parsing' },
        { icon: TrendingUp,name: 'Sigma.js',     sub: 'Graph Rendering' },
        { icon: Zap,       name: 'FastAPI',      sub: 'Backend API' },
    ];

    return (
        <section
            className="relative py-24 px-6 overflow-hidden"
            aria-labelledby="how-it-works-heading"
            style={{ background: 'linear-gradient(180deg, #0a0f1e 0%, #0f172a 100%)' }}
        >
            {/* Subtle top divider glow */}
            <div
                className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-px"
                style={{ background: 'linear-gradient(90deg, transparent, rgba(59,130,246,0.3), transparent)' }}
                aria-hidden="true"
            />

            <div className="max-w-6xl mx-auto">
                {/* Section header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-16"
                >
                    <span className="badge badge-blue mb-4">Pipeline Overview</span>
                    <h2
                        id="how-it-works-heading"
                        className="text-4xl md:text-5xl font-extrabold mb-4 gradient-text bg-gradient-to-br from-white to-slate-400"
                    >
                        How It Works
                    </h2>
                    <p className="text-slate-400 text-lg max-w-xl mx-auto leading-relaxed">
                        A 6-step AI-powered pipeline that transforms your code into actionable insights.
                    </p>
                </motion.div>

                {/* Steps grid */}
                <div
                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
                    role="list"
                    aria-label="Pipeline steps"
                >
                    {steps.map((step, i) => (
                        <motion.article
                            key={i}
                            role="listitem"
                            initial={{ opacity: 0, y: 32 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.55, delay: i * 0.08 }}
                            className="relative p-6 rounded-2xl"
                            style={{
                                background: 'linear-gradient(145deg, rgba(30,41,59,0.7), rgba(15,23,42,0.55))',
                                border: '1px solid rgba(255,255,255,0.06)',
                                backdropFilter: 'blur(10px)',
                            }}
                        >
                            {/* Step number badge */}
                            <div
                                className="absolute -top-3 -left-3 w-7 h-7 rounded-full flex items-center justify-center text-white font-bold text-xs shadow-lg"
                                style={{ background: step.accentHex }}
                                aria-label={`Step ${i + 1}`}
                            >
                                {i + 1}
                            </div>

                            {/* Icon */}
                            <div
                                className="w-12 h-12 rounded-xl flex items-center justify-center mb-5"
                                style={{
                                    background: step.accentHex + '18',
                                    border: `1px solid ${step.accentHex}30`,
                                }}
                                aria-hidden="true"
                            >
                                <step.icon className="w-6 h-6" style={{ color: step.accentHex }} />
                            </div>

                            <h3 className="text-base font-bold mb-2 text-slate-100">{step.title}</h3>
                            <p className="text-sm text-slate-400 leading-relaxed">{step.description}</p>
                        </motion.article>
                    ))}
                </div>

                {/* Tech stack */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: 0.5 }}
                    className="mt-16 p-8 rounded-2xl"
                    style={{
                        background: 'linear-gradient(145deg, rgba(30,41,59,0.6), rgba(15,23,42,0.5))',
                        border: '1px solid rgba(255,255,255,0.06)',
                        backdropFilter: 'blur(10px)',
                    }}
                    aria-labelledby="powered-by-heading"
                >
                    <h3
                        id="powered-by-heading"
                        className="text-xl font-bold mb-8 text-center text-slate-100"
                    >
                        Powered By
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                        {techStack.map((tech, i) => (
                            <div key={i} className="flex flex-col items-center gap-3">
                                <div
                                    className="w-12 h-12 rounded-xl flex items-center justify-center"
                                    style={{
                                        background: 'rgba(59,130,246,0.12)',
                                        border: '1px solid rgba(59,130,246,0.2)',
                                    }}
                                    aria-hidden="true"
                                >
                                    <tech.icon className="w-6 h-6 text-blue-400" />
                                </div>
                                <div>
                                    <div className="text-sm font-semibold text-slate-100">{tech.name}</div>
                                    <div className="text-xs text-slate-500 mt-0.5">{tech.sub}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </motion.div>
            </div>
        </section>
    );
};

export default HowItWorks;
