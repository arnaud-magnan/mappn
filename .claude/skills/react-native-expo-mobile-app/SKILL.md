---
name: React Native + Expo Mobile App
description: Patterns, libraries, and tooling for building geolocation-aware mobile apps with React Native and Expo SDK 52+, covering maps, navigation, location tracking, state management, and data visualization.
topics: react-native, expo, expo-router, react-native-maps, expo-location, tanstack-query, zustand, charts, heatmap, geolocation, bottom-sheet, NativeWind, EAS
created: 2026-02-25
updated: 2026-02-25
scratchpad: .specs/scratchpad/dee86e2d.md
---

# React Native + Expo Mobile App

## Overview

Expo SDK 52 (React Native 0.76) with New Architecture enabled by default is the production-ready foundation for cross-platform iOS/Android mobile apps. Expo Router v4 (file-based routing) + react-native-maps + TanStack Query v5 + Zustand is the recommended stack for geolocation-aware apps with map views, GPS tracking, and data visualization. EAS (Expo Application Services) handles builds and OTA updates.

---

## Key Concepts

- **Expo SDK 52**: React Native 0.76, New Architecture (Fabric + JSI) on by default. Use as baseline.
- **Expo Router v4**: File-based routing built on React Navigation. `(tabs)/_layout.tsx` for bottom tabs. Automatic deep linking.
- **New Architecture**: All recommended libraries must explicitly support New Architecture (check library docs/changelog).
- **EAS Build**: Cloud build service for iOS/Android binaries. `eas.json` defines build profiles.
- **EAS Update**: OTA (over-the-air) JS bundle updates without app store resubmission (JS-only changes only).
- **Config Plugins**: Expo managed workflow extensibility. Native dependencies use `plugins` array in `app.json`/`app.config.ts` instead of manual native modifications.
- **Managed Workflow**: Avoid ejecting to bare workflow. Use config plugins for native customization.
- **MapView.Polygon vs Heatmap**: Polygon overlays per district = "neighborhoods fill in" UX. Heatmap = density visualization. Polygon is better for city exploration % display.
- **tracksViewChanges**: Set `false` on static map markers — critical performance optimization.
- **TanStack Query**: Server state (API data, caching, background refetch). NOT a replacement for client state.
- **Zustand**: Lightweight client state (user location, auth tokens, UI flags). Complements TanStack Query.

---

## Documentation & References

| Resource | Description | Link |
|----------|-------------|------|
| Expo SDK 52 Changelog | SDK 52 features, React Native 0.76, New Arch default | https://expo.dev/changelog/sdk-52 |
| Expo Router Docs | File-based routing, layouts, tabs, deep linking | https://docs.expo.dev/router/introduction/ |
| Expo Location SDK | GPS tracking, background tasks, permissions | https://docs.expo.dev/versions/latest/sdk/location/ |
| Expo SecureStore | Keychain/Keystore token storage | https://docs.expo.dev/versions/latest/sdk/securestore/ |
| Expo ImagePicker | Camera and gallery access | https://docs.expo.dev/versions/latest/sdk/imagepicker/ |
| Expo Image | High-performance image display | https://docs.expo.dev/versions/latest/sdk/image/ |
| Expo Sharing | Native share sheet | https://docs.expo.dev/versions/latest/sdk/sharing/ |
| Expo Notifications | Push and local notifications | https://docs.expo.dev/versions/latest/sdk/notifications/ |
| EAS Build | Cloud builds, signing, app store submission | https://docs.expo.dev/build/introduction/ |
| react-native-maps | Map components, markers, polygons, heatmap | https://github.com/react-native-maps/react-native-maps |
| react-native-maps installation | Expo config plugin setup, API keys | https://github.com/react-native-maps/react-native-maps/blob/master/docs/installation.md |
| TanStack Query v5 | Server state, caching, background refetch | https://tanstack.com/query/latest |
| TanStack Query Persist | AsyncStorage cache persistence | https://tanstack.com/query/latest/docs/framework/react/plugins/persistQueryClient |
| Zustand | Lightweight client state management | https://github.com/pmndrs/zustand |
| React Native Reanimated v3 | Animations, gestures | https://docs.swmansion.com/react-native-reanimated/ |
| Gorhom Bottom Sheet | Map place preview bottom sheet | https://gorhom.github.io/react-native-bottom-sheet/ |
| react-native-gifted-charts | Bar/line/pie charts, pure RN | https://github.com/Abhinandan-Kushwaha/react-native-gifted-charts |
| Victory Native XL | Skia-based charts for New Architecture | https://commerce.nearform.com/open-source/victory-native/ |
| NativeWind v4 | Tailwind CSS for React Native | https://www.nativewind.dev/ |
| react-native-view-shot | Capture RN view as shareable image | https://github.com/gre/react-native-view-shot |
| react-native-map-clustering | Marker clustering for map performance | https://github.com/venits/react-native-map-clustering |

