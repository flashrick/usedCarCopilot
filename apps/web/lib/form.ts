export function parseIntegerInput(value: string): number | undefined {
  const normalized = value.replace(/[$,\s]/g, "");
  if (!normalized) {
    return undefined;
  }
  if (!/^\d+$/.test(normalized)) {
    return undefined;
  }
  return Number(normalized);
}

export function formattedInteger(value: number): string {
  return value.toLocaleString("en-US");
}
