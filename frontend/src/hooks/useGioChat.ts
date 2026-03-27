import { useCallback, useEffect, useRef, useState } from "react";
import { chatApi, type GioMessage, type GioAttachment, type AttachmentRef } from "../api/client";

const WS_BASE = import.meta.env.VITE_WS_URL ?? `ws://${window.location.host}`;

export function useGioChat(userId: string | null) {
  const [messages, setMessages] = useState<GioMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);

  // Load initial history
  useEffect(() => {
    if (!userId) return;
    loadHistory(1);
  }, [userId]);

  const loadHistory = useCallback(async (pageNum: number) => {
    try {
      const { data } = await chatApi.getHistory(pageNum);
      // Dismiss buttons on any assistant message that already has something after it —
      // those interactions are in the past and should not be re-activated on reload.
      const processed = data.map((msg, idx) => {
        if (msg.role === "assistant" && msg.buttons && idx < data.length - 1) {
          return { ...msg, buttons: null };
        }
        return msg;
      });
      if (pageNum === 1) {
        setMessages(processed);
      } else {
        // Older pages are always fully in the past — dismiss all their buttons.
        setMessages((prev) => [...processed.map((m) => ({ ...m, buttons: null })), ...prev]);
      }
      setHasMore(data.length === 50);
    } catch {
      // ignore
    }
  }, []);

  const loadMore = useCallback(() => {
    const nextPage = page + 1;
    setPage(nextPage);
    loadHistory(nextPage);
  }, [page, loadHistory]);

  // WebSocket connection with exponential backoff
  const connect = useCallback(() => {
    if (!userId) return;
    const token = localStorage.getItem("access_token");
    if (!token) return;

    const url = `${WS_BASE}/ws/${userId}?token=${token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const msg: GioMessage = JSON.parse(event.data);
        setMessages((prev) => {
          // Avoid duplicates
          if (prev.some((m) => m.id === msg.id)) return prev;
          return [...prev, msg];
        });
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Exponential backoff: 1s, 2s, 4s, 8s, max 30s
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
      reconnectAttempts.current += 1;
      reconnectTimerRef.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };

    // Keepalive ping every 30s
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [userId]);

  useEffect(() => {
    const cleanup = connect();
    return () => {
      cleanup?.();
      wsRef.current?.close();
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    };
  }, [connect]);

  const sendResponse = useCallback(
    async (
      messageId: string | null,
      buttonValue?: string,
      text?: string,
      buttonLabel?: string,
      attachmentRefs?: AttachmentRef[],
      attachmentDisplay?: GioAttachment[],
    ) => {
      setIsLoading(true);
      // Show a virtual user message immediately — use the button label for button presses
      // so the conversation flow is easy to follow.
      const displayContent = text ?? buttonLabel;
      if (displayContent) {
        const userMsg: GioMessage = {
          id: crypto.randomUUID(),
          role: "user",
          content: displayContent,
          timestamp: new Date().toISOString(),
          _attachments: attachmentDisplay?.length ? attachmentDisplay : undefined,
        };
        setMessages((prev) => [...prev, userMsg]);
      }
      try {
        const { data } = await chatApi.respond(messageId, buttonValue, text, buttonLabel, attachmentRefs);
        // WS will deliver the response; add it if WS is down
        setMessages((prev) => {
          if (prev.some((m) => m.id === data.id)) return prev;
          return [...prev, data];
        });
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  /** Dismiss button set on a specific message after a button tap. */
  const dismissButtons = useCallback((messageId: string) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === messageId ? { ...m, buttons: null } : m)),
    );
  }, []);

  return { messages, isLoading, isConnected, hasMore, loadMore, sendResponse, dismissButtons };
}
