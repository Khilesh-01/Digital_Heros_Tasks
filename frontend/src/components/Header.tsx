import { PulseLine } from "./PulseLine";

interface HeaderProps {
  isAuditing: boolean;
}

export function Header({ isAuditing }: HeaderProps) {
  return (
    <header className="site-header">
      <span className="brand-mark">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.4" />
          <path d="M4 8h1.6l.8-2.6L8 11l1-4.5.7 1.5H12" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Page Pulse
      </span>
      <h1>Know what your page says before your visitors do.</h1>
      <p className="lede">
        Paste any public URL and get an instant read on response time, SEO
        basics, and structure — no signup, no crawling delay.
      </p>
      <PulseLine active={isAuditing} />
    </header>
  );
}
