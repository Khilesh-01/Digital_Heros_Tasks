import { FormEvent, useState } from "react";

interface AuditFormProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

function looksLikeUrl(value: string): boolean {
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export function AuditForm({ onSubmit, isLoading }: AuditFormProps) {
  const [value, setValue] = useState("");
  const [touched, setTouched] = useState(false);

  const trimmed = value.trim();
  const hasValue = trimmed.length > 0;
  const isValid = hasValue && looksLikeUrl(trimmed);
  const showError = touched && hasValue && !isValid;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setTouched(true);
    if (!isValid || isLoading) return;
    onSubmit(trimmed);
  }

  return (
    <form className="section" onSubmit={handleSubmit} noValidate>
      <div className="audit-form">
        <label htmlFor="audit-url" className="visually-hidden">
          Page URL to audit
        </label>
        <input
          id="audit-url"
          type="text"
          inputMode="url"
          autoComplete="url"
          placeholder="https://your-website.com"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onBlur={() => setTouched(true)}
          aria-invalid={showError}
          aria-describedby={showError ? "audit-url-error" : "audit-url-hint"}
          disabled={isLoading}
        />
        <button type="submit" className="btn-audit" disabled={isLoading}>
          {isLoading ? "Auditing…" : "Audit page"}
        </button>
      </div>
      {showError ? (
        <p id="audit-url-error" className="field-error" role="alert">
          Enter a full URL starting with http:// or https://
        </p>
      ) : (
        <p id="audit-url-hint" className="field-hint">
          Example: https://example.com
        </p>
      )}
    </form>
  );
}
