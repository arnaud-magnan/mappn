/**
 * Territory service API client functions.
 *
 * Provides typed API calls for all /game/territories/* endpoints:
 * nearby territories, territory detail, claiming, challenging, and
 * contributing to cooperative zones.
 */

import { api } from './api';
import { TerritoryResponse, ChallengeResult, ResidentResponse } from '../types/api';

/**
 * Get territories near a geographic position.
 * Endpoint: GET /game/territories/nearby
 *
 * @param lat - Latitude in decimal degrees.
 * @param lon - Longitude in decimal degrees.
 * @param radius - Search radius in meters.
 */
export const getNearbyTerritories = async (
  lat: number,
  lon: number,
  radius: number = 5000
): Promise<TerritoryResponse[]> => {
  const { data } = await api.get<TerritoryResponse[]>(
    '/game/territories/nearby',
    {
      params: { lat, lon, radius },
    }
  );
  return data;
};

/**
 * Get a single territory's full details.
 * Endpoint: GET /game/territories/:territoryId
 *
 * @param territoryId - The territory's primary key.
 */
export const getTerritoryDetail = async (
  territoryId: number
): Promise<TerritoryResponse> => {
  const { data } = await api.get<TerritoryResponse>(
    `/game/territories/${territoryId}`
  );
  return data;
};

/**
 * Claim an unclaimed territory by assigning a creature as chief.
 * Endpoint: POST /game/territories/:territoryId/claim
 *
 * @param territoryId - The territory's primary key.
 * @param creatureId - The creature to assign as chief.
 */
export const claimTerritory = async (
  territoryId: number,
  creatureId: number
): Promise<TerritoryResponse> => {
  const { data } = await api.post<TerritoryResponse>(
    `/game/territories/${territoryId}/claim`,
    { creature_id: creatureId }
  );
  return data;
};

/**
 * Challenge the current chief of a PvP territory.
 * Endpoint: POST /game/territories/:territoryId/challenge
 *
 * @param territoryId - The territory's primary key.
 * @param attackerCreatureId - The creature to use as attacker.
 */
export const challengeTerritory = async (
  territoryId: number,
  attackerCreatureId: number
): Promise<ChallengeResult> => {
  const { data } = await api.post<ChallengeResult>(
    `/game/territories/${territoryId}/challenge`,
    { attacker_creature_id: attackerCreatureId }
  );
  return data;
};

/**
 * Contribute a creature to a cooperative territory.
 * Endpoint: POST /game/territories/:territoryId/contribute
 *
 * @param territoryId - The territory's primary key.
 * @param creatureId - The creature to contribute.
 */
export const contributeToTerritory = async (
  territoryId: number,
  creatureId: number
): Promise<TerritoryResponse> => {
  const { data } = await api.post<TerritoryResponse>(
    `/game/territories/${territoryId}/contribute`,
    { creature_id: creatureId }
  );
  return data;
};

/**
 * Claim a personal zone territory as the player's home base.
 * Endpoint: POST /game/territories/:territoryId/claim-home
 *
 * @param territoryId - The territory's primary key.
 */
export const claimHome = async (
  territoryId: number
): Promise<TerritoryResponse> => {
  const { data } = await api.post<TerritoryResponse>(
    `/game/territories/${territoryId}/claim-home`
  );
  return data;
};

/**
 * Get the list of residents who have claimed a personal zone as home.
 * Endpoint: GET /game/territories/:territoryId/residents
 *
 * @param territoryId - The territory's primary key.
 */
export const getResidents = async (
  territoryId: number
): Promise<ResidentResponse[]> => {
  const { data } = await api.get<ResidentResponse[]>(
    `/game/territories/${territoryId}/residents`
  );
  return data;
};
