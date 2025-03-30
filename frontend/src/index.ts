// Main entry point for Plomp frontend code

export class Plomp {
  constructor() {
    console.log('Plomp frontend initialized');
  }

  public init(): void {
    console.log('Plomp ready');
  }
}

// Auto-initialize if window exists (browser environment)
if (typeof window !== 'undefined') {
  (window as any).Plomp = new Plomp();
}
