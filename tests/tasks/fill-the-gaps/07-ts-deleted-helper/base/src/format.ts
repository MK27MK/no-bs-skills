export function formatRow(name: string, amount: number): string {
  return `${name.padEnd(20)}${amount.toFixed(2).padStart(10)}`;
}
