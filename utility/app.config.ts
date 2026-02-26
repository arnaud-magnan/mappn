import { ExpoConfig, ConfigContext } from 'expo/config';

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: 'Mappn',
  slug: 'mappn',
  version: '1.0.0',
  orientation: 'portrait',
  icon: './assets/images/icon.png',
  scheme: 'mappn',
  userInterfaceStyle: 'automatic',
  newArchEnabled: true,
  splash: {
    image: './assets/images/splash-icon.png',
    resizeMode: 'contain',
    backgroundColor: '#ffffff',
  },
  ios: {
    supportsTablet: true,
    bundleIdentifier: 'com.mappn.utility',
    infoPlist: {
      NSLocationWhenInUseUsageDescription:
        'Mappn uses your location to find nearby places and track visits.',
    },
  },
  android: {
    package: 'com.mappn.utility',
    adaptiveIcon: {
      foregroundImage: './assets/images/adaptive-icon.png',
      backgroundColor: '#ffffff',
    },
    edgeToEdgeEnabled: true,
    permissions: ['ACCESS_FINE_LOCATION'],
    config: {
      googleMaps: {
        apiKey: process.env.GOOGLE_MAPS_ANDROID_KEY ?? '',
      },
    },
  },
  web: {
    bundler: 'metro',
    output: 'static',
    favicon: './assets/images/favicon.png',
  },
  plugins: [
    'expo-router',
    'expo-secure-store',
    [
      'expo-location',
      {
        locationWhenInUsePermission:
          'Allow Mappn to use your location to discover nearby places and track visits.',
      },
    ],
    [
      'expo-image-picker',
      {
        photosPermission:
          'Allow Mappn to access your photos for travel journal entries.',
        cameraPermission:
          'Allow Mappn to use your camera for travel journal photos.',
      },
    ],
  ],
  experiments: {
    typedRoutes: true,
  },
});
