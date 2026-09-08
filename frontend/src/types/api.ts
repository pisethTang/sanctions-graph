export interface AgentPayload {
  name: string;
  nationality?: string;
  aliases?: string[];
  addresses?: string[];
  birth_date?: string | null;
}

export interface Agent extends AgentPayload {
  id: number;
  created_at: string;
}

/** Identifiers travel as [id_type, value] pairs; the API never stores them raw. */
export type IdentifierPair = [string, string];

export interface ScreeningCase {
  id: number;
  agent_id: number;
  agent_name: string;
  risk_score: number;
  status: string;
  match_count: number;
  created_at: string;
}

export interface Match {
  id: number;
  entity_id: number;
  entity_name: string;
  entity_type: string;
  source_id: string;
  match_type: string;
  confidence: number;
  explanation: string;
  resolved: boolean;
  resolution: string;
  created_at: string;
}

export interface ScreenResult {
  case: ScreeningCase;
  matches: Match[];
}

export interface CaseDetail {
  id: number;
  agent: Agent;
  risk_score: number;
  status: string;
  matches: Match[];
  network_snapshot: NetworkGraph | null;
  created_at: string;
}

export interface NetworkNode {
  data: { id: string; label: string; type: string; risk_score: number };
}

export interface NetworkEdge {
  data: { source: string; target: string; label: string };
}

export interface NetworkGraph {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}
