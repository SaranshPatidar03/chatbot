export type HealthResponse = {
  status: string;
  app: string;
  version: string;
  phase: number;
  environment: string;
};
