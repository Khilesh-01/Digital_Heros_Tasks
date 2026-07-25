interface ErrorAlertProps {
  message: string;
  errorCode: string;
}

export function ErrorAlert({ message, errorCode }: ErrorAlertProps) {
  return (
    <div className="section error-alert" role="alert">
      <svg className="error-alert__icon" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <circle cx="10" cy="10" r="8.5" stroke="currentColor" strokeWidth="1.4" />
        <path d="M10 6v5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        <circle cx="10" cy="13.6" r="0.9" fill="currentColor" />
      </svg>
      <div>
        <p className="error-alert__title">Audit couldn't finish</p>
        <p className="error-alert__message">{message}</p>
        <p className="error-alert__code">{errorCode}</p>
      </div>
    </div>
  );
}
