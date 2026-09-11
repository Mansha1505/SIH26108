/**
 * Demo Authentication Configuration for SIH Prototype.
 * Configurable in one single location.
 * Uses environment variables if available, with sensible default fallbacks.
 */

export const DEMO_AUTH_CONFIG = {
  officerId: import.meta.env.VITE_DEMO_OFFICER_ID || 'OFFICER-2026',
  password: import.meta.env.VITE_DEMO_PASSWORD || 'sih26108',
  officerName: 'Procurement Officer (BIS Portal)',
  department: 'Central Public Procurement Portal / BIS Standards Cell',
  sessionKey: 'sih26108_officer_session',
};
