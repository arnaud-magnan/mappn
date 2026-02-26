/**
 * Territory Detail screen.
 *
 * Displays territory information including zone type, owner, chief creature,
 * familiarity rankings, and passive reward rate. Provides conditional action
 * buttons based on territory state:
 * - Unclaimed: "Claim" button (disabled if no prior visit to area)
 * - PvP: "Challenge" button with creature selector modal
 * - Cooperative: "Contribute" button
 * - Personal: "Claim as Home" button with residents list
 *
 * Uses useTerritoryDetail hook for data fetching and useCreatures for
 * creature selection in claim/challenge/contribute flows.
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Alert,
  FlatList,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { useQueryClient } from '@tanstack/react-query';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

import { GAME_COLORS, ZONE_COLORS } from '@/constants/colors';
import { useTerritoryDetail } from '@/hooks/useTerritoryDetail';
import { useCreatures } from '@/hooks/useCreatures';
import { useLocationStore } from '@/stores/locationStore';
import {
  claimTerritory,
  contributeToTerritory,
  claimHome,
  getResidents,
} from '@/services/territoryService';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FamiliarityRanking } from '@/components/territory/FamiliarityRanking';
import { PassiveRateDisplay } from '@/components/territory/PassiveRateDisplay';
import { ChallengeButton } from '@/components/territory/ChallengeButton';
import { CreatureResponse, ResidentResponse } from '@/types/api';

/** Maps zone_type strings to human-readable labels. */
const ZONE_TYPE_LABELS: Record<string, string> = {
  personal: 'Personal Zone',
  cooperative: 'Cooperative Zone',
  pvp: 'PvP Zone',
};

