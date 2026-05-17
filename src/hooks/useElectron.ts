interface ElectronAPI {
  openFile: (options: any) => Promise<string | null>
  saveFile: (defaultPath: string, filters: any[]) => Promise<string | null>
  generateChart: (params: any) => Promise<string>
  readTextFile: (filePath: string) => Promise<string>
  writeBinaryFile: (filePath: string, data: number[]) => Promise<void>
}

declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
}

export function useElectron() {
  return {
    openFile: async (options: any) => {
      return window.electronAPI.openFile(options)
    },
    saveFile: async (defaultPath: string, filters: any[]) => {
      return window.electronAPI.saveFile(defaultPath, filters)
    },
    generateChart: async (params: any) => {
      return window.electronAPI.generateChart(params)
    },
    readText: async (filePath: string) => {
      return window.electronAPI.readTextFile(filePath)
    },
    writeBinary: async (filePath: string, buf: Uint8Array) => {
      return window.electronAPI.writeBinaryFile(filePath, Array.from(buf))
    },
  }
}
