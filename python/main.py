import sys
import json
import base64
import traceback
import io
import tempfile
import os
from io import BytesIO

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from plotter import plot_chromomap, calculate_windowed_density
from synteny import DualSyntenyPlotter, MultipleSpeciesSynteny, MicroSyntenyPlotter


def save_temp_file(content, suffix='.txt'):
    """Save content to a temporary file and return the path"""
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(content)
        return f.name


def handle_synteny_analysis(params):
    """Handle synteny analysis request"""
    synteny_type = params.get('synteny_type', 'dual')
    
    # Get file contents
    gff_content = params.get('gff_content', '')
    collinearity_content = params.get('collinearity_content', '')
    
    # Save to temp files
    gff_file = save_temp_file(gff_content, '.gff')
    collinearity_file = save_temp_file(collinearity_content, '.txt')
    
    try:
        if synteny_type == 'dual':
            # Dual synteny analysis
            plotter = DualSyntenyPlotter()
            plotter.parse_gff(gff_file)
            plotter.parse_collinearity(collinearity_file)
            
            up_chrs = params.get('up_chrs', [])
            down_chrs = params.get('down_chrs', [])
            plotter.set_chromosomes(up_chrs, down_chrs)
            
            settings = params.get('settings', {})
            plotter.min_genes_in_block = settings.get('min_genes_in_block', 30)
            plotter.fig_width = settings.get('fig_width', 15)
            plotter.fig_height = settings.get('fig_height', 6)
            
            fig = plotter.plot()
            
        elif synteny_type == 'multiple':
            # Multiple species synteny analysis
            plotter = MultipleSpeciesSynteny()
            plotter.parse_gff(gff_file)
            plotter.parse_collinearity(collinearity_file)
            
            layout_content = params.get('layout_content', '')
            pairs_content = params.get('pairs_content', '')
            
            if layout_content:
                layout_file = save_temp_file(layout_content, '.txt')
                plotter.parse_chr_layout(layout_file)
                os.unlink(layout_file)
            
            if pairs_content:
                pairs_file = save_temp_file(pairs_content, '.txt')
                plotter.parse_gene_pairs(pairs_file)
                os.unlink(pairs_file)
            
            settings = params.get('settings', {})
            plotter.fig_width = settings.get('fig_width', 15)
            plotter.fig_height = settings.get('fig_height', 10)
            
            fig = plotter.plot()
            
        elif synteny_type == 'micro':
            # Micro synteny analysis
            plotter = MicroSyntenyPlotter()
            plotter.parse_gff(gff_file)
            plotter.parse_collinearity(collinearity_file)
            
            region1 = params.get('region1', {})
            region2 = params.get('region2', {})
            
            if region1 and region2:
                plotter.set_regions(
                    (region1['chr'], region1['start'], region1['end']),
                    (region2['chr'], region2['start'], region2['end'])
                )
            
            # Parse second GFF if provided
            gff2_content = params.get('gff2_content', '')
            if gff2_content:
                gff2_file = save_temp_file(gff2_content, '.gff')
                plotter.parse_second_gff(gff2_file)
                os.unlink(gff2_file)
            
            settings = params.get('settings', {})
            plotter.fig_width = settings.get('fig_width', 14)
            plotter.fig_height = settings.get('fig_height', 8)
            plotter.show_gene_names = settings.get('show_gene_names', True)
            
            fig = plotter.plot()
            
        else:
            raise ValueError(f"Unknown synteny type: {synteny_type}")
        
        # Convert figure to base64
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
        return result
        
    finally:
        # Clean up temp files
        if os.path.exists(gff_file):
            os.unlink(gff_file)
        if os.path.exists(collinearity_file):
            os.unlink(collinearity_file)


def main():
    raw = sys.stdin.read()
    params = json.loads(raw)
    
    # Check if this is a synteny analysis request
    analysis_type = params.get('analysis_type', 'chromomap')
    
    if analysis_type == 'synteny':
        result = handle_synteny_analysis(params)
        print(json.dumps(result))
        sys.stdout.flush()
        return
    
    # Original chromomap analysis
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
        print(json.dumps({'error': str(e), 'traceback': traceback.format_exc()}), file=sys.stderr)
        sys.exit(1)
