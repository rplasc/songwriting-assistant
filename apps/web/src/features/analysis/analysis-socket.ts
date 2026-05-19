"use client";

import { wsUrl } from "@/lib/config";
import { io, type Socket } from "socket.io-client";
import type { Language } from "@/features/language/language-types";
import type { ServerAnalysisPayload } from "./analysis-types";
import type { RhymeMode } from "./rhyme-modes";

export interface SocketErrorPayload {
  message: string;
  code: string;
}

export interface EmitAnalyzeOptions {
  line: string;
  rhymeMode?: RhymeMode;
  language?: Language;
}

type AnalysisHandler = (payload: ServerAnalysisPayload) => void;
type ErrorHandler = (payload: SocketErrorPayload) => void;
type VoidHandler = () => void;

let socket: Socket | null = null;

function getSocket(): Socket {
  if (!socket) {
    socket = io(`${wsUrl}/editor`, {
      transports: ["websocket"],
      autoConnect: true,
    });

    if (process.env.NODE_ENV === "development") {
      socket.on("connect", () =>
        console.log("[WS /editor] connected", socket!.id),
      );
      socket.on("disconnect", (reason) =>
        console.log("[WS /editor] disconnected:", reason),
      );
      socket.on("connect_error", (err) =>
        console.warn("[WS /editor] connect_error:", err.message),
      );
    }
  }
  return socket;
}

export interface SocketAnalysisAdapter {
  emit: (options: EmitAnalyzeOptions) => void;
  onAnalysis: (handler: AnalysisHandler) => VoidHandler;
  onError: (handler: ErrorHandler) => VoidHandler;
  onConnectError: (handler: VoidHandler) => VoidHandler;
  isConnected: () => boolean;
}

export function getSocketAdapter(): SocketAnalysisAdapter {
  const s = getSocket();
  return {
    emit({ line, rhymeMode, language }) {
      const payload: {
        line: string;
        rhyme_mode?: RhymeMode;
        language?: Language;
      } = { line };
      if (rhymeMode) payload.rhyme_mode = rhymeMode;
      if (language) payload.language = language;
      s.emit("editor.analyze", payload);
    },
    onAnalysis(handler) {
      s.on("editor.analysis", handler);
      return () => s.off("editor.analysis", handler);
    },
    onError(handler) {
      s.on("editor.error", handler);
      return () => s.off("editor.error", handler);
    },
    onConnectError(handler) {
      s.on("connect_error", handler);
      return () => s.off("connect_error", handler);
    },
    isConnected: () => s.connected,
  };
}
