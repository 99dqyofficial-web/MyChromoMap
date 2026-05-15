import sys
import json
import base64
import traceback
import io
from io import BytesIO

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from plotter import plot_chromomap, calculate_windowed_density


def main():
    raw = sys.stdin.read()
    params = json.loads(raw)

    genes_data = params.get('genes', [])
    chr_lens = params.get('chr_lens', {})
    settings = params.get('settings', {})

    if isinstance(genes_data, dict) and genes_data.get('_is_path'):
        path = genes_data['path']
        if path.lower().endswith(('.xlsx', '.xls')):
            df_genes = pd.read_excel(path)
        else:
            df_genes = pd.read_csv(path)
    else:
        df_genes = pd.DataFrame(genes_data)

    if not df_genes.empty and 'Start' in df_genes.columns and 'End' in df_genes.columns:
        df_genes[['Start', 'End']] = df_genes[['Start', 'End']].apply(pd.to_numeric)

    d_map, d_max = {}, 0.0
    if settings.get('use_density_color') and params.get('gff_content'):
        gff_content = params['gff_content']
        d_map, d_max = calculate_windowed_density(
            io.StringIO(gff_content), chr_lens, settings.get('window_size_mb', 1.0) * 1e6)

    d_norm = mcolors.Normalize(0, d_max) if d_max > 0 else None
    cmap_name = settings.get('colormap_name', 'Grayscale_Print')
    try:
        d_cmap = plt.colormaps[cmap_name]
    except KeyError:
        d_cmap = plt.colormaps['Grayscale_Print']

    fig = plot_chromomap(df_genes, chr_lens, d_map, d_norm, d_cmap, settings)

    result = {}
    for fmt, kwargs in [
        ('png', {'format': 'png', 'dpi': 300, 'bbox_inches': 'tight'}),
        ('svg', {'format': 'svg', 'bbox_inches': 'tight'}),
        ('pdf', {'format': 'pdf', 'bbox_inches': 'tight'}),
    ]:
        buf = BytesIO()
        fig.savefig(buf, **kwargs)
        result[fmt] = base64.b64encode(buf.getvalue()).decode()
        buf.close()

    plt.close(fig)
    print(json.dumps(result))
    sys.stdout.flush()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'traceback': traceback.format_exc()}))
        sys.exit(1)
