'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

const SHORTCUTS: Record<string, string> = {
  'ctrl+k': '/chat',
  'ctrl+b': '/knowledge',
  'ctrl+m': '/memory',
  'ctrl+d': '/dashboard',
  'ctrl+g': '/graph',
  'ctrl+p': '/proactive',
  'ctrl+,': '/settings',
};

export default function KeyboardShortcuts() {
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + 快捷键
      if (e.ctrlKey || e.metaKey) {
        const key = e.key.toLowerCase();
        const shortcut = `ctrl+${key}`;

        if (SHORTCUTS[shortcut]) {
          e.preventDefault();
          router.push(SHORTCUTS[shortcut]);
        }
      }

      // / 聚焦搜索（在聊天页面）
      if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
        const target = e.target as HTMLElement;
        if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
          e.preventDefault();
          router.push('/chat');
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [router]);

  return null;
}
