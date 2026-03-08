
import { motion } from 'framer-motion';
import { ArrowRight, Shield, GitBranch, Zap, Eye, Brain, Network, Github } from 'lucide-react';

const HeroSection = ({ onStart }) => {
    return (
        <section className="relative min-h-screen flex flex-col items-center justify-center text-center p-8 overflow-hidden">
            {/* Background Gradients */}
            <div className="absolute top-0 left-0 w-full h-full bg-slate-950 z-[-2]" />
            <div className="absolute top-[-10%] left-[20%] w-[500px] h-[500px] bg-blue-500/20 rounded-full blur-[100px] z-[-1]" />
            <div className="absolute bottom-[-10%] right-[20%] w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[100px] z-[-1]" />

            {/* Badge */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="mb-6 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-sm font-medium backdrop-blur-sm"
            >
                AI-Powered Code Analysis • Multi-Language Support
            </motion.div>

            <motion.h1
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.8, delay: 0.1 }}
                className="text-6xl md:text-7xl font-extrabold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-100 to-slate-400"
            >
                Code<span className="text-blue-500">Forge</span>
            </motion.h1>

            <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8, delay: 0.3 }}
                className="text-xl text-slate-400 max-w-3xl mb-4 leading-relaxed"
            >
                Understand your codebase with AI-powered graph analysis and security risk assessment.
            </motion.p>

            <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8, delay: 0.4 }}
                className="text-base text-slate-500 max-w-2xl mb-10"
            >
                Powered by <span className="text-blue-400 font-semibold">AWS Bedrock</span> • Multi-language support • Interactive visualization
            </motion.p>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.5 }}
                className="flex gap-4 mb-16"
            >
                <button
                    onClick={onStart}
                    className="group relative px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-lg shadow-lg shadow-blue-500/30 transition-all hover:scale-105 flex items-center gap-2"
                >
                    Analyze Code
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>
                <a
                    href="https://github.com/Parthivgod/CodeForge"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group px-8 py-4 bg-slate-800/50 hover:bg-slate-800 text-white rounded-xl font-medium border border-white/5 transition-all hover:scale-105 backdrop-blur-sm flex items-center gap-2"
                >
                    <Github className="w-5 h-5" />
                    View on GitHub
                </a>
            </motion.div>

            {/* Features Grid */}
            <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.7 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full"
            >
                {/* Feature 1 */}
                <div className="group p-6 bg-slate-900/50 hover:bg-slate-900/80 border border-white/5 rounded-xl backdrop-blur-sm transition-all hover:scale-105 hover:border-blue-500/30">
                    <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-500/20 transition-colors">
                        <Network className="w-6 h-6 text-blue-400" />
                    </div>
                    <h3 className="text-lg font-bold mb-2 text-white">Code Property Graph</h3>
                    <p className="text-sm text-slate-400">
                        Multi-language AST parsing with relationship discovery across functions, classes, and modules.
                    </p>
                </div>

                {/* Feature 2 */}
                <div className="group p-6 bg-slate-900/50 hover:bg-slate-900/80 border border-white/5 rounded-xl backdrop-blur-sm transition-all hover:scale-105 hover:border-purple-500/30">
                    <div className="w-12 h-12 bg-purple-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-purple-500/20 transition-colors">
                        <Shield className="w-6 h-6 text-purple-400" />
                    </div>
                    <h3 className="text-lg font-bold mb-2 text-white">Security Risk Analysis</h3>
                    <p className="text-sm text-slate-400">
                        AI-powered deep risk assessment identifying vulnerabilities, injection points, and security hotspots.
                    </p>
                </div>

                {/* Feature 3 */}
                <div className="group p-6 bg-slate-900/50 hover:bg-slate-900/80 border border-white/5 rounded-xl backdrop-blur-sm transition-all hover:scale-105 hover:border-green-500/30">
                    <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-green-500/20 transition-colors">
                        <Eye className="w-6 h-6 text-green-400" />
                    </div>
                    <h3 className="text-lg font-bold mb-2 text-white">Interactive Visualization</h3>
                    <p className="text-sm text-slate-400">
                        Explore your codebase with Sigma.js powered graphs, hierarchical layouts, and smart filtering.
                    </p>
                </div>
            </motion.div>

            {/* Stats Bar */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8, delay: 0.9 }}
                className="mt-16 flex flex-wrap justify-center gap-8 text-center"
            >
                <div className="flex flex-col">
                    <div className="text-3xl font-bold text-blue-400">5+</div>
                    <div className="text-sm text-slate-500">Languages Supported</div>
                </div>
                <div className="flex flex-col">
                    <div className="text-3xl font-bold text-purple-400">3-Model</div>
                    <div className="text-sm text-slate-500">AI Pipeline</div>
                </div>
                <div className="flex flex-col">
                    <div className="text-3xl font-bold text-green-400">Real-time</div>
                    <div className="text-sm text-slate-500">Analysis</div>
                </div>
                <div className="flex flex-col">
                    <div className="text-3xl font-bold text-orange-400">Interactive</div>
                    <div className="text-sm text-slate-500">Visualization</div>
                </div>
            </motion.div>
        </section>
    );
};

export default HeroSection;
