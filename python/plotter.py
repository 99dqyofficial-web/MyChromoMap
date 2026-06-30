import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
import math
import os
import re

_FONTS_REGISTERED = False

def _register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    _FONTS_REGISTERED = True

    base = os.path.join(os.path.dirname(__file__), 'fonts')
    candidates = [
        'NotoSerifCJKsc-Regular.otf',
        'NotoSansCJKsc-Regular.otf',
    ]
    for name in candidates:
        p = os.path.join(base, name)
        if os.path.exists(p):
            fm.fontManager.addfont(p)

    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Noto Serif CJK SC', 'DejaVu Serif']
    plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'DejaVu Sans']
    plt.rcParams['mathtext.fontset'] = 'stix'
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['svg.fonttype'] = 'none'


_register_fonts()


def register_custom_colormaps():
    mako_cmap = mcolors.LinearSegmentedColormap.from_list(
        "Mako", ['#e3f7e3', '#BAE6E1', '#91D5DE'])
    gray_cmap = mcolors.LinearSegmentedColormap.from_list(
        "Grayscale_Print", ['#F8F8F8', '#969696', '#000000'])
    blues_cmap = mcolors.LinearSegmentedColormap.from_list(
        "Blues", ['#08306b', '#2171b5', '#6baed6', '#c6dbef'])
    
    # 使用 matplotlib 内置色系
    builtin_cmaps = [
        "YlOrRd", "Oranges", "Greens", "Purples", 
        "cividis", "turbo", "hot", "YlGnBu"
    ]
    
    for name in builtin_cmaps:
        if name not in plt.colormaps:
            plt.colormaps.register(cmap=plt.colormaps[name], name=name)
    
    # 注册自定义色系
    for name, cmap in [("Mako", mako_cmap), ("Grayscale_Print", gray_cmap), ("Blues", blues_cmap)]:
        if name not in plt.colormaps:
            plt.colormaps.register(cmap=cmap, name=name)


register_custom_colormaps()


def _parse_chr_num(name):
    """Extract chromosome number from various naming conventions.
    Handles: Chr01, Chr1, glyma.Wm82.gnm6.Gm01, Gm01, 1, etc."""
    m = re.search(r'(?:Chr|Gm|chr|gnm\d+\.)?0*(\d+)$', name)
    return int(m.group(1)) if m else None


def _build_seqid_map(gff_seqids, chr_keys):
    """Build a mapping from chr_keys -> best-matching GFF seqid.
    Tries direct match first, then numeric match."""
    direct = set(chr_keys) & set(gff_seqids)
    if direct:
        return {k: k for k in direct}

    mapping = {}
    chr_nums = {k: _parse_chr_num(k) for k in chr_keys}
    gff_nums = {s: _parse_chr_num(s) for s in gff_seqids}
    for chr_name, cn in chr_nums.items():
        if cn is None:
            continue
        for seqid, sn in gff_nums.items():
            if sn == cn:
                mapping[chr_name] = seqid
                break
    return mapping


def calculate_windowed_density(gff_buffer, len_dict_bp, window_size_bp):
    gff_cols = ['seqid', 'source', 'type', 'start', 'end',
                'score', 'strand', 'phase', 'attributes']
    try:
        df_gff = pd.read_csv(gff_buffer, sep='\t', comment='#',
                              header=None, names=gff_cols,
                              dtype={'seqid': str}, on_bad_lines='skip')
        df_genes = df_gff[df_gff['type'] == 'gene'].copy()
        if df_genes.empty:
            return {}, 0.0
        df_genes['midpoint'] = (df_genes['start'] + df_genes['end']) / 2

        gff_seqids = set(df_genes['seqid'].unique())
        seqid_map = _build_seqid_map(gff_seqids, len_dict_bp.keys())

        density_profile_map = {}
        global_max_density = 0.0
        for chr_name, chr_len in len_dict_bp.items():
            seqid = seqid_map.get(chr_name)
            if seqid is None:
                continue
            chr_sub_df = df_genes[df_genes['seqid'] == seqid]
            bin_edges = np.arange(0, chr_len + window_size_bp, window_size_bp)
            if bin_edges[-1] < chr_len:
                bin_edges = np.append(bin_edges, chr_len)
            binned_data = pd.cut(chr_sub_df['midpoint'], bins=bin_edges,
                                 include_lowest=True)
            counts_series = binned_data.value_counts(sort=False)
            density_values = counts_series.values / (window_size_bp / 1_000_000)
            density_profile_map[chr_name] = density_values
            if len(density_values) > 0:
                global_max_density = max(global_max_density, density_values.max())
        return density_profile_map, global_max_density
    except Exception as e:
        return {}, 0.0


def avoid_collisions(positions, min_spacing):
    n = len(positions)
    if n <= 1:
        return positions
    new_pos = np.array(positions, dtype=float)
    order = np.argsort(new_pos)
    sorted_p = new_pos[order]
    for _ in range(100):
        diffs = np.diff(sorted_p)
        overlaps = np.where(diffs < min_spacing)[0]
        if len(overlaps) == 0:
            break
        for i in overlaps:
            push = (min_spacing - diffs[i]) / 2 + 1e-5
            sorted_p[i] -= push
            sorted_p[i + 1] += push
    final_p = np.zeros_like(new_pos)
    final_p[order] = sorted_p
    return final_p.tolist()


