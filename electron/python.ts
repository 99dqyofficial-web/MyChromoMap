import { spawn, execSync } from 'child_process'
import { join, dirname } from 'path'
import { app } from 'electron'
import fs from 'fs'

function getPythonDir(): string {
  if (app.isPackaged) {
    return join(process.resourcesPath, 'python')
  }
  return join(__dirname, '../python')
}

function findPython(pythonDir: string): string {
  const candidates = [
    join(pythonDir, 'portable', 'bin', 'python3'),
    join(pythonDir, 'portable', 'bin', 'python3.11'),
    join(pythonDir, 'portable', 'bin', 'python3.12'),
    join(pythonDir, 'portable', 'bin', 'python3.13'),
  ]

  for (const p of candidates) {
    if (fs.existsSync(p)) {
      return p
    }
  }

  const systemCandidates = ['python3.13', 'python3.12', 'python3.11', 'python3']
  for (const cmd of systemCandidates) {
    try {
      execSync(`${cmd} --version`, { stdio: 'ignore' })
      return cmd
    } catch {
      continue
    }
  }

  return 'python3'
}

export async function runPython(params: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const pythonDir = getPythonDir()
    const python = findPython(pythonDir)
    const script = join(pythonDir, 'main.py')

    if (!fs.existsSync(script)) {
      reject(new Error(`Python script not found at: ${script}`))
      return
    }

    const child = spawn(python, [script], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PYTHONPATH: pythonDir,
      },
    })

    let stdout = ''
    let stderr = ''

    child.stdout.on('data', (data) => {
      stdout += data.toString()
    })

    child.stderr.on('data', (data) => {
      stderr += data.toString()
    })

    child.stdin.write(params)
    child.stdin.end()

    child.on('close', (code) => {
      if (code === 0) {
        resolve(stdout.trim())
      } else {
        reject(new Error(stderr || `Python process exited with code ${code}`))
      }
    })

    child.on('error', (err) => {
      reject(new Error(`Failed to start Python: ${err.message}`))
    })
  })
}
