import { useState } from "react";
import type { AuditReport } from "../types/audit";

interface ReportCardProps {
  report: AuditReport;
  onCopied: () => void;
}

function statusTier(status: number): "ok" | "warn" | "bad" {
  if (status >= 200 && status < 300) return "ok";
  if (status >= 300 && status < 400) return "warn";
  return "bad";
}

function formatBytes(bytes?: number | null): string {
  if (!bytes && bytes !== 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export function ReportCard({ report, onCopied }: ReportCardProps) {
  const [downloaded, setDownloaded] = useState(false);
  const tier = statusTier(report.status);
  const hasAltIssues = report.images_without_alt > 0;

  async function handleCopy() {
    await navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    onCopied();
  }

  function handleDownload() {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const safeHost = report.url.replace(/^https?:\/\//, "").replace(/[^\w.-]/g, "_");
    link.href = url;
    link.download = `page-pulse-${safeHost}.json`;
    link.click();
    URL.revokeObjectURL(url);
    setDownloaded(true);
    window.setTimeout(() => setDownloaded(false), 2000);
  }

  return (
    <section className="section report-card" aria-label="Audit report">
      <div className="report-card__header">
        <div>
          <span className="report-card__url">{report.url}</span>
          <h2 className="report-card__title">{report.title ?? "Untitled page"}</h2>
        </div>
        <div className="report-card__actions">
          <span className={`status-pill ${tier}`}>
            <span className="status-pill__dot" />
            HTTP {report.status}
          </span>
        </div>
      </div>

      <div className="report-card__meta">
        <div className="label">Meta description</div>
        <div>{report.meta_description ?? "No meta description found."}</div>
      </div>

      <div className="metrics-grid">
        <div className="metric-tile">
          <span className="metric-tile__value">{report.response_time_ms}ms</span>
          <span className="metric-tile__label">Response time</span>
        </div>
        <div className="metric-tile">
          <span className="metric-tile__value">{report.h1_count}</span>
          <span className="metric-tile__label">H1 headings</span>
        </div>
        <div className="metric-tile">
          <span className={`metric-tile__value${hasAltIssues ? " alert" : ""}`}>
            {report.images_without_alt}
          </span>
          <span className="metric-tile__label">
            Images missing alt{report.total_images != null ? ` / ${report.total_images}` : ""}
          </span>
        </div>
        <div className="metric-tile">
          <span className="metric-tile__value">{report.word_count.toLocaleString()}</span>
          <span className="metric-tile__label">Words on page</span>
        </div>
        {report.seo_score != null && (
          <div className="metric-tile">
            <span className="metric-tile__value">{report.seo_score}/100</span>
            <span className="metric-tile__label">SEO health score</span>
          </div>
        )}
      </div>

      <div className="report-card__extra">
        <div className="extra-item">
          <div className="label">Canonical URL</div>
          <div className="value">{report.canonical_url ?? "Not set"}</div>
        </div>
        <div className="extra-item">
          <div className="label">Open Graph title</div>
          <div className="value">{report.og_title ?? "Not set"}</div>
        </div>
        <div className="extra-item">
          <div className="label">Language</div>
          <div className="value">{report.language ?? "Not declared"}</div>
        </div>
        <div className="extra-item">
          <div className="label">Favicon</div>
          <div className="value">{report.favicon_present ? "Present" : "Not found"}</div>
        </div>
        <div className="extra-item">
          <div className="label">Page size</div>
          <div className="value">{formatBytes(report.content_size_bytes)}</div>
        </div>
      </div>

      <div className="report-card__header" style={{ borderTop: "1px solid var(--color-border)", borderBottom: "none" }}>
        <span className="field-hint" style={{ margin: 0 }}>
          Full report, ready to share
        </span>
        <div className="report-card__actions">
          <button type="button" className="icon-btn" onClick={handleCopy}>
            Copy JSON
          </button>
          <button type="button" className="icon-btn" onClick={handleDownload}>
            {downloaded ? "Downloaded ✓" : "Download JSON"}
          </button>
        </div>
      </div>
    </section>
  );
}
