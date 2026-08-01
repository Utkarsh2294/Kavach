import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Power, 
  Activity, 
  ScrollText, 
  ShieldCheck, 
  Sparkles, 
  ArrowRight,
  Shield,
  Server,
  Lock,
  ChevronRight
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// Feature Cards Data
const features = [
  {
    title: 'Delegation-Aware Kill Switch',
    description: 'Instantly revoke any agent — or an entire branch of delegated sub-agents — with a single action. Cascade control propagates through the full delegation tree.',
    icon: Power,
    iconColor: 'text-red-500',
    iconBg: 'bg-red-500/10'
  },
  {
    title: 'Real-Time Risk Scoring',
    description: 'Locally-trained ML models (Isolation Forest + XGBoost) score every transaction in real-time. No external LLM API calls — every decision is explainable and reproducible.',
    icon: Activity,
    iconColor: 'text-amber-500',
    iconBg: 'bg-amber-500/10'
  },
  {
    title: 'Tamper-Evident Audit Log',
    description: 'Every governance decision is recorded in a cryptographically chained audit trail. Detect tampering, prove compliance, and satisfy regulatory auditors with immutable records.',
    icon: ScrollText,
    iconColor: 'text-sky-500',
    iconBg: 'bg-sky-500/10'
  },
  {
    title: 'NIST RMF Alignment',
    description: 'Built-in compliance mapping to NIST AI Risk Management Framework. Automated evidence collection and gap analysis across Govern, Map, Measure, and Manage functions.',
    icon: ShieldCheck,
    iconColor: 'text-emerald-500',
    iconBg: 'bg-emerald-500/10'
  }
];

