'use client';
import { SWRConfig } from 'swr';
import { ReactNode } from 'react';

export function SWRProvider({ children }: { children: ReactNode }) {
  return (
    <SWRConfig
      value={{
        revalidateOnFocus: false,
        errorRetryCount: 3,
        errorRetryInterval: 5000,
        onError: (error: Error) => {
          console.error('[SWR]', error.message);
        },
      }}
    >
      {children}
    </SWRConfig>
  );
}
