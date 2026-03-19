import { Github, Twitter, Mail, Heart, Code2 } from 'lucide-react';

const Footer = () => {
    const socials = [
        {
            href: 'https://github.com/Parthivgod/CodeForge',
            label: 'CodeForge on GitHub',
            icon: Github,
        },
        {
            href: 'https://twitter.com/yourusername',
            label: 'Follow on Twitter',
            icon: Twitter,
        },
        {
            href: 'mailto:contact@codeforge.dev',
            label: 'Send email',
            icon: Mail,
        },
    ];

    const links = {
        Product: ['Features', 'Pricing', 'Documentation', 'API Reference'],
        Resources: ['Blog', 'Guides', 'Examples', 'Support'],
    };

    return (
        <footer
            className="relative border-t py-14 px-6"
            style={{
                background: 'linear-gradient(180deg, #0f172a 0%, #0a0f1e 100%)',
                borderTopColor: 'rgba(255,255,255,0.06)',
            }}
            aria-label="Site footer"
        >
            {/* Top glow line */}
            <div
                className="absolute top-0 left-1/2 -translate-x-1/2 w-[400px] h-px"
                style={{ background: 'linear-gradient(90deg, transparent, rgba(59,130,246,0.25), transparent)' }}
                aria-hidden="true"
            />

            <div className="max-w-6xl mx-auto">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-10">
                    {/* Brand */}
                    <div className="col-span-1 md:col-span-2">
                        <div className="flex items-center gap-2.5 mb-4">
                            <div
                                className="w-8 h-8 rounded-lg flex items-center justify-center"
                                style={{ background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)' }}
                                aria-hidden="true"
                            >
                                <Code2 className="w-4 h-4 text-white" />
                            </div>
                            <h3 className="text-xl font-bold gradient-text bg-gradient-to-r from-white to-blue-400">
                                CodeForge
                            </h3>
                        </div>
                        <p className="text-slate-400 text-sm mb-6 max-w-sm leading-relaxed">
                            AI-powered code analysis that helps you understand your codebase through graph visualization and security risk assessment.
                        </p>
                        <nav aria-label="Social links" className="flex gap-2">
                            {socials.map(({ href, label, icon: Icon }) => (
                                <a
                                    key={label}
                                    href={href}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    aria-label={label}
                                    className="p-2.5 rounded-xl transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400 focus-visible:outline-offset-2"
                                    style={{ background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(255,255,255,0.07)' }}
                                    onMouseEnter={e => {
                                        e.currentTarget.style.background = 'rgba(30,41,59,0.95)';
                                        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.14)';
                                    }}
                                    onMouseLeave={e => {
                                        e.currentTarget.style.background = 'rgba(30,41,59,0.6)';
                                        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.07)';
                                    }}
                                >
                                    <Icon className="w-4 h-4 text-slate-400" aria-hidden="true" />
                                </a>
                            ))}
                        </nav>
                    </div>

                    {/* Link columns */}
                    {Object.entries(links).map(([section, items]) => (
                        <div key={section}>
                            <h4 className="text-slate-100 font-semibold text-sm mb-4 uppercase tracking-wider">
                                {section}
                            </h4>
                            <nav aria-label={`${section} links`}>
                                <ul className="space-y-2.5">
                                    {items.map(item => (
                                        <li key={item}>
                                            <a
                                                href={`#${item.toLowerCase().replace(' ', '-')}`}
                                                className="text-sm text-slate-400 hover:text-slate-100 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400 focus-visible:outline-offset-1 rounded"
                                            >
                                                {item}
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            </nav>
                        </div>
                    ))}
                </div>

                {/* Bottom bar */}
                <div
                    className="pt-8 flex flex-col md:flex-row justify-between items-center gap-4"
                    style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
                >
                    <p className="text-xs text-slate-500 flex items-center gap-1.5">
                        © 2026 CodeForge. Built with
                        <Heart className="w-3.5 h-3.5 text-red-500 inline-block" aria-label="love" />
                        for developers.
                    </p>
                    <nav aria-label="Legal links" className="flex gap-5">
                        {['Privacy Policy', 'Terms of Service', 'License'].map(item => (
                            <a
                                key={item}
                                href={`#${item.toLowerCase().replace(' ', '-')}`}
                                className="text-xs text-slate-500 hover:text-slate-300 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400 rounded"
                            >
                                {item}
                            </a>
                        ))}
                    </nav>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
