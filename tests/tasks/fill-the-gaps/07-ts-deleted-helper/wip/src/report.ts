import { formatRow } from "./format";

export interface Expense {
  name: string;
  amount: number;
}

export function renderReport(expenses: Expense[]): string {
  // one line per expense, then a TOTAL line
  return expenses.map((e) => formatRow(e.name, e.amount)).join("\n");
}
