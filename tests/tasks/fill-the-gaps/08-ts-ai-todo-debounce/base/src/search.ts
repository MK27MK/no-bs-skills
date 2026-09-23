export function bindSearch(input: HTMLInputElement, search: (q: string) => void): void {
  input.addEventListener("input", () => {
    search(input.value);
  });
}
