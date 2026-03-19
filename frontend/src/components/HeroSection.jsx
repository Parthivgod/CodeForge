import { motion } from 'framer-motion';
import { ArrowRight, Shield, Eye, Network, Github, Cpu, GitBranch } from 'lucide-react';

const HeroSection = ({ onStart }) => {
    const features = [
        {
            icon: Network,
            title: 'Code Property Graph',
            description: 'Multi-language AST parsing with relationship discovery across functions, classes, and modules.',
            accent: 'blue',
            accentHex: '#3b82f6',
        },
        {
            icon: Shield,
            title: 'Security Risk Analysis',
            description: 'AI-powered deep risk assessment identifying vulnerabilities, injection points, and security hotspots.',
            accent: 'purple',
            accentHex: '#8b5cf6',
        },
        {
            icon: Eye,
            title: 'Interactive Visualization',
            description: 'Explore your codebase with Sigma.js powered graphs, hierarchical layouts, and smart filtering.',
            accent: 'emerald',
            accentHex: '#10b981',
        },
    ];

    const stats = [
        { value: '5+',         label: 'Languages',     color: '#3b82f6' },
        { value: '3-Model',    label: 'AI Pipeline',   color: '#8b5cf6' },
        { value: 'Real-time',  label: 'Analysis',      color: '#10b981' },
        { value: 'Interactive',label: 'Visualization', color: '#f97316' },
    ];

    return (
        <section
            className="relative min-h-screen flex flex-col items-center justify-center text-center px-6 pb-24 overflow-hidden"
            aria-label="Hero"
        >
            {/* Background layers */}
            <div className="absolute inset-0 bg-[#0a0f1e] z-[-3]" />
            <div className="absolute inset-0 bg-grid z-[-2] opacity-100" />
            <div
                className="absolute top-[-8%] left-[15%] w-[600px] h-[600px] rounded-full z-[-1]"
                style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.18) 0%, transparent 70%)' }}
                aria-hidden="true"
            />
            <div
                className="absolute bottom-[-5%] right-[10%] w-[500px] h-[500px] rounded-full z-[-1]"
                style={{ background: 'radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 70%)' }}
                aria-hidden="true"
            />

            {/* Badge */}
            <motion.div
                initial={{ opacity: 0, y: -16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="mb-8"
            >
                <span className="badge badge-blue">
                    <Cpu className="w-3.5 h-3.5" aria-hidden="true" />
                    AI-Powered Code Analysis &nbsp;·&nbsp; Multi-Language Support
                </span>
            </motion.div>

            {/* Heading */}
            <motion.h1
                initial={{ opacity: 0, scale: 0.94 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.7, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
                className="text-6xl md:text-7xl lg:text-8xl font-extrabold tracking-tight mb-6 leading-[1.05]"
            >
                <span className="gradient-text bg-gradient-to-br from-white via-slate-200 to-slate-400">
                    Code
                </span>
                <span style={{ color: '#3b82f6' }}>Forge</span>
            </motion.h1>

            {/* Subheading */}
            <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.7, delay: 0.25 }}
                className="text-xl md:text-2xl text-slate-300 max-w-2xl mb-3 leading-relaxed font-light"
            >
                Understand your codebase with AI-powered graph analysis and security risk assessment.
            </motion.p>

            <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.7, delay: 0.35 }}
                className="text-sm text-slate-500 max-w-xl mb-12 leading-relaxed"
            >
                Powered by{' '}
                <span className="text-blue-400 font-semibold">AWS Bedrock</span>
                {' '}·{' '}
                Multi-language support
                {' '}·{' '}
                Interactive visualization
            </motion.p>

            {/* CTAs */}
            <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.45 }}
                className="flex flex-col sm:flex-row gap-4 mb-20"
            >
                <button
                    onClick={onStart}
                    aria-label="Start analyzing your code"
                    className="group relative inline-flex items-center justify-center gap-2.5 px-8 py-4 rounded-xl font-bold text-lg text-white transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400 focus-visible:outline-offset-2"
                    style={{
                        background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                        boxShadow: '0 0 24px rgba(59,130,246,0.35), 0 4px 16px rgba(0,0,0,0.4)',
                    }}
                    onMouseEnter={e => e.currentTarget.style.boxShadow = '0 0 36px rgba(59,130,246,0.5), 0 4px 20px rgba(0,0,0,0.4)'}
                    onMouseLeave={e => e.currentTarget.style.boxShadow = '0 0 24px rgba(59,130,246,0.35), 0 4px 16px rgba(0,0,0,0.4)'}
                >
                    Analyze Code
                    <ArrowRight className="w-5 h-5 transition-transform duration-200 group-hover:translate-x-1" aria-hidden="true" />
                </button>

                <a
                    href="https://github.com/Parthivgod/CodeForge"
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label="View CodeForge on GitHub (opens in new tab)"
                    className="group inline-flex items-center justify-center gap-2.5 px-8 py-4 rounded-xl font-medium text-slate-200 border transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400 focus-visible:outline-offset-2"
                    style={{
                        background: 'rgba(30,41,59,0.6)',
                        borderColor: 'rgba(255,255,255,0.1)',
                        backdropFilter: 'blur(8px)',
                    }}
                    onMouseEnter={e => {
                        e.currentTarget.style.background = 'rgba(30,41,59,0.9)';
                        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.18)';
                    }}
                    onMouseLeave={e => {
                        e.currentTarget.style.background = 'rgba(30,41,59,0.6)';
                        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
                    }}
                >
                    <Github className="w-5 h-5" aria-hidden="true" />
                    View on GitHub
                </a>
            </motion.div>

            {/* Feature cards */}
            <motion.div
                initial={{ opacity: 0, y: 32 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.6 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-5xl w-full mb-20"
                role="list"
                aria-label="Key features"
            >
                {features.map((feat, i) => (
                    <article
                        key={i}
                        role="listitem"
                        className="group p-6 rounded-2xl cursor-default transition-all duration-250"
                        style={{
                            background: 'linear-gradient(145deg, rgba(30,41,59,0.7), rgba(15,23,42,0.6))',
                            border: '1px solid rgba(255,255,255,0.06)',
                            backdropFilter: 'blur(10px)',
                        }}
                        onMouseEnter={e => {
                            e.currentTarget.style.borderColor = feat.accentHex + '40';
                            e.currentTarget.style.transform = 'translateY(-3px)';
                            e.currentTarget.style.boxShadow = `0 12px 40px rgba(0,0,0,0.4), 0 0 20px ${feat.accentHex}18`;
                        }}
                        onMouseLeave={e => {
                            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)';
                            e.currentTarget.style.transform = 'translateY(0)';
                            e.currentTarget.style.boxShadow = 'none';
                        }}
                    >
                        <div
                            className="w-12 h-12 rounded-xl flex items-center justify-center mb-5 transition-colors duration-200"
                            style={{ background: feat.accentHex + '18' }}
                            aria-hidden="true"
                        >
                            <feat.icon className="w-6 h-6" style={{ color: feat.accentHex }} />
                        </div>
                        <h3 className="text-base font-bold mb-2 text-slate-100">{feat.title}</h3>
                        <p className="text-sm text-slate-400 leading-relaxed">{feat.description}</p>
                    </article>
                ))}
            </motion.div>

            {/* Stats row */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.7, delay: 0.85 }}
                className="flex flex-wrap justify-center gap-10 md:gap-16"
                aria-label="Product statistics"
            >
                {stats.map((s, i) => (
                    <div key={i} className="flex flex-col items-center gap-1">
                        <span
                            className="text-3xl font-extrabold tabular-nums"
                            style={{ color: s.color }}
                        >
                            {s.value}
                        </span>
                        <span className="text-xs text-slate-500 uppercase tracking-widest font-medium">
                            {s.label}
                        </span>
                    </div>
                ))}
            </motion.div>
        </section>
    );
};

export default HeroSection;
