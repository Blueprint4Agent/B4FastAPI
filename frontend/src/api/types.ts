export type User = {
  id: number;
  email: string;
  name: string;
  is_verified: boolean;
  created_at: string;
};

export type LoginPayload = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  user: User;
};

export type RefreshPayload = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
};
