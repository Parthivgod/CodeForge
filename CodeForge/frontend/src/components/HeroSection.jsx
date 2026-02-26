
import { motion } from 'framer-motion';
import { ArrowRight, Box } from 'lucide-react';

const HeroSection = ({ onStart }) => {
    return (
        <section className="relative min-h-screen flex flex-col items-center justify-center text-center p-8 overflow-hidden">
            {/* Background Gradients */}
            <div className="absolute top-0 left-0 w-full h-full bg-slate-950 z-[-2]" />
            <div className="absolute top-[-10%] left-[20%] w-[500px] h-[500px] bg-blue-500/20 rounded-full blur-[100px] z-[-1]" />
            <div className="absolute bottom-[-10%] right-[20%] w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[100px] z-[-1]" />


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
                className="text-xl text-slate-400 max-w-2xl mb-10 leading-relaxed"
            >
                Transform legacy code into microservices in minutes.
                Powered by <span className="text-white font-semibold">Azure OpenAI</span> + <span className="text-white font-semibold">Deep Learning</span>.
            </motion.p>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.5 }}
                className="flex gap-4"
            >
                <button
                    onClick={onStart}
                    className="group relative px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-lg shadow-lg shadow-blue-500/30 transition-all hover:scale-105 flex items-center gap-2"
                >
                    Start Decomposing
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>
                <button className="px-8 py-4 bg-slate-800/50 hover:bg-slate-800 text-white rounded-xl font-medium border border-white/5 transition-all hover:scale-105 backdrop-blur-sm">
                    How it works
                </button>
            </motion.div>
        </section>
    );
};

export default HeroSection;