export default function TerritoryDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const territoryId = id !== undefined ? parseInt(id, 10) : null;
  const queryClient = useQueryClient();

  const { data: territory, isLoading, error } = useTerritoryDetail(
    Number.isNaN(territoryId) ? null : territoryId
  );
  const { data: creaturesData } = useCreatures({ limit: 100 });

  const [isClaimModalVisible, setIsClaimModalVisible] = useState(false);
  const [isContributeModalVisible, setIsContributeModalVisible] =
    useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [isClaimingHome, setIsClaimingHome] = useState(false);
  const [residents, setResidents] = useState<ResidentResponse[]>([]);

  // Location availability check - disable actions when location is denied
  const userLat = useLocationStore((state) => state.latitude);
  const userLon = useLocationStore((state) => state.longitude);
  const hasLocation = userLat !== null && userLon !== null;

  const creatures = creaturesData?.creatures ?? [];
  const availableCreatures = creatures.filter(
    (c) => c.assigned_territory_id === null
  );
  // All creatures including those already assigned (for reassignment flow)
  const allCreatures = creatures;

  const isUnclaimed = territory?.owner_id === null || territory?.owner_id === undefined;
  const isPvp = territory?.zone_type === 'pvp';
  const isCooperative = territory?.zone_type === 'cooperative';
  const isPersonal = territory?.zone_type === 'personal';
  const hasVisited = territory?.has_visited === true;

  const zoneType = territory?.zone_type ?? 'personal';
  const zoneColor =
    ZONE_COLORS[zoneType as keyof typeof ZONE_COLORS] ?? GAME_COLORS.primary;

  // Parse familiarity rankings from territory data
  const familiarityRankings = (territory?.familiarity_rankings ?? []).map(
    (entry: Record<string, unknown>) => ({
      user_id: String(entry.user_id ?? ''),
      username: String(entry.username ?? 'Unknown'),
      score: Number(entry.score ?? 0),
    })
  );

  // Fetch residents when the territory is a personal zone
  useEffect(() => {
    if (isPersonal && territoryId !== null) {
      getResidents(territoryId)
        .then(setResidents)
        .catch(() => setResidents([]));
    }
  }, [isPersonal, territoryId]);

  /**
   * Claim a personal zone territory as the player's home base.
   * Shows cooldown-specific messaging when the API rejects with a cooldown error.
   */
  const handleClaimHome = useCallback(async () => {
    if (territoryId === null) return;
    setIsClaimingHome(true);
    try {
      await claimHome(territoryId);
      await queryClient.invalidateQueries({ queryKey: ['territories'] });
      // Refresh residents list after successful claim
      const updatedResidents = await getResidents(territoryId);
      setResidents(updatedResidents);
      Alert.alert('Home Claimed', 'You have claimed this hex as your home base.');
    } catch (err: unknown) {
      const responseData =
        typeof err === 'object' &&
        err !== null &&
        'response' in err
          ? (err as { response?: { data?: { detail?: string } } })
              .response?.data?.detail ?? ''
          : '';

      if (responseData.toLowerCase().includes('cooldown')) {
        Alert.alert(
          'Cooldown Active',
          'You must wait before claiming a new home. Please try again later.'
        );
      } else {
        Alert.alert(
          'Claim Failed',
          responseData || 'Could not claim this hex as your home. Please try again.'
        );
      }
    } finally {
      setIsClaimingHome(false);
    }
  }, [territoryId, queryClient]);

  /**
   * Attempt to claim a territory with a creature.
   *
   * Handles two specific error scenarios:
   * 1. "Visit this area first" - player has not visited the territory area
   * 2. Creature already assigned - prompts for reassignment confirmation
   */
  const handleClaim = useCallback(
    async (creatureId: number) => {
      if (territoryId === null) return;

      // Check if the selected creature is currently assigned to another territory
      const selectedCreature = allCreatures.find(
        (c) => c.id === creatureId
      );
      if (
        selectedCreature !== undefined &&
        selectedCreature.assigned_territory_id !== null
      ) {
        // Creature is currently chief of another territory - prompt reassignment
        Alert.alert(
          'Reassign Creature',
          `This creature is currently chief of Territory #${selectedCreature.assigned_territory_id}. Reassigning it will remove it from that territory. Continue?`,
          [
            { text: 'Cancel', style: 'cancel' },
            {
              text: 'Reassign',
              style: 'destructive',
              onPress: () => performClaim(territoryId, creatureId),
            },
          ]
        );
        return;
      }

      await performClaim(territoryId, creatureId);
    },
    [territoryId, allCreatures]
  );

  /**
   * Execute the claim API call and handle error responses.
   */
  const performClaim = useCallback(
    async (tId: number, creatureId: number) => {
      setIsActionLoading(true);
      try {
        await claimTerritory(tId, creatureId);
        await queryClient.invalidateQueries({
          queryKey: ['territories'],
        });
        setIsClaimModalVisible(false);
        router.back();
      } catch (err: unknown) {
        // Parse error response to show appropriate message
        const errorMessage =
          err instanceof Error ? err.message : '';
        const responseData =
          typeof err === 'object' &&
          err !== null &&
          'response' in err
            ? (err as { response?: { data?: { detail?: string } } })
                .response?.data?.detail ?? ''
            : '';

        if (
          errorMessage.includes('visit') ||
          responseData.includes('visit') ||
          responseData.includes('Visit')
        ) {
          Alert.alert(
            'Cannot Claim',
            'Visit this area first. You must have at least one confirmed visit to this area before claiming it.'
          );
        } else {
          Alert.alert(
            'Claim Failed',
            'Could not claim this territory. Please try again.'
          );
        }
      } finally {
        setIsActionLoading(false);
      }
    },
    [queryClient]
  );

  const handleContribute = useCallback(
    async (creatureId: number) => {
      if (territoryId === null) return;
      setIsActionLoading(true);
      try {
        await contributeToTerritory(territoryId, creatureId);
        await queryClient.invalidateQueries({
          queryKey: ['territories'],
        });
        setIsContributeModalVisible(false);
      } catch (err) {
        // Let error propagate to UI
      } finally {
        setIsActionLoading(false);
      }
    },
    [territoryId, queryClient]
  );

  const handleChallengeComplete = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['territories'] });
  }, [queryClient]);

  if (isLoading) {
    return <LoadingSpinner message="Loading territory..." />;
  }

  if (error !== null || territory === undefined) {
    return (
      <View style={styles.errorContainer}>
        <MaterialIcons name="error" size={48} color={GAME_COLORS.error} />
        <Text style={styles.errorText}>
          Failed to load territory details.
        </Text>
        <Button title="Go Back" onPress={() => router.back()} variant="secondary" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton}>
          <MaterialIcons name="arrow-back" size={24} color={GAME_COLORS.text} />
        </Pressable>
        <Text style={styles.screenTitle}>Territory Detail</Text>
      </View>

      {/* Zone Type Badge */}
      <View style={styles.zoneTypeContainer}>
        <View style={[styles.zoneTypeBadge, { backgroundColor: zoneColor }]}>
          <Text style={styles.zoneTypeText}>
            {ZONE_TYPE_LABELS[zoneType] ?? zoneType}
          </Text>
        </View>
      </View>

      {/* Owner Info */}
      <Card title="Owner" style={styles.section}>
        {isUnclaimed ? (
          <View style={styles.unclaimedRow}>
            <MaterialIcons
              name="flag"
              size={20}
              color={GAME_COLORS.textSecondary}
            />
            <Text style={styles.unclaimedText}>Unclaimed Territory</Text>
          </View>
        ) : (
          <View>
            <View style={styles.ownerRow}>
              <MaterialIcons
                name="person"
                size={20}
                color={GAME_COLORS.primary}
              />
              <Text style={styles.ownerName}>
                {territory.owner_username ?? 'Unknown Player'}
              </Text>
            </View>
            {territory.chief_creature_id !== null && (
              <View style={styles.chiefRow}>
                <MaterialIcons
                  name="pets"
                  size={16}
                  color={GAME_COLORS.accent}
                />
                <Text style={styles.chiefText}>
                  Chief: {territory.chief_creature_name ?? `Creature #${territory.chief_creature_id}`}
                </Text>
              </View>
            )}
          </View>
        )}
      </Card>

      {/* Passive Reward Rate */}
      <Card style={styles.section}>
        <PassiveRateDisplay rate={territory.passive_reward_rate} />
      </Card>

      {/* Familiarity Rankings */}
      {familiarityRankings.length > 0 && (
        <Card style={styles.section}>
          <FamiliarityRanking rankings={familiarityRankings} />
        </Card>
      )}

      {/* Location warning banner */}
      {!hasLocation && (
        <View style={styles.locationWarning}>
          <MaterialIcons name="gps-off" size={16} color={GAME_COLORS.warning} />
          <Text style={styles.locationWarningText}>
            Enable location to use this feature
          </Text>
        </View>
      )}

      {/* Action Buttons */}
      <View style={styles.actionSection}>
        {/* Unclaimed: Claim button (disabled if no visit, no creatures, or no location) */}
        {isUnclaimed && (
          <>
            <Button
              title={!hasVisited ? 'Visit this area first' : 'Claim Territory'}
              onPress={() => setIsClaimModalVisible(true)}
              variant="primary"
              disabled={!hasVisited || allCreatures.length === 0 || !hasLocation}
            />
            {!hasVisited && (
              <Text style={styles.visitRequiredText}>
                You must visit this area at least once before claiming it.
              </Text>
            )}
          </>
        )}

        {/* PvP: Challenge button (disabled if no location) */}
        {!isUnclaimed && isPvp && (
          <ChallengeButton
            territoryId={territory.id}
            creatures={creatures}
            onChallengeComplete={handleChallengeComplete}
            disabled={!hasLocation}
          />
        )}

        {/* Cooperative: Contribute button (disabled if no location) */}
        {isCooperative && !isUnclaimed && (
          <Button
            title="Contribute"
            onPress={() => setIsContributeModalVisible(true)}
            variant="primary"
            disabled={availableCreatures.length === 0 || !hasLocation}
          />
        )}

        {/* Personal Zone: Claim Home section */}
        {isPersonal && (
          <Card style={styles.personalZoneCard}>
            <View style={styles.personalZoneHeader}>
              <MaterialIcons name="home" size={22} color={ZONE_COLORS.personal} />
              <Text style={styles.personalZoneTitle}>Personal Zone</Text>
            </View>
            <Text style={styles.personalZoneDescription}>
              Claim this hex as your home base. Multiple players can share the same hex.
            </Text>
            <Button
              title={isClaimingHome ? 'Claiming...' : 'Claim as Home'}
              onPress={handleClaimHome}
              variant="primary"
              disabled={isClaimingHome || !hasLocation}
            />
            {residents.length > 0 && (
              <View style={styles.residentsSection}>
                <View style={styles.residentsHeader}>
                  <MaterialIcons
                    name="people"
                    size={18}
                    color={GAME_COLORS.textSecondary}
                  />
                  <Text style={styles.residentsTitle}>
                    Residents ({residents.length})
                  </Text>
                </View>
                {residents.map((resident) => (
                  <View key={resident.user_id} style={styles.residentRow}>
                    <MaterialIcons
                      name="person"
                      size={16}
                      color={GAME_COLORS.primary}
                    />
                    <Text style={styles.residentName}>{resident.username}</Text>
                  </View>
                ))}
              </View>
            )}
          </Card>
        )}
      </View>

      {/* Claim Creature Selector Modal */}
      <Modal
        visible={isClaimModalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setIsClaimModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                Select Creature to Claim
              </Text>
              <Pressable
                onPress={() => setIsClaimModalVisible(false)}
                style={styles.closeButton}>
                <MaterialIcons
                  name="close"
                  size={24}
                  color={GAME_COLORS.text}
                />
              </Pressable>
            </View>
            {allCreatures.length === 0 ? (
              <Text style={styles.noCreaturesText}>
                No creatures available. Collect creatures from loot boxes first.
              </Text>
            ) : (
              <FlatList
                data={allCreatures}
                keyExtractor={(item: CreatureResponse) => item.id.toString()}
                renderItem={({ item }: { item: CreatureResponse }) => (
                  <Pressable
                    style={styles.creatureRow}
                    disabled={isActionLoading}
                    onPress={() => handleClaim(item.id)}>
                    <View style={styles.creatureInfo}>
                      <Text style={styles.creatureName}>{item.name}</Text>
                      <Text style={styles.creatureStats}>
                        Lv.{item.level} | Power: {item.power}
                      </Text>
                      {item.assigned_territory_id !== null && (
                        <Text style={styles.assignedIndicator}>
                          Assigned to Territory #{item.assigned_territory_id}
                        </Text>
                      )}
                    </View>
                    <MaterialIcons
                      name="chevron-right"
                      size={20}
                      color={GAME_COLORS.textSecondary}
                    />
                  </Pressable>
                )}
                style={styles.creatureList}
              />
            )}
          </View>
        </View>
      </Modal>

      {/* Contribute Creature Selector Modal */}
      <Modal
        visible={isContributeModalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setIsContributeModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                Select Creature to Contribute
              </Text>
              <Pressable
                onPress={() => setIsContributeModalVisible(false)}
                style={styles.closeButton}>
                <MaterialIcons
                  name="close"
                  size={24}
                  color={GAME_COLORS.text}
                />
              </Pressable>
            </View>
            {availableCreatures.length === 0 ? (
              <Text style={styles.noCreaturesText}>
                No available creatures. Unassign a creature first.
              </Text>
            ) : (
              <FlatList
                data={availableCreatures}
                keyExtractor={(item: CreatureResponse) => item.id.toString()}
                renderItem={({ item }: { item: CreatureResponse }) => (
                  <Pressable
                    style={styles.creatureRow}
                    disabled={isActionLoading}
                    onPress={() => handleContribute(item.id)}>
                    <View style={styles.creatureInfo}>
                      <Text style={styles.creatureName}>{item.name}</Text>
                      <Text style={styles.creatureStats}>
                        Lv.{item.level} | Power: {item.power}
                      </Text>
                    </View>
                    <MaterialIcons
                      name="chevron-right"
                      size={20}
                      color={GAME_COLORS.textSecondary}
                    />
                  </Pressable>
                )}
                style={styles.creatureList}
              />
            )}
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: GAME_COLORS.surface,
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    paddingTop: 48,
  },
  backButton: {
    padding: 8,
    marginRight: 12,
  },
  screenTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: GAME_COLORS.text,
  },
  zoneTypeContainer: {
    marginBottom: 16,
    alignItems: 'flex-start',
  },
  zoneTypeBadge: {
    paddingVertical: 4,
    paddingHorizontal: 14,
    borderRadius: 12,
  },
  zoneTypeText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#ffffff',
  },
  section: {
    marginBottom: 12,
  },
  unclaimedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  unclaimedText: {
    fontSize: 14,
    color: GAME_COLORS.textSecondary,
    fontStyle: 'italic',
  },
  ownerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  ownerName: {
    fontSize: 16,
    fontWeight: '600',
    color: GAME_COLORS.text,
  },
  chiefRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
  },
  chiefText: {
    fontSize: 13,
    color: GAME_COLORS.textSecondary,
  },
  actionSection: {
    marginTop: 16,
    gap: 12,
  },
  visitRequiredText: {
    fontSize: 13,
    color: GAME_COLORS.textSecondary,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
    backgroundColor: GAME_COLORS.background,
  },
  errorText: {
    fontSize: 16,
    color: GAME_COLORS.error,
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 20,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: GAME_COLORS.background,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '70%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: GAME_COLORS.text,
  },
  closeButton: {
    padding: 4,
  },
  noCreaturesText: {
    fontSize: 14,
    color: GAME_COLORS.textSecondary,
    textAlign: 'center',
    paddingVertical: 24,
  },
  creatureList: {
    maxHeight: 300,
  },
  creatureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: GAME_COLORS.border,
  },
  creatureInfo: {
    flex: 1,
  },
  creatureName: {
    fontSize: 15,
    fontWeight: '600',
    color: GAME_COLORS.text,
  },
  creatureStats: {
    fontSize: 12,
    color: GAME_COLORS.textSecondary,
    marginTop: 2,
  },
  assignedIndicator: {
    fontSize: 11,
    color: GAME_COLORS.warning,
    fontStyle: 'italic',
    marginTop: 2,
  },
  locationWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: GAME_COLORS.warning + '20',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
  },
  locationWarningText: {
    fontSize: 13,
    color: GAME_COLORS.warning,
    flex: 1,
  },
  personalZoneCard: {
    marginTop: 4,
  },
  personalZoneHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  personalZoneTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: GAME_COLORS.text,
  },
  personalZoneDescription: {
    fontSize: 14,
    color: GAME_COLORS.textSecondary,
    marginBottom: 14,
    lineHeight: 20,
  },
  residentsSection: {
    marginTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: GAME_COLORS.border,
    paddingTop: 14,
  },
  residentsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 10,
  },
  residentsTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: GAME_COLORS.text,
  },
  residentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 6,
    paddingHorizontal: 4,
  },
  residentName: {
    fontSize: 14,
    color: GAME_COLORS.text,
  },
});
