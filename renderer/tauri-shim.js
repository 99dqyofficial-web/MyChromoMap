// Tauri v2 API shim
// With `withGlobalTauri: true`, window.__TAURI__ is auto-populated.
const T = window.__TAURI__

if (T && T.core) {
  window.TauriAPI = {
    arch: T.os ? T.os.arch : (async () => { try { return await T.core.invoke('plugin:os|arch') } catch { return 'arm64' } }),

    openFile: async (filters) => {
      const result = await T.dialog.open({ multiple: false, filters })
      return result || null
    },

    saveFile: async (defaultPath, filters) => {
      const result = await T.dialog.save({ defaultPath, filters })
      return result || null
    },

    readTextFile: async (path) => {
      return await T.fs.readTextFile(path)
    },

    writeBinaryFile: async (path, contents) => {
      return await T.fs.writeFile(path, contents)
    },

    generateChart: async (params) => {
      return await T.core.invoke('generate_chart', { params: JSON.stringify(params) })
    }
  }
} else {
  // Fallback: direct invoke
  const invoke = window.__TAURI_INVOKE__
  window.TauriAPI = {
    arch: async () => { try { return await invoke('plugin:os|arch') } catch { return 'arm64' } },
    openFile: async (filters) => { const r = await invoke('plugin:dialog|open', { options: { multiple: false, filters } }); return r || null },
    saveFile: async (dp, filters) => { const r = await invoke('plugin:dialog|save', { options: { defaultPath: dp, filters } }); return r || null },
    readTextFile: async (path) => await invoke('plugin:fs|read_text_file', { path }),
    writeBinaryFile: async (path, contents) => await invoke('plugin:fs|write_file', contents, { headers: { path: encodeURIComponent(path), options: '{}' } }),
    generateChart: async (params) => await invoke('generate_chart', { params: JSON.stringify(params) })
  }
}
