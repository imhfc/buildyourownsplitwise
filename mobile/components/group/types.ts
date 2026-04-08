export interface Suggestion {
  from_user_id: string;
  from_user_name: string;
  to_user_id: string;
  to_user_name: string;
  amount: string;
  currency: string;
}

export interface CurrencyGroupSuggestions {
  currency: string;
  suggestions: Suggestion[];
}

export interface PendingSettlement {
  id: string;
  from_user: string;
  from_user_name: string;
  to_user: string;
  to_user_name: string;
  amount: number;
  currency: string;
  status: string;
  settled_at: string;
}

export interface Member {
  user: { id: string; display_name: string; email: string };
  role: string;
  joined_at: string;
}
