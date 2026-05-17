import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  openFile: (options: any) => ipcRenderer.invoke('open-file', options),
  saveFile: (defaultPath: string, filters: any[]) => ipcRenderer.invoke('save-file', defaultPath, filters),
  generateChart: (params: any) => ipcRenderer.invoke('generate-chart', params),
  readTextFile: (filePath: string) => ipcRenderer.invoke('read-text-file', filePath),
  writeBinaryFile: (filePath: string, data: number[]) => ipcRenderer.invoke('write-binary-file', filePath, data),
})
