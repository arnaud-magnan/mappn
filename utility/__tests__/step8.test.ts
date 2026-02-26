import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..');

describe('Step 8: Auth Flow (Service, Screens, Root Layout)', () => {
  // =========================================================================
  // 1. authService.ts
  // =========================================================================
  describe('services/authService.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'services/authService.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports api instance from ./api', () => {
      expect(content).toContain("from './api'");
    });

    it('imports useAuthStore from stores/authStore', () => {
      expect(content).toContain('useAuthStore');
    });

    it('imports AuthTokenResponse type', () => {
      expect(content).toContain('AuthTokenResponse');
    });

    // login
    it('exports login function', () => {
      expect(content).toMatch(/export\s+(const|async\s+function|function)\s+login/);
    });

    it('login accepts email and password parameters', () => {
      expect(content).toMatch(/login[\s\S]*email\s*:\s*string[\s\S]*password\s*:\s*string/);
    });

    it('login calls POST /auth/login', () => {
      expect(content).toContain('/auth/login');
      expect(content).toContain('.post');
    });

    it('login stores tokens via auth store setTokens', () => {
      expect(content).toContain('setTokens');
    });

    // register
    it('exports register function', () => {
      expect(content).toMatch(/export\s+(const|async\s+function|function)\s+register/);
    });

    it('register accepts email, username, and password parameters', () => {
      expect(content).toMatch(/register[\s\S]*email\s*:\s*string[\s\S]*username\s*:\s*string[\s\S]*password\s*:\s*string/);
    });

    it('register calls POST /auth/register', () => {
      expect(content).toContain('/auth/register');
    });

    it('register stores tokens via auth store setTokens', () => {
      // setTokens is used by both login and register
      const setTokensCalls = content.match(/setTokens/g);
      expect(setTokensCalls).not.toBeNull();
      expect(setTokensCalls!.length).toBeGreaterThanOrEqual(2);
    });

    // refreshToken
    it('exports refreshToken function', () => {
      expect(content).toMatch(/export\s+(const|async\s+function|function)\s+refreshToken/);
    });

    it('refreshToken calls POST /auth/refresh', () => {
      expect(content).toContain('/auth/refresh');
    });

    it('refreshToken reads current refresh token from auth store', () => {
      expect(content).toContain('getState');
      expect(content).toContain('refreshToken');
    });

    // logout
    it('exports logout function', () => {
      expect(content).toMatch(/export\s+(const|async\s+function|function)\s+logout/);
    });

    it('logout calls clearAuth to clear SecureStore and auth store', () => {
      expect(content).toContain('clearAuth');
    });
  });

  // =========================================================================
  // 2. locationStore.ts
  // =========================================================================
  describe('stores/locationStore.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'stores/locationStore.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports zustand create', () => {
      expect(content).toContain('zustand');
      expect(content).toContain('create');
    });

    it('has latitude state', () => {
      expect(content).toContain('latitude');
    });

    it('has longitude state', () => {
      expect(content).toContain('longitude');
    });

    it('has accuracy state', () => {
      expect(content).toContain('accuracy');
    });

    it('has isTracking state', () => {
      expect(content).toContain('isTracking');
    });

    it('has setLocation action', () => {
      expect(content).toContain('setLocation');
    });

    it('has setTracking action', () => {
      expect(content).toContain('setTracking');
    });

    it('exports useLocationStore hook', () => {
      expect(content).toMatch(/export\s+(const|function)\s+useLocationStore/);
    });
  });

  // =========================================================================
  // 3. mapStore.ts
  // =========================================================================
  describe('stores/mapStore.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'stores/mapStore.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports zustand create', () => {
      expect(content).toContain('zustand');
      expect(content).toContain('create');
    });

    it('has region state', () => {
      expect(content).toContain('region');
    });

    it('has selectedPlaceId state', () => {
      expect(content).toContain('selectedPlaceId');
    });

    it('has activeFilters state', () => {
      expect(content).toContain('activeFilters');
    });

    it('has setRegion action', () => {
      expect(content).toContain('setRegion');
    });

    it('has setSelectedPlace action', () => {
      expect(content).toContain('setSelectedPlace');
    });

    it('has toggleFilter action', () => {
      expect(content).toContain('toggleFilter');
    });

    it('exports useMapStore hook', () => {
      expect(content).toMatch(/export\s+(const|function)\s+useMapStore/);
    });
  });

  // =========================================================================
  // 4. Root layout (_layout.tsx)
  // =========================================================================
  describe('app/_layout.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/_layout.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports GestureHandlerRootView', () => {
      expect(content).toContain('GestureHandlerRootView');
      expect(content).toContain('react-native-gesture-handler');
    });

    it('imports QueryClientProvider and QueryClient', () => {
      expect(content).toContain('QueryClientProvider');
      expect(content).toContain('QueryClient');
      expect(content).toContain('@tanstack/react-query');
    });

    it('creates a QueryClient instance', () => {
      expect(content).toContain('new QueryClient');
    });

    it('wraps app in GestureHandlerRootView', () => {
      expect(content).toContain('<GestureHandlerRootView');
    });

    it('wraps app in QueryClientProvider', () => {
      expect(content).toContain('<QueryClientProvider');
    });

    it('imports useAuthStore for token checking', () => {
      expect(content).toContain('useAuthStore');
    });

    it('calls loadTokens on mount to check existing session', () => {
      expect(content).toContain('loadTokens');
    });

    it('uses expo-router for navigation (Slot or Stack)', () => {
      expect(content).toMatch(/Slot|Stack/);
      expect(content).toContain('expo-router');
    });

    it('imports ErrorBoundary for error wrapping', () => {
      expect(content).toContain('ErrorBoundary');
    });

    it('redirects to (auth)/login when no tokens', () => {
      expect(content).toContain('(auth)/login');
    });

    it('redirects to (tabs) when tokens are present', () => {
      expect(content).toContain('(tabs)');
    });

    it('uses router.replace for navigation', () => {
      expect(content).toContain('router.replace');
    });

    it('includes Stack.Screen for (auth) group', () => {
      expect(content).toContain('(auth)');
    });

    it('includes Stack.Screen for (tabs) group', () => {
      expect(content).toContain('(tabs)');
    });
  });

  // =========================================================================
  // 5. Auth layout
  // =========================================================================
  describe('app/(auth)/_layout.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(auth)/_layout.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('uses Stack layout from expo-router', () => {
      expect(content).toContain('Stack');
      expect(content).toContain('expo-router');
    });

    it('has headerShown false for no navigation header overlap', () => {
      expect(content).toContain('headerShown');
    });

    it('has screen definitions for login and register', () => {
      expect(content).toContain('login');
      expect(content).toContain('register');
    });

    it('exports a default layout function', () => {
      expect(content).toMatch(/export\s+default\s+function/);
    });
  });

  // =========================================================================
  // 6. Login screen
  // =========================================================================
  describe('app/(auth)/login.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(auth)/login.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('has email TextInput field', () => {
      expect(content).toContain('TextInput');
      expect(content).toMatch(/email/i);
    });

    it('has password TextInput field', () => {
      expect(content).toContain('secureTextEntry');
    });

    it('has email format validation', () => {
      expect(content).toMatch(/@|email.*valid|invalid.*email/i);
    });

    it('has required field validation', () => {
      expect(content).toMatch(/required|Please enter/i);
    });

    it('displays error messages for failed login', () => {
      expect(content).toMatch(/error|Error/);
    });

    it('calls authService.login on submit', () => {
      expect(content).toContain('login');
    });

    it('has link to register screen', () => {
      expect(content).toMatch(/register|Register|Sign up|sign up/i);
    });

    it('navigates to (tabs) on successful login', () => {
      expect(content).toContain('router.replace');
      expect(content).toContain('(tabs)');
    });

    it('uses Button component from ui library', () => {
      expect(content).toContain('Button');
    });

    it('imports from expo-router for navigation', () => {
      expect(content).toContain('expo-router');
    });

    it('exports a default screen function', () => {
      expect(content).toMatch(/export\s+default\s+function/);
    });
  });

  // =========================================================================
  // 7. Register screen
  // =========================================================================
  describe('app/(auth)/register.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(auth)/register.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('has email TextInput field', () => {
      expect(content).toContain('TextInput');
      expect(content).toMatch(/email/i);
    });

    it('has username TextInput field', () => {
      expect(content).toMatch(/username/i);
    });

    it('has password TextInput field', () => {
      expect(content).toContain('secureTextEntry');
    });

    it('has email format validation', () => {
      expect(content).toMatch(/@|email.*valid|invalid.*email/i);
    });

    it('has required field validation for all fields', () => {
      expect(content).toMatch(/required|Please enter/i);
    });

    it('has password minimum length validation', () => {
      expect(content).toMatch(/length|8.*character|character.*8/i);
    });

    it('displays error messages for failed registration', () => {
      expect(content).toMatch(/error|Error/);
    });

    it('calls authService.register on submit', () => {
      expect(content).toContain('register');
    });

    it('has link to login screen', () => {
      expect(content).toMatch(/login|Login|Sign in|sign in|Already have/i);
    });

    it('navigates to (tabs) on successful registration', () => {
      expect(content).toContain('router.replace');
      expect(content).toContain('(tabs)');
    });

    it('uses Button component from ui library', () => {
      expect(content).toContain('Button');
    });

    it('imports from expo-router for navigation', () => {
      expect(content).toContain('expo-router');
    });

    it('exports a default screen function', () => {
      expect(content).toMatch(/export\s+default\s+function/);
    });
  });

  // =========================================================================
  // 8. Judge-identified fixes: session expiry, refresh token format,
  //    network error detection, layout flash prevention
  // =========================================================================

  describe('authStore sessionExpired field', () => {
    let content: string;
    const filePath = path.join(ROOT, 'stores/authStore.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('has sessionExpired boolean field in interface', () => {
      expect(content).toContain('sessionExpired: boolean');
    });

    it('has setSessionExpired method in interface', () => {
      expect(content).toContain('setSessionExpired');
    });

    it('initializes sessionExpired to false', () => {
      expect(content).toContain('sessionExpired: false');
    });

    it('implements setSessionExpired action', () => {
      expect(content).toMatch(/setSessionExpired.*expired.*boolean/);
    });
  });

  describe('api.ts refresh token format and session expiry', () => {
    let content: string;
    const filePath = path.join(ROOT, 'services/api.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('sends refresh token as Bearer header (not request body)', () => {
      // The interceptor should use Authorization: Bearer header
      expect(content).toContain('Authorization: `Bearer ${refresh_token}`');
    });

    it('sends empty object as request body for refresh', () => {
      // Should post empty body: {}, not { refresh_token }
      expect(content).toMatch(/axios\.post[\s\S]*?\{\}[\s\S]*?headers/);
    });

    it('does NOT send refresh_token as request body property', () => {
      // The old bug: axios.post(url, { refresh_token })
      // The fix: axios.post(url, {}, { headers: { Authorization: ... } })
      // Verify there is no line that looks like a body with refresh_token property
      const lines = content.split('\n');
      const bodyLines = lines.filter(line =>
        line.trim().match(/^\{\s*refresh_token\s*\}/)
      );
      expect(bodyLines.length).toBe(0);
    });

    it('sets sessionExpired flag before redirecting to login', () => {
      expect(content).toContain('setSessionExpired(true)');
    });

    it('destructures setSessionExpired from auth store on refresh failure', () => {
      expect(content).toContain('setSessionExpired');
      expect(content).toContain('clearAuth');
    });
  });

  describe('login.tsx session expiry message', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(auth)/login.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('imports useAuthStore', () => {
      expect(content).toContain('useAuthStore');
    });

    it('imports useEffect', () => {
      expect(content).toContain('useEffect');
    });

    it('checks sessionExpired on mount', () => {
      expect(content).toContain('sessionExpired');
    });

    it('displays session expired message', () => {
      expect(content).toContain('Session expired, please log in again');
    });

    it('clears sessionExpired flag after showing message', () => {
      expect(content).toContain('setSessionExpired(false)');
    });
  });

  describe('login.tsx network error detection', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(auth)/login.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('checks for missing response (network error) before status codes', () => {
      expect(content).toContain('!axiosError.response');
    });

    it('shows network error message', () => {
      expect(content).toContain('Network error. Please check your connection.');
    });
  });

  describe('register.tsx network error detection', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(auth)/register.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('checks for missing response (network error) before status codes', () => {
      expect(content).toContain('!axiosError.response');
    });

    it('shows network error message', () => {
      expect(content).toContain('Network error. Please check your connection.');
    });
  });

  describe('_layout.tsx flash prevention', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/_layout.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('returns null when isReady is false to prevent screen flash', () => {
      expect(content).toContain('if (!isReady) return null');
    });
  });
});
