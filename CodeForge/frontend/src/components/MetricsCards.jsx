
import { motion } from 'framer-motion';
import { Activity, Code, Layers, Zap } from 'lucide-react';

const MetricCard = ({ icon: Icon, label, value, color, delay }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay }}
        className="glass p-4 rounded-xl flex items-center justify-between border-l-4"
        style={{ borderLeftColor: color }}
    >
        <div>
            <p className="text-slate-400 text-sm font-medium">{label}</p>
            <h4 className="text-2xl font-bold mt-1 text-white">{value}</h4>
        </div>
        <div className="p-3 bg-slate-800/50 rounded-lg">
            <Icon className="w-5 h-5" style={{ color }} />
        </div>
    </motion.div>
);

const MetricsCards = ({ stats }) => {
    // Default/Mock stats if empty
    const s = stats || { nodes: 0, loc: "0", edges: 0, confidence: "0%" };

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <MetricCard icon={Layers} label="Nodes Extracted" value={s.nodes} color="#3b82f6" delay={0.1} />
            <MetricCard icon={Code} label="Total LOC" value={s.loc} color="#eab308" delay={0.2} />
            <MetricCard icon={Zap} label="Relations (Edges)" value={s.edges} color="#10b981" delay={0.3} />
            <MetricCard icon={Activity} label="Confidence" value={s.confidence} color="#8b5cf6" delay={0.4} />
        </div>
    );
};

export default MetricsCards;
