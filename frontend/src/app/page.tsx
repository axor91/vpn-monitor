"use client";

import { useEffect, useState, useCallback } from "react";
import { Shield, Globe, Wrench } from "lucide-react";
import { api } from "@/lib/api";
import type { SummaryData } from "@/lib/api";
import { cn } from "@/lib/utils";
import { StatusBar } from "@/components/StatusBar";
import { SourceCard } from "@/components/SourceCard";
import { ManualCheck } from "@/components/ManualCheck";
import { ToastContainer } from "@/components/Toast";

type Tab = "dashboard" | "white" | "black" | "manual";

export default function HomePage() {
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [tab, setTab] = useState<Tab>("dashboard");

  const loadSummary = useCallback(async () => {
    try {
      const data = await api.getSummary();
      setSummary(data);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    loadSummary();
    const interval = setInterval(loadSummary, 30000);
    return () => clearInterval(interval);
  }, [loadSummary]);

  const whiteAlive = (summary?.white || []).reduce((s, src) => s + src.alive, 0);
  const blackAlive = (summary?.black || []).reduce((s, src) => s + src.alive, 0);

  const tabs: { id: Tab; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: "dashboard", label: "Обзор", icon: <Shield size={14} /> },
    { id: "white", label: "Для отключений", icon: <Globe size={14} />, badge: whiteAlive || undefined },
    { id: "black", label: "Обычный VPN", icon: <Shield size={14} />, badge: blackAlive || undefined },
    { id: "manual", label: "Ручная проверка", icon: <Wrench size={14} /> },
  ];

  return (
    <div className="min-h-screen">
      <ToastContainer />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {/* Header */}
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-purple-400 flex items-center justify-center text-white font-extrabold text-lg shadow-lg shadow-accent/20">
              V
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">
                VPN <span className="text-accent-light">Monitor</span>
              </h1>
              <p className="text-[11px] text-muted -mt-0.5">Мониторинг VPN-профилей</p>
            </div>
          </div>

        </header>

        {/* Status */}
        <div className="mb-6">
          <StatusBar data={summary} />
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-bg-card border border-border rounded-xl p-1 overflow-x-auto">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                "flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap min-h-[44px]",
                tab === t.id
                  ? "bg-accent text-white shadow-sm"
                  : "text-muted hover:text-zinc-300 hover:bg-bg-hover"
              )}
            >
              {t.icon}
              {t.label}
              {t.badge !== undefined && (
                <span
                  className={cn(
                    "px-1.5 py-0.5 rounded-full text-[10px] font-bold",
                    tab === t.id ? "bg-white/20" : "bg-zinc-800 text-zinc-400"
                  )}
                >
                  {t.badge}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        <main>
          {tab === "dashboard" && (
            <div className="space-y-8 animate-fade-in">
              {/* White list section */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-accent-dim flex items-center justify-center">
                    <Globe size={16} className="text-accent-light" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold">Белые списки</h2>
                    <p className="text-[11px] text-muted">
                      При отключении мобильного интернета (CIDR/SNI обход)
                    </p>
                  </div>
                </div>
                <div className="space-y-2">
                  {(summary?.white || []).length === 0 ? (
                    <div className="glass p-8 text-center text-muted text-sm">
                      Данных пока нет. Проверка запускается автоматически.
                    </div>
                  ) : (
                    (summary?.white || []).map((src) => (
                      <SourceCard key={src.id} source={src} category="white" isChecking={summary?.is_checking ?? false} />
                    ))
                  )}
                </div>
              </section>

              {/* Black list section */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center">
                    <Shield size={16} className="text-zinc-400" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold">Чёрные списки</h2>
                    <p className="text-[11px] text-muted">
                      Обычный VPN — YouTube, WhatsApp, Instagram, Discord
                    </p>
                  </div>
                </div>
                <div className="space-y-2">
                  {(summary?.black || []).length === 0 ? (
                    <div className="glass p-8 text-center text-muted text-sm">
                      Данных пока нет. Проверка запускается автоматически.
                    </div>
                  ) : (
                    (summary?.black || []).map((src) => (
                      <SourceCard key={src.id} source={src} category="black" isChecking={summary?.is_checking ?? false} />
                    ))
                  )}
                </div>
              </section>
            </div>
          )}

          {tab === "white" && (
            <div className="space-y-2 animate-fade-in">
              {(summary?.white || []).map((src) => (
                <SourceCard key={src.id} source={src} category="white" isChecking={summary?.is_checking ?? false} />
              ))}
            </div>
          )}

          {tab === "black" && (
            <div className="space-y-2 animate-fade-in">
              {(summary?.black || []).map((src) => (
                <SourceCard key={src.id} source={src} category="black" isChecking={summary?.is_checking ?? false} />
              ))}
            </div>
          )}

          {tab === "manual" && (
            <div className="animate-fade-in">
              <ManualCheck />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
