import { Github, Twitter, Mail, Heart } from 'lucide-react';

const Footer = () => {
    return (
        <footer className="relative bg-slate-950 border-t border-white/5 py-12 px-8">
            <div className="max-w-6xl mx-auto">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
                    {/* Brand */}
                    <div className="col-span-1 md:col-span-2">
                        <h3 className="text-2xl font-bold mb-3 bg-clip-text text-transparent bg-gradient-to-r from-white to-blue-400">
                            CodeForge
                        </h3>
                        <p className="text-slate-400 text-sm mb-4 max-w-md">
                            AI-powered code analysis tool that helps you understand your codebase through graph visualization and security risk assessment.
                        </p>
                        <div className="flex gap-3">
                            <a
                                href="https://github.com/yourusername/codeforge"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 bg-slate-800/50 hover:bg-slate-800 rounded-lg transition-colors"
                            >
                                <Github className="w-5 h-5 text-slate-400 hover:text-white" />
                            </a>
                            <a
                                href="https://twitter.com/yourusername"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 bg-slate-800/50 hover:bg-slate-800 rounded-lg transition-colors"
                            >
                                <Twitter className="w-5 h-5 text-slate-400 hover:text-white" />
                            </a>
                            <a
                                href="mailto:contact@codeforge.dev"
                                className="p-2 bg-slate-800/50 hover:bg-slate-800 rounded-lg transition-colors"
                            >
                                <Mail className="w-5 h-5 text-slate-400 hover:text-white" />
                            </a>
                        </div>
                    </div>

                    {/* Product */}
                    <div>
                        <h4 className="text-white font-semibold mb-3">Product</h4>
                        <ul className="space-y-2 text-sm text-slate-400">
                            <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                            <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                            <li><a href="#docs" className="hover:text-white transition-colors">Documentation</a></li>
                            <li><a href="#api" className="hover:text-white transition-colors">API Reference</a></li>
                        </ul>
                    </div>

                    {/* Resources */}
                    <div>
                        <h4 className="text-white font-semibold mb-3">Resources</h4>
                        <ul className="space-y-2 text-sm text-slate-400">
                            <li><a href="#blog" className="hover:text-white transition-colors">Blog</a></li>
                            <li><a href="#guides" className="hover:text-white transition-colors">Guides</a></li>
                            <li><a href="#examples" className="hover:text-white transition-colors">Examples</a></li>
                            <li><a href="#support" className="hover:text-white transition-colors">Support</a></li>
                        </ul>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="text-sm text-slate-500">
                        © 2026 CodeForge. Built with <Heart className="w-4 h-4 inline text-red-500" /> for developers.
                    </div>
                    <div className="flex gap-6 text-sm text-slate-500">
                        <a href="#privacy" className="hover:text-white transition-colors">Privacy Policy</a>
                        <a href="#terms" className="hover:text-white transition-colors">Terms of Service</a>
                        <a href="#license" className="hover:text-white transition-colors">License</a>
                    </div>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
