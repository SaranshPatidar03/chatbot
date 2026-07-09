export const queryKeys = {
  health: ["health"] as const,
  me: ["me"] as const,
  documents: ["documents"] as const,
  document: (id: string) => ["documents", id] as const,
  chats: ["chats"] as const,
  chat: (id: string) => ["chats", id] as const,
  chatMessages: (id: string) => ["chats", id, "messages"] as const,
  organizations: ["organizations"] as const,
  organization: (id: string) => ["organizations", id] as const,
  organizationMembers: (id: string) => ["organizations", id, "members"] as const,
  userSettings: ["user-settings"] as const,
  dashboard: ["dashboard"] as const,
};
