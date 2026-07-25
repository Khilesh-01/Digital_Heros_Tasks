import { useEffect, useRef, useState } from "react";
import { AuditForm } from "./components/AuditForm";
import { EmptyState } from "./components/EmptyState";
import { ErrorAlert } from "./components/ErrorAlert";
import { Footer } from "./components/Footer";
import { Header } from "./components/Header";
import { ReportCard } from "./components/ReportCard";
import { SkeletonLoader } from "./components/SkeletonLoader";
import { Toast } from "./components/Toast";
import { auditUrl, AuditRequestError } from "./api/client";
import type { AuditReport } from "./types/audit";

type AuditState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; report: AuditReport }
  | { status: "error"; message: string; errorCode: string };

export default function App() {
  const [state, setState] = useState<AuditState>({ status: "idle" });
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const toastTimer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (toastTimer.current) window.clearTimeout(toastTimer.current);
    };
  }, []);

  function showToast(message: string) {
    setToastMessage(message);
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToastMessage(null), 2200);
  }

  async function handleAudit(url: string) {
    setState({ status: "loading" });
    try {
      const report = await auditUrl(url);
      setState({ status: "success", report });
    } catch (error) {
      const err = error as AuditRequestError;
      setState({ status: "error", message: err.message, errorCode: err.errorCode });
    }
  }

  return (
    <div className="page-shell">
      <div className="container">
        <Header isAuditing={state.status === "loading"} />
        <AuditForm onSubmit={handleAudit} isLoading={state.status === "loading"} />

        {state.status === "idle" && <EmptyState />}
        {state.status === "loading" && <SkeletonLoader />}
        {state.status === "error" && (
          <ErrorAlert message={state.message} errorCode={state.errorCode} />
        )}
        {state.status === "success" && (
          <ReportCard report={state.report} onCopied={() => showToast("Report copied to clipboard")} />
        )}
      </div>

      {toastMessage && <Toast message={toastMessage} />}
      <Footer />
    </div>
  );
}