---

## Recommended Libraries & Tools

| Name | Purpose | Maturity | Notes |
|------|---------|----------|-------|
| expo (SDK 52) | Core framework | Stable | New Architecture default |
| expo-router v4 | File-based navigation | Stable | Replaces React Navigation direct usage for new projects |
| react-native-maps v1.14+ | Maps, markers, polygons, heatmap | Stable | v1.14+ required for New Architecture |
| expo-location | GPS tracking (foreground + background) | Stable | Needs expo-task-manager for background |
| expo-task-manager | Background task execution | Stable | Required for background location |
| @tanstack/react-query v5 | Server state and API cache | Stable | Use with Axios fetcher |
| @tanstack/react-query-persist-client | Persist query cache to AsyncStorage | Stable | Offline-first UX |
| zustand | Client state (location, auth, UI) | Stable | Minimal boilerplate |
| axios | HTTP client with interceptors | Stable | Auth token injection, 401 refresh |
| @react-native-async-storage/async-storage | Persistent key-value storage | Stable | User prefs, TanStack persister |
| expo-secure-store | Secure JWT token storage | Stable | Keychain/Keystore backed |
| expo-image-picker | Camera + gallery access | Stable | Journal photo capture |
| expo-image | High-performance image display | Stable | Better than built-in Image |
| expo-sharing | Native share sheet | Stable | Share exploration map image |
| react-native-view-shot | Capture view as image | Stable | Export exploration map |
| react-native-reanimated v3 | Animations | Stable | Built into Expo SDK 52 |
| react-native-gesture-handler | Gesture support | Stable | Required peer dep, in Expo |
| @gorhom/bottom-sheet | Place preview bottom sheet on map | Stable | Built with Reanimated 3 |
| react-native-gifted-charts | Bar charts (popular times histogram) | Stable | Pure RN, no native deps |
| NativeWind v4 | Tailwind CSS styling | Stable | Works with Expo Router + New Arch |
| react-native-map-clustering | Cluster map markers | Stable | Drop-in MapView replacement |
| expo-notifications | Push and local notifications | Stable | Achievement alerts, visit confirmations |
| @expo/vector-icons | Icon library (MaterialIcons, etc.) | Stable | Bundled with Expo |

### Recommended Stack for Mappn Utility App

Expo SDK 52 + Expo Router v4 for navigation. react-native-maps for maps with custom busyness-colored markers, Geojson/Polygon overlays for exploration districts, and `@gorhom/bottom-sheet` for place preview. TanStack Query v5 + Zustand for state. expo-location for GPS. expo-secure-store for JWT storage. react-native-gifted-charts for popular times histogram. react-native-view-shot + expo-sharing for exploration map export.

---

## Patterns & Best Practices

### Expo Router Bottom Tabs Layout

**When to use**: Main app navigation with bottom tab bar.

```typescript
// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

export default function TabLayout() {
  return (
    <Tabs>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Map',
          tabBarIcon: ({ color }) => <MaterialIcons name="map" size={28} color={color} />,
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{ title: 'Explore' }}
      />
      <Tabs.Screen
        name="journal"
        options={{ title: 'Journal' }}
      />
      <Tabs.Screen
        name="profile"
        options={{ title: 'Profile' }}
      />
    </Tabs>
  );
}
```

### react-native-maps Configuration (Expo)

**When to use**: Any screen requiring a map.

app.json config:
```json
{
  "expo": {
    "plugins": [
      [
        "react-native-maps",
        {
          "iosGoogleMapsApiKey": "YOUR_IOS_KEY",
          "androidGoogleMapsApiKey": "YOUR_ANDROID_KEY"
        }
      ]
    ]
  }
}
```

