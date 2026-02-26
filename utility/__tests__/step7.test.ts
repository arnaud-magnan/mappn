import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..');
const UI_DIR = path.join(ROOT, 'components/ui');

describe('Step 7: Shared UI Components', () => {
  describe('Barrel export (components/ui/index.ts)', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(path.join(UI_DIR, 'index.ts'), 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(path.join(UI_DIR, 'index.ts'))).toBe(true);
    });

    const expectedExports = [
      'Button',
      'Card',
      'LoadingSpinner',
      'EmptyState',
      'ErrorBoundary',
      'NetworkBanner',
    ];

    it.each(expectedExports)('exports %s', (name) => {
      expect(content).toContain(name);
    });
  });

  describe('Button.tsx', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(path.join(UI_DIR, 'Button.tsx'), 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(path.join(UI_DIR, 'Button.tsx'))).toBe(true);
    });

    it('defines ButtonProps interface', () => {
      expect(content).toContain('ButtonProps');
    });

    it('accepts title prop', () => {
      expect(content).toContain('title');
    });

    it('accepts onPress prop', () => {
      expect(content).toContain('onPress');
    });

    it('accepts loading prop', () => {
      expect(content).toContain('loading');
    });

    it('accepts disabled prop', () => {
      expect(content).toContain('disabled');
    });

    it('accepts variant prop', () => {
      expect(content).toContain('variant');
    });

    it('has primary, secondary, and text variants', () => {
      expect(content).toContain('primary');
      expect(content).toContain('secondary');
      expect(content).toContain('text');
    });

    it('renders ActivityIndicator for loading state', () => {
      expect(content).toContain('ActivityIndicator');
    });

    it('uses colors from constants/colors', () => {
      expect(content).toContain('colors');
      expect(content).toMatch(/THEME_COLORS/);
    });

    it('uses Pressable (not TouchableOpacity)', () => {
      expect(content).toContain('Pressable');
    });

    it('exports Button function', () => {
      expect(content).toMatch(/export\s+(function|const)\s+Button/);
    });
  });

  describe('Card.tsx', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(path.join(UI_DIR, 'Card.tsx'), 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(path.join(UI_DIR, 'Card.tsx'))).toBe(true);
    });

    it('defines CardProps interface', () => {
      expect(content).toContain('CardProps');
    });

    it('accepts children prop', () => {
      expect(content).toContain('children');
    });

    it('accepts optional title prop', () => {
      expect(content).toContain('title');
    });

    it('accepts optional padding prop', () => {
      expect(content).toContain('padding');
    });

    it('has border radius styling', () => {
      expect(content).toContain('borderRadius');
    });

    it('has shadow styling', () => {
      expect(content).toMatch(/shadow|elevation/);
    });

    it('uses colors from constants/colors', () => {
      expect(content).toMatch(/THEME_COLORS/);
    });

    it('exports Card function', () => {
      expect(content).toMatch(/export\s+(function|const)\s+Card/);
    });
  });

  describe('LoadingSpinner.tsx', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(UI_DIR, 'LoadingSpinner.tsx'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(path.join(UI_DIR, 'LoadingSpinner.tsx'))
      ).toBe(true);
    });

    it('defines LoadingSpinnerProps interface', () => {
      expect(content).toContain('LoadingSpinnerProps');
    });

    it('renders ActivityIndicator', () => {
      expect(content).toContain('ActivityIndicator');
    });

    it('accepts optional message prop', () => {
      expect(content).toContain('message');
    });

    it('accepts optional size prop', () => {
      expect(content).toContain('size');
    });

    it('centers content', () => {
      expect(content).toMatch(/alignItems.*center|justifyContent.*center/);
    });

    it('uses colors from constants/colors', () => {
      expect(content).toMatch(/THEME_COLORS/);
    });

    it('exports LoadingSpinner function', () => {
      expect(content).toMatch(/export\s+(function|const)\s+LoadingSpinner/);
    });
  });

  describe('EmptyState.tsx', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(path.join(UI_DIR, 'EmptyState.tsx'), 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(path.join(UI_DIR, 'EmptyState.tsx'))).toBe(true);
    });

    it('defines EmptyStateProps interface', () => {
      expect(content).toContain('EmptyStateProps');
    });

    it('accepts icon prop', () => {
      expect(content).toContain('icon');
    });

    it('accepts title prop', () => {
      expect(content).toContain('title');
    });

    it('accepts description prop', () => {
      expect(content).toContain('description');
    });

    it('accepts optional actionLabel prop', () => {
      expect(content).toContain('actionLabel');
    });

    it('accepts optional onAction prop', () => {
      expect(content).toContain('onAction');
    });

    it('uses MaterialIcons', () => {
      expect(content).toContain('MaterialIcons');
    });

    it('uses colors from constants/colors', () => {
      expect(content).toMatch(/THEME_COLORS/);
    });

    it('exports EmptyState function', () => {
      expect(content).toMatch(/export\s+(function|const)\s+EmptyState/);
    });
  });

  describe('ErrorBoundary.tsx', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(UI_DIR, 'ErrorBoundary.tsx'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(path.join(UI_DIR, 'ErrorBoundary.tsx'))
      ).toBe(true);
    });

    it('is a class component (extends Component)', () => {
      expect(content).toMatch(/class\s+ErrorBoundary\s+extends\s+Component/);
    });

    it('implements componentDidCatch lifecycle', () => {
      expect(content).toContain('componentDidCatch');
    });

    it('implements getDerivedStateFromError static method', () => {
      expect(content).toContain('getDerivedStateFromError');
    });

    it('tracks hasError state', () => {
      expect(content).toContain('hasError');
    });

    it('logs error in componentDidCatch', () => {
      expect(content).toMatch(/console\.(error|warn|log)/);
    });

    it('accepts children prop', () => {
      expect(content).toContain('children');
    });

    it('accepts optional fallback prop', () => {
      expect(content).toContain('fallback');
    });

    it('provides retry functionality', () => {
      expect(content).toMatch(/retry|Retry|handleRetry/i);
    });

    it('uses colors from constants/colors', () => {
      expect(content).toMatch(/THEME_COLORS/);
    });

    it('exports ErrorBoundary class', () => {
      expect(content).toMatch(/export\s+class\s+ErrorBoundary/);
    });
  });

  describe('NetworkBanner.tsx', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(UI_DIR, 'NetworkBanner.tsx'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(path.join(UI_DIR, 'NetworkBanner.tsx'))
      ).toBe(true);
    });

    it('imports from @react-native-community/netinfo', () => {
      expect(content).toContain('@react-native-community/netinfo');
    });

    it('uses NetInfo.addEventListener to monitor connectivity', () => {
      expect(content).toContain('addEventListener');
    });

    it('uses NetInfo.fetch to get initial state', () => {
      expect(content).toContain('fetch');
    });

    it('tracks isConnected state', () => {
      expect(content).toContain('isConnected');
    });

    it('returns null when connected (banner is hidden)', () => {
      expect(content).toContain('return null');
    });

    it('accepts optional message prop', () => {
      expect(content).toContain('message');
    });

    it('unsubscribes from connectivity changes on unmount', () => {
      expect(content).toMatch(/unsubscribe|return\s+NetInfo\.addEventListener|return\s+unsubscribe/);
    });

    it('uses useEffect for subscription lifecycle', () => {
      expect(content).toContain('useEffect');
    });

    it('uses colors from constants/colors', () => {
      expect(content).toMatch(/THEME_COLORS/);
    });

    it('exports NetworkBanner function', () => {
      expect(content).toMatch(/export\s+(function|const)\s+NetworkBanner/);
    });
  });
});
