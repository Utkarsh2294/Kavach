import { http, HttpResponse } from 'msw';

/**
 * Mock data for the authenticated user
 */
const mockUser = {
  id: 'usr_1234567890abcdef',
  name: 'Test User',
  email: 'test@kavach.dev',
  role: 'admin',
  organizationId: 'org_0987654321fedcba',
  createdAt: '2023-01-15T12:00:00Z'
};

/**
 * POST /api/v1/auth/login
 * Request: { email: string, password: string }
 * Response 200: { user: { id, name, email, role, organizationId, createdAt }, accessToken, refreshToken }
 * Response 401: { error: { code: 'INVALID_CREDENTIALS', message: 'Invalid email or password' } }
 */
const loginHandler = http.post('/api/v1/auth/login', async ({ request }) => {
  const { email, password } = await request.json();

  if (!email || !password) {
    return HttpResponse.json({ error: { code: 'INVALID_CREDENTIALS', message: 'Invalid email or password' } }, { status: 401 });
  }

  // Accept any password for mock purposes
  return HttpResponse.json({
    user: { ...mockUser, email },
    accessToken: 'mock_access_token_xyz',
    refreshToken: 'mock_refresh_token_abc'
  }, { status: 200 });
});

/**
 * POST /api/v1/auth/signup  
 * Request: { name: string, email: string, password: string }
 * Response 201: { user: { id, name, email, role, organizationId, createdAt }, accessToken, refreshToken }
 * Response 409: { error: { code: 'EMAIL_EXISTS', message: 'An account with this email already exists' } }
 */
const signupHandler = http.post('/api/v1/auth/signup', async ({ request }) => {
  const { name, email, password } = await request.json();

  if (email === 'exists@kavach.dev') {
    return HttpResponse.json({ error: { code: 'EMAIL_EXISTS', message: 'An account with this email already exists' } }, { status: 409 });
  }

  return HttpResponse.json({
    user: { ...mockUser, name, email },
    accessToken: 'mock_access_token_xyz',
    refreshToken: 'mock_refresh_token_abc'
  }, { status: 201 });
});

/**
 * POST /api/v1/auth/forgot-password
 * Request: { email: string }
 * Response 200: { message: 'If an account with that email exists, a reset link has been sent.' }
 */
const forgotPasswordHandler = http.post('/api/v1/auth/forgot-password', async () => {
  return HttpResponse.json({
    message: 'If an account with that email exists, a reset link has been sent.'
  }, { status: 200 });
});

/**
 * POST /api/v1/auth/reset-password
 * Request: { token: string, password: string }
 * Response 200: { message: 'Password has been reset successfully.' }
 * Response 400: { error: { code: 'INVALID_TOKEN', message: 'Reset token is invalid or expired' } }
 */
const resetPasswordHandler = http.post('/api/v1/auth/reset-password', async ({ request }) => {
  const { token } = await request.json();
  
  if (token === 'invalid') {
    return HttpResponse.json({ error: { code: 'INVALID_TOKEN', message: 'Reset token is invalid or expired' } }, { status: 400 });
  }

  return HttpResponse.json({
    message: 'Password has been reset successfully.'
  }, { status: 200 });
});

/**
 * POST /api/v1/auth/logout
 * Response 200: { message: 'Logged out successfully' }
 */
const logoutHandler = http.post('/api/v1/auth/logout', async () => {
  return HttpResponse.json({
    message: 'Logged out successfully'
  }, { status: 200 });
});

/**
 * GET /api/v1/auth/me
 * Response 200: { user: { id, name, email, role, organizationId, createdAt } }
 * Response 401: { error: { code: 'UNAUTHORIZED', message: 'Not authenticated' } }
 */
const meHandler = http.get('/api/v1/auth/me', async ({ request }) => {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer mock_access_token')) {
    return HttpResponse.json({ error: { code: 'UNAUTHORIZED', message: 'Not authenticated' } }, { status: 401 });
  }
  
  return HttpResponse.json({
    user: mockUser
  }, { status: 200 });
});

export const authHandlers = [
  loginHandler,
  signupHandler,
  forgotPasswordHandler,
  resetPasswordHandler,
  logoutHandler,
  meHandler
];