def plot_chromomap(genes, l_dict, d_map, d_norm, d_cmap, settings):
    chrs_per_row = settings.get('chrs_per_row', 10)
    fig_width = settings.get('fig_width', 15.0)
    row_height = settings.get('row_height', 8.0)
    ruler_offset = settings.get('ruler_offset', 0.8)
    major_tick_int = settings.get('major_tick_int', 10)
    tick_line_len = settings.get('tick_line_len', 0.2)
    show_minor = settings.get('show_minor', True)
    use_density_color = settings.get('use_density_color', False)
    window_size_mb = settings.get('window_size_mb', 1.0)
    chr_width = settings.get('chr_width', 0.4)
    label_spacing = settings.get('label_spacing', 1.2)
    font_size = settings.get('font_size', 10)
    label_color = settings.get('label_color', '#000000')
    chr_fill_color = settings.get('chr_fill_color', '')

    sorted_chrs = sorted(l_dict.keys())
    total_chrs = len(sorted_chrs)
    num_rows = math.ceil(total_chrs / chrs_per_row)
    max_mb = max(l_dict.values()) / 1e6

    fig, axes = plt.subplots(num_rows, 1,
                              figsize=(fig_width, row_height * num_rows))
    if num_rows == 1:
        axes = [axes]

    for r in range(num_rows):
        ax = axes[r]
        row_chrs = sorted_chrs[r * chrs_per_row: (r + 1) * chrs_per_row]
        ax.set_xlim(-ruler_offset - 0.5, chrs_per_row * 1.5)
        ax.set_ylim(max_mb * 1.05, -max_mb * 0.05)
        ax.axis('off')

        rx = -ruler_offset
        ax.plot([rx, rx], [0, max_mb], color='black', lw=1.2)
        for t in range(0, int(max_mb) + 1, major_tick_int):
            ax.plot([rx - tick_line_len, rx], [t, t], color='black', lw=1)
            ax.text(rx - tick_line_len - 0.1, t, str(t),
                    ha='right', va='center', fontsize=font_size)
        if show_minor:
            for t in range(0, int(max_mb) + 1, 5):
                if t % major_tick_int != 0:
                    ax.plot([rx - tick_line_len / 2, rx], [t, t],
                            color='black', lw=0.7)
        ax.text(rx, -2, "Mb", ha='center',
                fontweight='bold', fontsize=font_size)

        for i, name in enumerate(row_chrs):
            x = i * 1.2
            c_len_mb = l_dict[name] / 1e6

            if use_density_color and d_norm and name in d_map:
                dens = d_map[name]
                for idx, v in enumerate(dens):
                    sy = idx * window_size_mb
                    bh = min(window_size_mb, c_len_mb - sy)
                    if bh > 0:
                        ax.add_patch(patches.Rectangle(
                            (x - chr_width / 2, sy), chr_width, bh,
                            facecolor=d_cmap(d_norm(v)), lw=0, zorder=0))

            ax.add_patch(patches.FancyBboxPatch(
                (x - chr_width / 2, 0), chr_width, c_len_mb,
                boxstyle=f"round,pad=0,rounding_size={chr_width / 2}",
                ec='black', fc=chr_fill_color if chr_fill_color else 'none', lw=1.2, zorder=1))
            ax.text(x, -2, name, ha='center',
                    fontweight='bold', fontsize=font_size + 1)

            c_gs = genes[genes['Chr'] == name].copy()
            if not c_gs.empty:
                c_gs['y'] = c_gs['Start'] / 1e6
                c_gs['ly'] = avoid_collisions(c_gs['y'].tolist(), label_spacing)
                for _, row in c_gs.iterrows():
                    color = row.get('Color', '')
                    if not color or pd.isna(color):
                        color = "#FF0000"
                    ax.plot([x - chr_width / 2, x + chr_width / 2],
                            [row['y'], row['y']], color=color, lw=2, zorder=2)
                    ax.plot([x + chr_width / 2, x + chr_width / 2 + 0.1],
                            [row['y'], row['ly']], color='black', lw=0.5)
                    ax.text(x + chr_width / 2 + 0.12, row['ly'], row['Gene'],
                            va='center', fontsize=font_size,
                            color=label_color, style='italic')

    # Add colorbar for density legend
    if use_density_color and d_norm:
        # Create a ScalarMappable for the colorbar
        sm = plt.cm.ScalarMappable(cmap=d_cmap, norm=d_norm)
        sm.set_array([])
        
        # Add colorbar to the right of the last axes
        cbar = fig.colorbar(sm, ax=axes[-1], orientation='vertical', 
                           fraction=0.02, pad=0.04, shrink=0.8)
        cbar.set_label('Gene Density (genes/Mb)', fontsize=font_size, 
                      fontweight='bold')
        cbar.ax.tick_params(labelsize=font_size - 1)
        
        # Add a small title above the colorbar
        cbar.ax.set_title('Density', fontsize=font_size, fontweight='bold', pad=10)

    plt.tight_layout()
    return fig
