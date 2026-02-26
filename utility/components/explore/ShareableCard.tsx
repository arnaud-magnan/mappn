/**
 * ShareableCard wraps the map and stats overlay in a capturable View.
 *
 * Uses react-native-view-shot's captureRef() to take a PNG snapshot of the
 * wrapped content. The capture() method is exposed via a forwarded ref so the
 * parent screen can trigger it on demand (e.g., from a share button press).
 *
 * Usage:
 *   const cardRef = useRef<ShareableCardRef>(null);
 *   const uri = await cardRef.current?.capture();
 */

import React, {
  forwardRef,
  useImperativeHandle,
  useRef,
} from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { captureRef } from 'react-native-view-shot';

import { THEME_COLORS } from '@/constants/colors';

export interface ShareableCardRef {
  /** Capture the card as a PNG and return the temporary file URI. */
  capture: () => Promise<string>;
}

export interface ShareableCardProps {
  /** City name shown in the stats overlay. */
  city: string;
  /** Number of unique places the user has visited. */
  placesVisited: number;
  /** Exploration percentage for the selected city (0-100). */
  exploredPct: number;
  /** Children (typically the MapView + HeatmapLayer). */
  children: React.ReactNode;
}

/**
 * A capturable card that wraps map content with a stats overlay.
 *
 * The outer View is the capture target for react-native-view-shot. The stats
 * overlay is rendered as an absolutely-positioned panel at the bottom so it
 * appears on top of the map in the generated image.
 */
export const ShareableCard = forwardRef<ShareableCardRef, ShareableCardProps>(
  function ShareableCard({ city, placesVisited, exploredPct, children }, ref) {
    const viewRef = useRef<View>(null);

    useImperativeHandle(ref, () => ({
      capture: async (): Promise<string> => {
        if (!viewRef.current) {
          throw new Error('ShareableCard: view ref is not attached');
        }
        return captureRef(viewRef, { format: 'png', quality: 1 });
      },
    }));

    const displayPct = Math.round(Math.min(100, Math.max(0, exploredPct)));

    return (
      <View ref={viewRef} style={styles.container} collapsable={false}>
        {children}

        {/* Stats overlay rendered on top of the map content */}
        <View style={styles.statsOverlay}>
          <Text style={styles.cityName}>{city}</Text>
          <Text style={styles.stat}>{placesVisited} places visited</Text>
          <Text style={styles.stat}>{displayPct}% explored</Text>
        </View>
      </View>
    );
  }
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: 'hidden',
  },
  statsOverlay: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.92)',
    borderRadius: 12,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 4,
  },
  cityName: {
    fontSize: 16,
    fontWeight: '700',
    color: THEME_COLORS.text,
    marginBottom: 4,
  },
  stat: {
    fontSize: 13,
    color: THEME_COLORS.textSecondary,
    lineHeight: 18,
  },
});
