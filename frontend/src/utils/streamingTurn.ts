import type { ChatResponse } from "../types/chat";

/**
 * SSE metadata already contains the full user-visible turn (widgets, options,
 * or final narrative). Background token streams can be ignored for UI state.
 */
export function metadataCompletesStreamingTurn(
  response: ChatResponse,
): boolean {
  const metadataMessage = response.message?.trim() ?? "";

  if (response.presentation != null) {
    return true;
  }

  if (metadataMessage.length > 0) {
    return true;
  }

  if ((response.options?.length ?? 0) > 0) {
    return true;
  }

  return false;
}
