// ─── Auth ────────────────────────────────────────────────────────────────────

export type UserRole = "doctor" | "patient" | "admin";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatarUrl?: string;
  hospital?: string;
  specialization?: string;
  createdAt: string;
}

// ─── Patient / Case ──────────────────────────────────────────────────────────

export type CancerSubtype =
  | "Luminal A"
  | "Luminal B"
  | "HER2-Enriched"
  | "TNBC"
  | "Unknown";

export type CaseStatus =
  | "Under Analysis"
  | "Treatment Ongoing"
  | "Pending Review"
  | "Completed"
  | "Draft";

export type TumourStage = "I" | "II" | "III" | "IV";
export type TumourGrade = 1 | 2 | 3;
export type BiomarkerStatus = "Positive" | "Negative" | "Unknown";

export interface Biomarkers {
  er: BiomarkerStatus;
  pr: BiomarkerStatus;
  her2: BiomarkerStatus;
  ki67?: number; // percentage
  pdl1: BiomarkerStatus;
  brca1: BiomarkerStatus;
  brca2: BiomarkerStatus;
  pik3ca: BiomarkerStatus;
  cyclinD1: BiomarkerStatus;
  tp53: BiomarkerStatus;
  top2a: BiomarkerStatus;
  bcl2: BiomarkerStatus;
  tils?: number; // percentage
  oncotypeDX?: number; // 0-100
  mammaPrint?: "High Risk" | "Low Risk" | "Not Done";
  pam50?: string;
}

export interface HealthProfile {
  lvef?: number; // percentage
  comorbidities: string[];
  medications: string[];
  allergies: string[];
  menopausalStatus?: "Pre" | "Post" | "Peri" | "Unknown";
  performanceScore?: number; // ECOG 0-4
}

export interface TumourInfo {
  stage: TumourStage;
  grade: TumourGrade;
  sizeInCm: number;
  lymphNodesPositive: boolean;
  lymphNodeCount?: number;
  location?: string;
  histologyType?: string;
}

export interface ClinicalCase {
  id: string;
  patientName: string;
  patientAge: number;
  patientSex: "Male" | "Female" | "Other";
  patientContact?: string;
  patientPhotoUrl?: string;
  doctorNotes?: string;
  tumour: TumourInfo;
  biomarkers: Biomarkers;
  healthProfile: HealthProfile;
  subtype: CancerSubtype;
  status: CaseStatus;
  createdAt: string;
  updatedAt: string;
  doctorId: string;
  recommendations?: TreatmentRecommendation[];
  safetyAlerts?: SafetyAlert[];
  versions?: CaseVersion[];
}

// ─── Treatment ───────────────────────────────────────────────────────────────

export type GuidelineSource = "NCCN" | "ISMPO" | "St.Gallen" | "ESMO" | "ASCO";

export interface RuleNode {
  id: string;
  label: string;
  value: string;
  conclusion: string;
}

export interface TreatmentRecommendation {
  id: string;
  name: string;
  description: string;
  confidenceScore: number; // 0-100
  guidelineSource: GuidelineSource;
  ruleTrace: RuleNode[];
  duration?: string;
  sideEffectSeverity?: number; // 1-5
  suitabilityPercent?: number;
  isTopRecommendation?: boolean;
}

export interface SafetyAlert {
  id: string;
  severity: "Critical" | "High" | "Medium" | "Low";
  triggerSource: string;
  affectedTreatment: string;
  recommendedAction: string;
  description: string;
}

// ─── Version History ─────────────────────────────────────────────────────────

export interface CaseVersion {
  id: string;
  version: number;
  createdAt: string;
  doctorName: string;
  changeSummary: string;
  snapshot: Partial<ClinicalCase>;
}

// ─── Analytics ───────────────────────────────────────────────────────────────

export interface AnalyticsData {
  subtypeDistribution: Record<CancerSubtype, number>;
  casesByStage: Record<TumourStage, number>;
  biomarkerPositivity: Record<string, number>;
  monthlyVolume: { month: string; cases: number }[];
  treatmentFrequency: Record<string, number>;
  alertFrequency: { type: string; count: number }[];
}

// ─── Notifications ───────────────────────────────────────────────────────────

export type NotificationType = "case_update" | "analysis" | "alert" | "second_opinion";

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  caseId?: string;
  isRead: boolean;
  createdAt: string;
}
