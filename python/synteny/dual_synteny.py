"""
Dual Synteny Plotter
Converted from TBtools-II DualSyntenyPlotter.java
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np
from typing import List, Dict, Tuple, Optional
from .synteny_plotter import SyntenyPlotter, GeneInfo, CollinearityBlock


class DualSyntenyPlotter(SyntenyPlotter):
    """Dual synteny plotter for comparing two genomes"""
    
    def __init__(self):
        super().__init__()
        self.up_chrs: List[str] = []
        self.down_chrs: List[str] = []
        self.fig_width: int = 15
        self.fig_height: int = 6
        self.min_genes_in_block: int = 30
        self.link_color: str = '#FF6666'
        self.link_color_minus: str = '#6666FF'
        self.highlight_genes: Dict[str, str] = {}
        self.chr_colors: Dict[str, str] = {}
        
    def parse_ctl_file(self, ctl_file: str):
        """Parse control file for dual synteny layout"""
        with open(ctl_file, 'r') as f:
            lines = f.readlines()
            
        if len(lines) >= 1:
            self.fig_width = int(lines[0].split()[0]) / 100
        if len(lines) >= 2:
            self.fig_height = int(lines[1].split()[0]) / 100
        if len(lines) >= 3:
            self.up_chrs = [c.strip() for c in lines[2].split()[0].split(',')]
        if len(lines) >= 4:
            self.down_chrs = [c.strip() for c in lines[3].split()[0].split(',')]
    
    def set_chromosomes(self, up_chrs: List[str], down_chrs: List[str]):
        """Set chromosomes for upper and lower genomes"""
        self.up_chrs = up_chrs
        self.down_chrs = down_chrs
    
    def set_chr_colors(self, colors: Dict[str, str]):
        """Set chromosome colors"""
        self.chr_colors = colors
    
    def plot(self, output_file: str = None, dpi: int = 300) -> plt.Figure:
        """Generate dual synteny plot"""
        # Calculate chromosome positions
        up_chr_positions = self._calculate_chr_positions(self.up_chrs, y_base=0.65)
        down_chr_positions = self._calculate_chr_positions(self.down_chrs, y_base=0.35)
        
        fig, ax = plt.subplots(figsize=(self.fig_width, self.fig_height))
        
        # Draw chromosomes
        self._draw_chromosomes(ax, up_chr_positions, label='Up')
        self._draw_chromosomes(ax, down_chr_positions, label='Down')
        
        # Draw collinearity links
        self._draw_collinearity_links(ax, up_chr_positions, down_chr_positions)
        
        # Add legend
        self._add_legend(ax)
        
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        plt.tight_layout()
        
        if output_file:
            fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
        
        return fig
    
    def _calculate_chr_positions(self, chrs: List[str], y_base: float) -> Dict[str, Dict]:
        """Calculate chromosome positions (normalized)"""
        positions = {}
        valid_chrs = [c for c in chrs if c in self.gene_info or any(g.chr == c for g in self.gene_info.values())]
        
        if not valid_chrs:
            return positions
            
        total_length = sum(self.get_chr_length(c) for c in valid_chrs)
        
        current_x = 0.05
        gap = 0.02
        
        for chr_name in valid_chrs:
            chr_len = self.get_chr_length(chr_name)
            width = (chr_len / total_length) * 0.85
            
            positions[chr_name] = {
                'start': current_x,
                'end': current_x + width,
                'y': y_base,
                'length': chr_len,
                'color': self.chr_colors.get(chr_name, '#CCCCCC')
            }
            current_x += width + gap
        
        return positions
    
    def _draw_chromosomes(self, ax, chr_positions: Dict[str, Dict], label: str):
        """Draw chromosome bars"""
        for chr_name, pos in chr_positions.items():
            start = pos['start']
            end = pos['end']
            y = pos['y']
            color = pos['color']
            
            # Draw chromosome bar
            rect = patches.FancyBboxPatch(
                (start, y - 0.03), end - start, 0.06,
                boxstyle="round,pad=0.005",
                facecolor=color,
                edgecolor='black',
                linewidth=1.5,
                alpha=0.8
            )
            ax.add_patch(rect)
            
            # Add chromosome label
            ax.text((start + end) / 2, y + 0.06, chr_name,
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    def _draw_collinearity_links(self, ax, up_positions: Dict[str, Dict],
                                  down_positions: Dict[str, Dict]):
        """Draw collinearity links between genes"""
        for block in self.collinearity_blocks:
            if block.num_genes < self.min_genes_in_block:
                continue
            
            # Determine link color based on strand
            color = self.link_color if block.strand else self.link_color_minus
            
            for pair in block.gene_pairs:
                from_gene = self.gene_info.get(pair.from_gene)
                to_gene = self.gene_info.get(pair.to_gene)
                
                if not from_gene or not to_gene:
                    continue
                
                # Check if genes are in displayed chromosomes
                if from_gene.chr not in up_positions or to_gene.chr not in down_positions:
                    continue
                
                # Calculate positions
                up_pos = up_positions[from_gene.chr]
                down_pos = down_positions[to_gene.chr]
                
                from_x = up_pos['start'] + (from_gene.start / up_pos['length']) * (up_pos['end'] - up_pos['start'])
                to_x = down_pos['start'] + (to_gene.start / down_pos['length']) * (down_pos['end'] - down_pos['start'])
                
                from_y = up_pos['y'] - 0.03
                to_y = down_pos['y'] + 0.03
                
                # Draw bezier curve
                verts = [
                    (from_x, from_y),
                    (from_x, (from_y + to_y) / 2),
                    (to_x, (from_y + to_y) / 2),
                    (to_x, to_y)
                ]
                codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
                path = Path(verts, codes)
                
                patch = patches.PathPatch(path, facecolor='none',
                                         edgecolor=color, alpha=0.4, lw=0.8)
                ax.add_patch(patch)
    
    def _add_legend(self, ax):
        """Add legend to the plot"""
        legend_x = 0.9
        legend_y = 0.95
        
        # Plus strand
        ax.plot([legend_x, legend_x + 0.03], [legend_y, legend_y], 
               color=self.link_color, lw=2, alpha=0.6)
        ax.text(legend_x + 0.04, legend_y, 'Plus strand', 
               va='center', fontsize=8)
        
        # Minus strand
        ax.plot([legend_x, legend_x + 0.03], [legend_y - 0.03, legend_y - 0.03], 
               color=self.link_color_minus, lw=2, alpha=0.6)
        ax.text(legend_x + 0.04, legend_y - 0.03, 'Minus strand', 
               va='center', fontsize=8)
