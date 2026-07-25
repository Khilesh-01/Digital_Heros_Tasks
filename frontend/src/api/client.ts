import axios, { AxiosError } from "axios";
import type { ApiError, AuditReport } from "../types/audit";

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 20_000;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT_MS,
  headers: { "Content-Type": "application/json" },
});

/** A normalized, UI-friendly error - every failure path collapses into this shape. */
export class AuditRequestError extends Error {
  errorCode: string;

  constructor(message: string, errorCode: string) {
    super(message);
    this.name = "AuditRequestError";
    this.errorCode = errorCode;
  }
}

export async function auditUrl(url: string): Promise<AuditReport> {
  try {
    const response = await apiClient.post<AuditReport>("/audit", { url });
    return response.data;
  } catch (error) {
    throw normalizeError(error);
  }
}

export async function checkHealth(): Promise<boolean> {
  try {
    await apiClient.get("/health");
    return true;
  } catch {
    return false;
  }
}

function normalizeError(error: unknown): AuditRequestError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>;

    if (axiosError.response?.data?.message) {
      return new AuditRequestError(
        axiosError.response.data.message,
        axiosError.response.data.error_code ?? "unknown_error"
      );
    }
    if (axiosError.code === "ECONNABORTED") {
      return new AuditRequestError(
        "The request took too long and was cancelled. Please try again.",
        "client_timeout"
      );
    }
    if (!axiosError.response) {
      return new AuditRequestError(
        "Could not reach the Page Pulse API. Check your connection and try again.",
        "network_error"
      );
    }
  }
  return new AuditRequestError("Something went wrong. Please try again.", "unknown_error");
}