export default function LandingPage() {
  const [isVisible, setIsVisible] = useState({});

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible((prev) => ({ ...prev, [entry.target.id]: true }));
          }
        });
      },
      { threshold: 0.1 }
    );

    const elements = document.querySelectorAll('.animate-on-scroll');
    elements.forEach((el) => observer.observe(el));

    return () => elements.forEach((el) => observer.unobserve(el));
  }, []);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans overflow-hidden selection:bg-indigo-500/30">
      
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/20 blur-[120px]" />
        <div className="absolute top-[20%] right-[-10%] w-[40%] h-[40%] rounded-full bg-violet-600/20 blur-[120px]" />
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff0a_1px,transparent_1px),linear-gradient(to_bottom,#ffffff0a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
      </div>

      <div className="relative z-10">
        
        {/* Navigation */}
        <nav className="border-b border-zinc-800/50 bg-zinc-950/50 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-8 h-8 text-indigo-500" />
              <span className="text-xl font-bold tracking-tight">Kavach</span>
            </div>
            <div className="flex items-center gap-4">
              <Link to="/login" className="text-sm font-medium text-zinc-400 hover:text-zinc-100 transition-colors">
                Log in
              </Link>
              <Button asChild className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors shadow-sm">
                <Link to="/signup">Get Started</Link>
              </Button>
            </div>
          </div>
        </nav>

        <main>
          {/* Hero Section */}
          <section id="hero" className="relative pt-32 pb-20 sm:pt-40 sm:pb-24 lg:pb-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center flex flex-col items-center animate-on-scroll transition-all duration-1000 opacity-0 translate-y-8 data-[visible=true]:opacity-100 data-[visible=true]:translate-y-0" data-visible={isVisible['hero']}>
            
            <Badge variant="outline" className="mb-8 border-zinc-800 bg-zinc-900/50 text-zinc-300 py-1.5 px-4 rounded-full flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-violet-500" />
              <span>Built for Financial Services</span>
            </Badge>

            <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-zinc-100 via-zinc-200 to-zinc-500 max-w-4xl mb-8 leading-tight">
              Governance & Trust Layer for <br className="hidden sm:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-400">Autonomous Financial Agents</span>
            </h1>

            <p className="text-lg sm:text-xl text-zinc-400 max-w-2xl mb-10 leading-relaxed">
              Real-time oversight, delegation-aware kill switches, and tamper-evident audit trails — so your AI agents operate within the boundaries you set.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
              <Button asChild size="lg" className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg h-12 px-8 text-base shadow-[0_0_20px_-5px_rgba(99,102,241,0.5)] transition-all">
                <Link to="/signup">
                  Get Started <ArrowRight className="ml-2 w-4 h-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="border-zinc-700 hover:bg-zinc-800/50 text-zinc-100 rounded-lg h-12 px-8 text-base bg-zinc-900/50 backdrop-blur-sm transition-all">
                <Link to="/contact">
                  Request Demo
                </Link>
              </Button>
            </div>
          </section>

          {/* Social Proof Section */}
          <section id="trusted" className="py-12 border-y border-zinc-800/50 bg-zinc-900/20 backdrop-blur-sm animate-on-scroll transition-all duration-1000 delay-200 opacity-0 data-[visible=true]:opacity-100" data-visible={isVisible['trusted']}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
              <p className="text-sm font-medium text-zinc-500 uppercase tracking-widest mb-8">Trusted by forward-thinking financial institutions</p>
              <div className="flex flex-wrap justify-center items-center gap-8 sm:gap-16 opacity-50 grayscale">
                 <div className="flex items-center gap-2 text-xl font-bold font-serif"><Shield className="w-6 h-6"/> Citadel Trust</div>
                 <div className="flex items-center gap-2 text-xl font-bold"><Server className="w-6 h-6"/> Nexus Bank</div>
                 <div className="flex items-center gap-2 text-xl font-bold font-mono"><Lock className="w-6 h-6"/> QUANTUM.cap</div>
              </div>
            </div>
          </section>

          {/* Features Section */}
          <section id="features" className="py-24 sm:py-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
            <div className="text-center mb-16 sm:mb-24 animate-on-scroll transition-all duration-1000 opacity-0 translate-y-8 data-[visible=true]:opacity-100 data-[visible=true]:translate-y-0" id="features-header" data-visible={isVisible['features-header']}>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6">Built for Trust, Designed for Control</h2>
              <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
                Comprehensive governance infrastructure that bridges the gap between autonomous capabilities and regulatory requirements.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
              {features.map((feature, index) => {
                const Icon = feature.icon;
                const id = `feature-${index}`;
                return (
                  <Card 
                    key={index} 
                    id={id}
                    className="group bg-zinc-900/50 border-zinc-800 rounded-xl overflow-hidden hover:border-zinc-700 hover:shadow-lg hover:shadow-indigo-500/5 transition-all duration-300 hover:-translate-y-1 animate-on-scroll opacity-0 translate-y-8 data-[visible=true]:opacity-100 data-[visible=true]:translate-y-0 backdrop-blur-sm"
                    data-visible={isVisible[id]}
                    style={{ transitionDelay: `${index * 150}ms` }}
                  >
                    <CardHeader>
                      <div className={cn("w-12 h-12 rounded-lg flex items-center justify-center mb-4 transition-colors", feature.iconBg)}>
                        <Icon className={cn("w-6 h-6", feature.iconColor)} />
                      </div>
                      <CardTitle className="text-xl font-semibold text-zinc-100">{feature.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CardDescription className="text-zinc-400 text-base leading-relaxed">
                        {feature.description}
                      </CardDescription>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </section>

          {/* How It Works Section */}
          <section id="how-it-works" className="py-24 bg-zinc-900/30 border-y border-zinc-800/50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="text-center mb-16 animate-on-scroll transition-all duration-1000 opacity-0 translate-y-8 data-[visible=true]:opacity-100 data-[visible=true]:translate-y-0" id="how-it-works-header" data-visible={isVisible['how-it-works-header']}>
                <h2 className="text-3xl sm:text-4xl font-bold mb-6">Seamless Integration</h2>
                <p className="text-zinc-400 text-lg max-w-2xl mx-auto">Deploy governance alongside your existing agent frameworks with minimal friction.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {[
                  { step: '01', title: 'Connect Your Agents', desc: 'SDKs for LangChain, AutoGen, and custom Python/Node frameworks drop in with just three lines of code.' },
                  { step: '02', title: 'Set Policies', desc: 'Define risk thresholds, allowed actions, and delegation constraints using our declarative YAML syntax.' },
                  { step: '03', title: 'Monitor & Intervene', desc: 'Watch agent execution in real-time. Pausing or terminating rogue agents is always one click away.' }
                ].map((item, i) => (
                  <div 
                    key={i} 
                    id={`step-${i}`}
                    className="relative p-6 rounded-xl border border-zinc-800/50 bg-zinc-900/20 hover:bg-zinc-900/40 transition-colors animate-on-scroll opacity-0 translate-y-8 data-[visible=true]:opacity-100 data-[visible=true]:translate-y-0"
                    data-visible={isVisible[`step-${i}`]}
                    style={{ transitionDelay: `${i * 200}ms` }}
                  >
                    <div className="text-5xl font-mono font-bold text-zinc-800 mb-4">{item.step}</div>
                    <h3 className="text-xl font-semibold mb-3 text-zinc-200">{item.title}</h3>
                    <p className="text-zinc-400 leading-relaxed">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* CTA Section */}
          <section id="cta" className="py-24 sm:py-32 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto text-center animate-on-scroll transition-all duration-1000 opacity-0 scale-95 data-[visible=true]:opacity-100 data-[visible=true]:scale-100" data-visible={isVisible['cta']}>
            <div className="p-8 sm:p-12 rounded-3xl bg-gradient-to-b from-zinc-900 to-zinc-950 border border-zinc-800 shadow-2xl relative overflow-hidden">
              {/* Internal glow */}
              <div className="absolute inset-0 bg-indigo-500/5 mix-blend-overlay" />
              
              <div className="relative z-10">
                <h2 className="text-3xl sm:text-5xl font-bold mb-6 text-zinc-100">Ready to govern your AI fleet?</h2>
                <p className="text-xl text-zinc-400 mb-10 max-w-2xl mx-auto">
                  Start building safer, compliant, and controllable autonomous systems today.
                </p>
                <Button asChild size="lg" className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg h-14 px-10 text-lg shadow-lg shadow-indigo-600/20 transition-all hover:scale-105">
                  <Link to="/signup">
                    Get Started Free <ChevronRight className="ml-2 w-5 h-5" />
                  </Link>
                </Button>
              </div>
            </div>
          </section>
        </main>

        {/* Footer */}
        <footer className="border-t border-zinc-800/80 bg-zinc-950 py-12 px-4 sm:px-6 lg:px-8 mt-12">
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2 opacity-80 hover:opacity-100 transition-opacity">
              <Shield className="w-6 h-6 text-indigo-500" />
              <span className="text-lg font-bold">Kavach</span>
            </div>
            <p className="text-sm text-zinc-500">
              © {new Date().getFullYear()} Kavach Systems Inc. All rights reserved.
            </p>
            <div className="flex gap-6 text-sm text-zinc-500">
              <Link to="/privacy" className="hover:text-zinc-300 transition-colors">Privacy</Link>
              <Link to="/terms" className="hover:text-zinc-300 transition-colors">Terms</Link>
              <Link to="/docs" className="hover:text-zinc-300 transition-colors">Documentation</Link>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
