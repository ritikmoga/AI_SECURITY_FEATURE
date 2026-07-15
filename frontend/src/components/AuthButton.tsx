import { useEffect, useRef, useState } from 'react';
import { clearSession, googleSignIn, saveSession } from '../lib/api';
import type { AppUser } from '../types';

declare global {
  interface Window { google?: { accounts: { id: { initialize: (config: object) => void; renderButton: (element: HTMLElement, options: object) => void } } } }
}

const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;

export function AuthButton({ user, onUser }: { user: AppUser | null; onUser: (user: AppUser | null) => void }) {
  const mount = useRef<HTMLDivElement>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!clientId || user) return;
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client'; script.async = true;
    script.onload = () => {
      if (!window.google || !mount.current) return;
      window.google.accounts.id.initialize({ client_id: clientId, callback: async (response: { credential: string }) => {
        try { const session = await googleSignIn(response.credential); saveSession(session); onUser(session.user); }
        catch (err) { setError(err instanceof Error ? err.message : 'Sign-in failed.'); }
      }});
      window.google.accounts.id.renderButton(mount.current, { theme: 'filled_black', size: 'large', shape: 'pill', text: 'signin_with' });
    };
    document.head.appendChild(script);
    return () => script.remove();
  }, [user, onUser]);

  if (user) return <div className="user-menu">{user.avatar_url ? <img src={user.avatar_url} alt="" /> : null}<span>{user.display_name}</span><button className="signout-btn" onClick={() => { clearSession(); onUser(null); }}>Sign out</button></div>;
  if (!clientId) return <span className="auth-note">Add VITE_GOOGLE_CLIENT_ID to enable sign-in</span>;
  return <div className="auth-wrap"><div ref={mount} />{error ? <small className="error-text">{error}</small> : null}</div>;
}
