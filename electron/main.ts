import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import { join } from 'path'
import { runPython } from './python'

// Disable hardware acceleration to fix GPU errors on Macs
app.disableHardwareAcceleration()
app.commandLine.appendSwitch('disable-gpu')
app.commandLine.appendSwitch('disable-software-rasterizer')

let mainWindow: BrowserWindow | null = null

function createWindow() {
  console.log('Creating window...')
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    title: 'ChromoMap - 染色体物理图谱',
    show: false,
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  const url = process.env.VITE_DEV_SERVER_URL || `file://${join(__dirname, '../dist/index.html')}`
  console.log('Loading:', url)
  
  mainWindow.loadURL(url).then(() => {
    console.log('Loaded successfully')
    mainWindow!.show()
  }).catch(err => {
    console.error('Failed to load:', err)
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
  
  mainWindow.on('unresponsive', () => {
    console.log('Window became unresponsive')
  })
}

app.whenReady().then(() => {
  console.log('App ready')
  app.setActivationPolicy('regular')
  createWindow()
  app.focus({ steal: true })
}).catch(err => {
  console.error('Failed to start app:', err)
})

app.on('window-all-closed', (e: any) => {
  console.log('All windows closed - preventing quit')
  e.preventDefault()
  if (process.platform !== 'darwin') {
    // Don't quit on macOS
  }
})

app.on('activate', () => {
  console.log('Activate event')
  if (mainWindow === null) {
    createWindow()
  }
})

app.on('will-quit', () => {
  console.log('Will quit')
})

app.on('quit', () => {
  console.log('Quit')
})

ipcMain.handle('open-file', async (_, options) => {
  const result = await dialog.showOpenDialog(mainWindow!, options)
  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0]
  }
  return null
})

ipcMain.handle('save-file', async (_, defaultPath, filters) => {
  const result = await dialog.showSaveDialog(mainWindow!, {
    defaultPath,
    filters,
  })
  if (!result.canceled && result.filePath) {
    return result.filePath
  }
  return null
})

ipcMain.handle('generate-chart', async (_, params) => {
  try {
    const result = await runPython(JSON.stringify(params))
    return result
  } catch (error) {
    throw error
  }
})

ipcMain.handle('read-text-file', async (_, filePath) => {
  const fs = await import('fs/promises')
  return fs.readFile(filePath, 'utf-8')
})

ipcMain.handle('write-binary-file', async (_, filePath, data) => {
  const fs = await import('fs/promises')
  await fs.writeFile(filePath, Buffer.from(data))
})
