import { motion } from 'framer-motion';
import { Activity, Code, Layers, Zap, GitFork } from 'lucide-react';

const METRICS = [
    { icon: Layers,   label: 'Nodes Extracted',  key: 'nodes',      accentHex: '#3b82f6' },
    { icon: Code,     label: 'Total LOC',         key: 'loc',        accentHex: '#eab308' },
    { icon: Zap,      label: 'Relations',         key: 'edges',      accentHex: '#10b981' },
    { icon: Activity, label: 'Confidence',        key: 'confidence', accentHex: '#8b5cf6' },
    { icon: GitFork,  label: 'Microservices',     key: 'services',   accentHex: '#f97316' },
];

const MetricCard = ({ icon: Icon, label, value, accentHex, delay }) => (
    <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay }}
        className="flex items-center gap-3 py-3 px-4 rounded-xl"
        style={{
            background: 'rgba(15,23,42,0.6)',
            border: `1px solid ${accentHex}22`,
        }}
        role="group"
        aria-label={`${label}: ${value ?? 'N/A'}`}
    >
        <div
            className="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: accentHex + '18' }}
            aria-hidden="true"
        >
            <Icon className="w-4 h-4" style={{ color: accentHex }} />
        </div>
        <div className="min-w-0">
            <p className="text-xs text-slate-500 leading-none mb-1 truncate">{label}</p>
            <p
                className="text-lg font-bold tabular-nums leading-none"
                style={{ color: accentHex }}
            >
                {value ?? 'N/A'}
            </p>
        </div>
    </motion.div>
);

const MetricsCards = ({ stats }) => {
    const s = stats || { nodes: 0, loc: '0', edges: 0, confidence: '0%', services: undefined };

    return (
        <div
            className="grid grid-cols-2 md:grid-cols-5 gap-3"
            role="region"
            aria-label="Analysis metrics"
        >
            {METRICS.map((m, i) => (
                <MetricCard
                    key={m.key}
                    icon={m.icon}
                    label={m.label}
                    value={s[m.key]}
                    accentHex={m.accentHex}
                    delay={i * 0.07}
                />
            ))}
        </div>
    );
};

export default MetricsCards;
