export function bindSearch(input: HTMLInputElement, search: (q: string) => void): void {
  // AI TODO: debounce, 300ms, and skip queries shorter than 2 chars
  input.addEventListener("input", () => {
    search(input.value);
  });
}
