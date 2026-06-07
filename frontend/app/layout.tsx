import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import { LayoutDashboard, Network, Brain, FileText, Inbox, Star, TrendingUp, Cpu } from "lucide-react";
import EntitySearch from "@/components/EntitySearch";
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
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex h-screen bg-slate-950 text-white">
          <aside className="w-60 bg-slate-900 border-r border-slate-800 flex flex-col">
            <div className="p-6 border-b border-slate-800">
              <h1 className="text-base font-bold text-white leading-tight">
                AI Transmission Map
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                AI Infrastructure · Bottleneck Intelligence
              </p>
            </div>
            <nav className="flex-1 p-4 space-y-1">
              {navItems.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-indigo-600/20 transition-colors group"
                >
                  <Icon className="w-4 h-4 text-slate-400 group-hover:text-indigo-400" />
                  {label}
                </Link>
              ))}
              <div className="pt-3">
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
      </body>
    </html>
  );
}
