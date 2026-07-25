export function SkeletonLoader() {
  return (
    <div className="section skeleton-card" role="status" aria-label="Auditing page">
      <div className="skeleton-line" style={{ width: "40%" }} />
      <div className="skeleton-line" style={{ width: "70%" }} />
      <div className="skeleton-line" style={{ width: "55%" }} />
      <div className="skeleton-line" style={{ width: "85%" }} />
      <span className="visually-hidden">Auditing the page, please wait…</span>
    </div>
  );
}
