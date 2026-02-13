"use client";

import { useEffect, useState, useCallback } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastType = "success" | "error" | "info";

interface ToastItem {
  id: number;
  message: string;
  type: ToastType;
}

let _addToast: ((msg: string, type: ToastType) => void) | null = null;

export function toast(message: string, type: ToastType = "info") {
  _addToast?.(message, type);
}

let _nextId = 0;

export function ToastContainer() {
  const [items, setItems] = useState<ToastItem[]>([]);

  const add = useCallback((message: string, type: ToastType) => {
    const id = ++_nextId;
    setItems((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setItems((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  useEffect(() => {
    _addToast = add;
    return () => {
      _addToast = null;
    };
  }, [add]);

  const remove = (id: number) => setItems((prev) => prev.filter((t) => t.id !== id));

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm" aria-live="polite" role="status">
      {items.map((t) => (
        <div
          key={t.id}
          className={cn(
            "animate-slide-in flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium",
            t.type === "success" && "bg-success/90 text-white",
            t.type === "error" && "bg-danger/90 text-white",
            t.type === "info" && "bg-accent/90 text-white",
          )}
        >
          <span className="flex-1">{t.message}</span>
          <button onClick={() => remove(t.id)} className="opacity-70 hover:opacity-100">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
