import type { ChatResponse } from "../types/chat";

const API_BASE_URL = "/api";

export class ApiError extends Error {
  statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

function getErrorMessage(responseBody: unknown, statusCode: number): string {
  if (typeof responseBody !== "object" || responseBody === null) {
    return statusCode === 404
      ? "The chat endpoint was not found. Check that the backend is running on port 8000."
      : "The request could not be completed.";
  }

  if ("detail" in responseBody && typeof responseBody.detail === "string") {
    return responseBody.detail;
  }

  if ("message" in responseBody && typeof responseBody.message === "string") {
    return responseBody.message;
  }

  if ("detail" in responseBody && Array.isArray(responseBody.detail)) {
    const validationMessages = responseBody.detail
      .filter(
        (item): item is { msg: string } =>
          typeof item === "object" &&
          item !== null &&
          "msg" in item &&
          typeof item.msg === "string",
      )
      .map((item) => item.msg);

    if (validationMessages.length > 0) {
      return validationMessages.join(" ");
    }
  }

  return statusCode === 404
    ? "The chat endpoint was not found. Check that the backend is running on port 8000."
    : "The request could not be completed.";
}

export async function sendChatMessage(
  customerId: string,
  message: string,
): Promise<ChatResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Customer-ID": customerId,
      },
      body: JSON.stringify({
        message,
      }),
    });
  } catch {
    throw new ApiError(
      "The NexaTel backend is unavailable. Make sure it is running on port 8000.",
      0,
    );
  }

  let responseBody: unknown = null;

  try {
    responseBody = await response.json();
  } catch {
    // Some proxies return an empty body for network-level errors.
  }

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(responseBody, response.status),
      response.status,
    );
  }

  if (
    typeof responseBody !== "object" ||
    responseBody === null ||
    !("message" in responseBody) ||
    !("status" in responseBody)
  ) {
    throw new ApiError(
      "The backend returned an invalid response.",
      response.status,
    );
  }

  return responseBody as ChatResponse;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch("/health");

    return response.ok;
  } catch {
    return false;
  }
}