### Custom Busyness-Colored Markers

**When to use**: Map pins colored by busyness level (green/yellow/red).

```tsx
import MapView, { Marker, Callout } from 'react-native-maps';

const BUSYNESS_COLORS = { quiet: '#22c55e', moderate: '#eab308', busy: '#ef4444' };

function BusynessMarker({ place }) {
  const color = BUSYNESS_COLORS[place.busynessLevel];
  return (
    <Marker
      coordinate={{ latitude: place.lat, longitude: place.lng }}
      tracksViewChanges={false}  // CRITICAL for performance
    >
      <View style={{ backgroundColor: color, width: 12, height: 12, borderRadius: 6 }} />
      <Callout>
        <Text>{place.name}</Text>
        <Text>Busyness: {place.busynessLevel}</Text>
      </Callout>
    </Marker>
  );
}
```

### District Polygon Overlay (Exploration Map)

**When to use**: Rendering visited/unvisited neighborhoods as colored fills.

```tsx
import MapView, { Geojson } from 'react-native-maps';

// Backend serves district boundaries as GeoJSON FeatureCollection
// Each feature has `visited: boolean` in properties

function ExplorationMap({ districts }) {
  return (
    <MapView style={StyleSheet.absoluteFillObject}>
      <Geojson
        geojson={districts}
        fillColor="rgba(34, 197, 94, 0.4)"   // visited = green fill
        strokeColor="#22c55e"
        strokeWidth={1}
        tracksViewChanges={false}
      />
    </MapView>
  );
}
```

### expo-location Foreground GPS Tracking

**When to use**: Sending GPS updates to backend while app is open.

app.json permissions:
```json
{
  "expo": {
    "plugins": [
      ["expo-location", {
        "locationWhenInUsePermission": "Allow Mappn to use your location to track visits."
      }]
    ]
  }
}
```

```typescript
import * as Location from 'expo-location';

async function startTracking(onUpdate: (coords) => void) {
  const { status } = await Location.requestForegroundPermissionsAsync();
  if (status !== 'granted') return;

  await Location.watchPositionAsync(
    { accuracy: Location.Accuracy.Balanced, timeInterval: 30000, distanceInterval: 20 },
    (location) => onUpdate(location.coords)
  );
}
```

### TanStack Query + Axios Setup

**When to use**: All API data fetching and caching.

```typescript
// services/api.ts
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

export const api = axios.create({ baseURL: process.env.EXPO_PUBLIC_API_URL });

api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// hooks/usePlacesNearby.ts
import { useQuery } from '@tanstack/react-query';

export function usePlacesNearby(lat: number, lng: number) {
  return useQuery({
    queryKey: ['places', 'nearby', lat, lng],
    queryFn: () => api.get('/places/nearby', { params: { lat, lng } }).then(r => r.data),
    staleTime: 5 * 60 * 1000,  // 5 minutes
  });
}
```

### Zustand Auth Store

**When to use**: Client-side auth state (token, user object, location).

```typescript
import { create } from 'zustand';

interface AuthStore {
  user: User | null;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));
```

### Bottom Sheet for Place Preview

**When to use**: Tapping a map pin shows place details in a bottom sheet.

```tsx
import BottomSheet, { BottomSheetView } from '@gorhom/bottom-sheet';

const bottomSheetRef = useRef<BottomSheet>(null);
const snapPoints = useMemo(() => ['25%', '50%'], []);

<BottomSheet ref={bottomSheetRef} snapPoints={snapPoints} index={-1} enablePanDownToClose>
  <BottomSheetView>
    <Text>{selectedPlace?.name}</Text>
  </BottomSheetView>
</BottomSheet>
```

### Exploration Map Export (Share)

**When to use**: Sharing exploration map as image with stats overlay.

```typescript
import { captureRef } from 'react-native-view-shot';
import * as Sharing from 'expo-sharing';

async function shareExplorationMap(mapRef: RefObject<View>) {
  const uri = await captureRef(mapRef, { format: 'png', quality: 0.9 });
  await Sharing.shareAsync(uri);
}
```

---

## Project Structure

