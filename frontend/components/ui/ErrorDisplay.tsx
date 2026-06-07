'use client';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorDisplayProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorDisplay({ message = 'Could not load data', onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-slate-400">
      <AlertTriangle className="h-8 w-8 text-amber-500 mb-3" />
      <p className="text-sm mb-3">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-2 text-xs text-indigo-400 hover:text-indigo-300 underline"
        >
          <RefreshCw className="h-3 w-3" /> Retry
        </button>
      )}
    </div>
  );
}
