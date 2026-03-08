import { motion } from 'framer-motion';
import { Code, GitBranch, Brain, Shield, BarChart3, Eye } from 'lucide-react';

const HowItWorks = () => {
    const steps = [
        {
            icon: Code,
            title: "Multi-Language Parsing",
            description: "AST parsing for Python, JavaScript, TypeScript, Java, and Go using Tree-sitter.",
            color: "blue",
        },
        {
            icon: GitBranch,
            title: "Graph Construction",
            description: "Build a Code Property Graph mapping functions, classes, and their relationships.",
            color: "purple",
        },
        {
            icon: Brain,
            title: "AI Analysis (3 Models)",
            description: "Mapper classifies nodes, Linker extracts relationships, Sentinel performs deep risk analysis.",
            color: "indigo",
        },
        {
            icon: Shield,
            title: "Security Assessment",
            description: "Identify vulnerabilities, injection points, and security hotspots with AI reasoning.",
            color: "red",
        },
        {
            icon: BarChart3,
            title: "Feature Engineering",
            description: "Generate 128-dimensional embeddings combining structural and semantic features.",
            color: "green",
        },
        {
            icon: Eye,
            title: "Interactive Visualization",
            description: "Explore your codebase with Sigma.js powered graphs and smart filtering.",
            color: "orange",
        },
    ];

    const colorMap = {
        blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
        purple: "bg-purple-500/10 text-purple-400 border-purple-500/20",
        indigo: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
        red: "bg-red-500/10 text-red-400 border-red-500/20",
        green: "bg-green-500/10 text-green-400 border-green-500/20",
        orange: "bg-orange-500/10 text-orange-400 border-orange-500/20",
    };

    return (
        <section className="relative py-20 px-8 bg-slate-950">
            <div className="max-w-6xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-16"
                >
                    <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                        How It Works
                    </h2>
                    <p className="text-slate-400 text-lg max-w-2xl mx-auto">
                        A 6-step AI-powered pipeline that transforms your code into actionable insights
                    </p>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {steps.map((step, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 40 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.6, delay: index * 0.1 }}
                            className="group relative p-6 bg-slate-900/50 border border-white/5 rounded-xl backdrop-blur-sm hover:bg-slate-900/80 transition-all hover:scale-105"
                        >
                            {/* Step Number */}
                            <div className="absolute -top-3 -left-3 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg">
                                {index + 1}
                            </div>

                            {/* Icon */}
                            <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 border ${colorMap[step.color]}`}>
                                <step.icon className="w-6 h-6" />
                            </div>

                            {/* Content */}
                            <h3 className="text-lg font-bold mb-2 text-white">{step.title}</h3>
                            <p className="text-sm text-slate-400">{step.description}</p>
                        </motion.div>
                    ))}
                </div>

                {/* Tech Stack */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: 0.8 }}
                    className="mt-16 p-8 bg-slate-900/50 border border-white/5 rounded-xl backdrop-blur-sm"
                >
                    <h3 className="text-2xl font-bold mb-6 text-center text-white">Powered By</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                        <div>
                            <div className="text-3xl mb-2">🤖</div>
                            <div className="text-sm font-medium text-white">AWS Bedrock</div>
                            <div className="text-xs text-slate-500">Multi-Model AI</div>
                        </div>
                        <div>
                            <div className="text-3xl mb-2">🌳</div>
                            <div className="text-sm font-medium text-white">Tree-sitter</div>
                            <div className="text-xs text-slate-500">AST Parsing</div>
                        </div>
                        <div>
                            <div className="text-3xl mb-2">📊</div>
                            <div className="text-sm font-medium text-white">Sigma.js</div>
                            <div className="text-xs text-slate-500">Graph Rendering</div>
                        </div>
                        <div>
                            <div className="text-3xl mb-2">⚡</div>
                            <div className="text-sm font-medium text-white">FastAPI</div>
                            <div className="text-xs text-slate-500">Backend API</div>
                        </div>
                    </div>
                </motion.div>
            </div>
        </section>
    );
};

export default HowItWorks;