```
app/                        # Expo Router file-based routes
  (tabs)/
    index.tsx               # Map view (home)
    explore.tsx             # Exploration heatmap
    journal.tsx             # Travel journal
    profile.tsx             # Profile & stats
    _layout.tsx             # Bottom tab bar layout
  place/
    [id].tsx                # Place detail screen
  auth/
    login.tsx
    register.tsx
  _layout.tsx               # Root layout (QueryClient, GestureHandler, etc.)

components/                 # Reusable UI components
  map/
    BusynessMarker.tsx
    PlaceCallout.tsx
    DistrictOverlay.tsx
  charts/
    PopularTimesChart.tsx
    BusynessForecastSlider.tsx
  journal/
    JournalEntry.tsx
  profile/
    AchievementBadge.tsx
    StatCard.tsx

hooks/                      # Custom React hooks
  usePlacesNearby.ts
  usePlaceDetail.ts
  useLocationTracking.ts
  useJournalEntries.ts

stores/                     # Zustand stores
  authStore.ts
  locationStore.ts
  uiStore.ts

services/                   # API client and external services
  api.ts                    # Axios instance with interceptors
  visits.ts                 # Visit confirmation logic

constants/
  colors.ts                 # Busyness colors, theme colors
  config.ts

assets/
  fonts/
  images/

app.config.ts               # Expo config (plugins, permissions, env vars)
eas.json                    # EAS Build profiles
```

---

## Similar Implementations

### Expo Router Official Tutorial

- **Source**: https://docs.expo.dev/tutorial/introduction/
- **Approach**: File-based routing with `(tabs)` group, nested stacks, config plugins
- **Applicability**: Direct pattern for Mappn tab navigation structure

### Expo Location Background Tracking Example

- **Source**: https://github.com/expo/expo/tree/main/apps/native-component-list/src/screens/Location
- **Approach**: `expo-location` + `expo-task-manager` for background GPS
- **Applicability**: Visit detection GPS loop pattern

---

## Common Pitfalls & Solutions

| Issue | Impact | Solution |
|-------|--------|----------|
| `tracksViewChanges={true}` on many markers | High - severe map jank | Always set `tracksViewChanges={false}` on static markers |
| Missing Google Maps API key on Android | High - blank map | Enable Maps SDK for Android in Google Cloud Console; add key to app.json plugin |
| MapView.Heatmap is Google Maps only | High - iOS fails | Use Polygon overlays for district visualization instead; Heatmap needs `googleMaps` provider prop |
| Background location rejected by App Store | High - app rejected | Request foreground-only first; justify "always" permission with clear UX copy |
| New Architecture incompatible library | Medium - runtime crash | Verify library changelog for "New Architecture" or "Fabric" support before adding |
| JWT stored in AsyncStorage (insecure) | High - security risk | Use `expo-secure-store` (Keychain/Keystore) for all tokens |
| TanStack Query staleTime=0 on map data | Medium - excessive API calls | Set staleTime >= 5min for nearby places; live busyness = shorter staleTime |
| Ejecting from managed workflow | High - maintenance burden | Avoid ejecting; use config plugins for native customization |
| expo-location on simulator | Low - no GPS data | Use Simulator > Features > Location for testing location on iOS Simulator |
| EAS Build without eas.json profiles | Medium - build fails | Always define development, preview, production profiles in eas.json |

---

## Recommendations

1. **Use Expo Router v4 with `(tabs)` group**: Standard file-based navigation with zero-boilerplate deep linking for all four main tabs.
2. **react-native-maps with Geojson/Polygon for exploration map**: Native Google/Apple maps with district polygon overlays is simpler and more aligned with "neighborhoods fill in" UX than a density heatmap.
3. **Set `tracksViewChanges={false}` on all static markers**: This single change prevents the most common map performance issue in react-native-maps.
4. **TanStack Query v5 + Zustand side by side**: Keep server state (API) in TanStack Query with appropriate staleTime per data type; keep client state (location, auth, UI) in Zustand.
5. **expo-secure-store for JWT tokens**: Never store auth tokens in AsyncStorage; always use Keychain/Keystore via expo-secure-store.
6. **Foreground location tracking only for MVP**: Background location complicates App Store review and drains battery. Foreground-only is sufficient for visit detection while app is open.
7. **app.config.ts (TypeScript) over app.json**: Enables dynamic env var injection (e.g., `process.env.EXPO_PUBLIC_API_URL`) and programmatic config.

