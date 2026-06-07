import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import { LayoutDashboard, Network, Brain, FileText, Inbox, Star, TrendingUp, Cpu, Bookmark, Mail } from "lucide-react";
import EntitySearch from "@/components/EntitySearch";
import { SWRProvider } from "@/lib/swr-config";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Transmission Map",
  description: "AI Infrastructure · Bottleneck Intelligence",
};

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/graph", label: "Graph", icon: Network },
  { href: "/thesis", label: "Thesis", icon: Brain },
  { href: "/memo", label: "Memo", icon: FileText },
  { href: "/evidence", label: "Evidence", icon: Inbox },
  { href: "/house-view", label: "House View", icon: Star },
  { href: "/regime", label: "Regime", icon: TrendingUp },
  { href: "/models", label: "Models", icon: Cpu },
  { href: "/watchlist", label: "Watchlist", icon: Bookmark },
  { href: "/digest", label: "Digest", icon: Mail },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className} suppressHydrationWarning={true}>
        <SWRProvider>
        <div className="flex h-screen bg-slate-950 text-white overflow-hidden">
          <aside className="w-14 md:w-60 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 transition-all">
            <div className="p-3 md:p-6 border-b border-slate-800">
              <h1 className="hidden md:block text-base font-bold text-white leading-tight">
                AI Transmission Map
              </h1>
              <p className="hidden md:block text-xs text-slate-400 mt-1">
                AI Infrastructure · Bottleneck Intelligence
              </p>
              <div className="md:hidden flex justify-center">
                <span className="text-indigo-400 text-lg font-bold">AI</span>
              </div>
            </div>
            <nav className="flex-1 p-2 md:p-4 space-y-1">
              {navItems.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-3 px-2 md:px-3 py-2.5 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-indigo-600/20 transition-colors group"
                  title={label}
                >
                  <Icon className="w-4 h-4 shrink-0 text-slate-400 group-hover:text-indigo-400" />
                  <span className="hidden md:block">{label}</span>
                </Link>
              ))}
              <div className="hidden md:block pt-3">
                <EntitySearch />
              </div>
            </nav>
            <div className="p-4 border-t border-slate-800">
              <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-emerald-900/40 border border-emerald-700/40 text-xs text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                AI_CAPEX_EXPANSION
              </span>
            </div>
          </aside>

          <div className="flex-1 flex flex-col overflow-hidden">
            <header className="h-14 border-b border-slate-800 bg-slate-900/50 flex items-center px-6">
              <span className="text-sm text-slate-400">US AI Infrastructure · Equity Investor View</span>
            </header>
            <main className="flex-1 overflow-auto p-6">
              {children}
            </main>
          </div>
        </div>
        </SWRProvider>
      </body>
    </html>
  );
}