---

## Implementation Guidance

### Installation

```bash
# Create new Expo project with Expo Router
npx create-expo-app@latest mappn-app --template tabs

# Maps
npx expo install react-native-maps

# Location
npx expo install expo-location expo-task-manager

# State management
npm install @tanstack/react-query@5 @tanstack/react-query-persist-client @tanstack/async-storage-persister zustand axios

# Storage
npx expo install @react-native-async-storage/async-storage expo-secure-store

# UI and images
npx expo install expo-image expo-image-picker expo-sharing
npm install react-native-view-shot

# Animations and bottom sheet
npx expo install react-native-reanimated react-native-gesture-handler
npm install @gorhom/bottom-sheet

# Charts
npm install react-native-gifted-charts

# Marker clustering
npm install react-native-map-clustering

# NativeWind (Tailwind CSS)
npm install nativewind tailwindcss
npx tailwindcss init

# Build tooling
npm install -g eas-cli
eas login
eas build:configure
```

### app.config.ts Setup

```typescript
import { ExpoConfig, ConfigContext } from 'expo/config';

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: 'Mappn',
  slug: 'mappn',
  plugins: [
    ['react-native-maps', {
      androidGoogleMapsApiKey: process.env.GOOGLE_MAPS_ANDROID_KEY,
      iosGoogleMapsApiKey: process.env.GOOGLE_MAPS_IOS_KEY,
    }],
    ['expo-location', {
      locationWhenInUsePermission: 'Allow Mappn to use your location to discover nearby places and track visits.',
    }],
    ['expo-image-picker', {
      photosPermission: 'Allow Mappn to access your photos for travel journal entries.',
      cameraPermission: 'Allow Mappn to use your camera for travel journal photos.',
    }],
  ],
  ios: {
    bundleIdentifier: 'com.mappn.utility',
    infoPlist: {
      NSLocationWhenInUseUsageDescription: 'Mappn uses your location to find nearby places.',
    },
  },
  android: {
    package: 'com.mappn.utility',
    permissions: ['ACCESS_FINE_LOCATION'],
  },
});
```

### Root Layout Setup (QueryClient + GestureHandler)

```tsx
// app/_layout.tsx
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Slot } from 'expo-router';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 5 * 60 * 1000 } },
});

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <Slot />
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
```

### EAS Build Profiles (eas.json)

```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal"
    },
    "production": {
      "autoIncrement": true
    }
  },
  "submit": {
    "production": {}
  }
}
```

---

## Sources & Verification

| Source | Type | Last Verified |
|--------|------|---------------|
| https://expo.dev/changelog/sdk-52 | Official | 2026-02-25 |
| https://docs.expo.dev/router/introduction/ | Official | 2026-02-25 |
| https://docs.expo.dev/versions/latest/sdk/location/ | Official | 2026-02-25 |
| https://docs.expo.dev/versions/latest/sdk/securestore/ | Official | 2026-02-25 |
| https://github.com/react-native-maps/react-native-maps/blob/master/docs/installation.md | Official | 2026-02-25 |
| https://github.com/react-native-maps/react-native-maps/blob/master/docs/heatmap.md | Official | 2026-02-25 |
| https://tanstack.com/query/latest | Official | 2026-02-25 |
| https://github.com/pmndrs/zustand | Official | 2026-02-25 |
| https://docs.swmansion.com/react-native-reanimated/ | Official | 2026-02-25 |
| https://gorhom.github.io/react-native-bottom-sheet/ | Official | 2026-02-25 |
| https://github.com/Abhinandan-Kushwaha/react-native-gifted-charts | Community | 2026-02-25 |
| https://www.nativewind.dev/ | Official | 2026-02-25 |
| https://github.com/gre/react-native-view-shot | Community | 2026-02-25 |
| https://github.com/venits/react-native-map-clustering | Community | 2026-02-25 |
| Context7 MCP - Expo llms.txt | Official docs mirror | 2026-02-25 |
| Context7 MCP - react-native-maps | Official docs mirror | 2026-02-25 |

---

## Changelog

| Date | Changes |
|------|---------|
| 2026-02-25 | Initial creation for task: implement-utility-app.feature.md |
