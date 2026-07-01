"""
Multiple Species Synteny Plotter
Converted from TBtools-II MultipleSpeciesSyteny.java
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np
from typing import List, Dict, Tuple, Optional
from .synteny_plotter import SyntenyPlotter, GeneInfo, CollinearityBlock


class MultipleSpeciesSynteny(SyntenyPlotter):
    """Multiple species synteny plotter"""
    
    def __init__(self):
        super().__init__()
        self.chr_layout: Dict[str, List[str]] = {}
        self.genome_colors: Dict[str, str] = {}
        self.gene_pairs: List[Tuple[str, str, str]] = []  # (from, to, color)
        self.highlight_regions: List[Tuple[str, int, int, str]] = []
        self.highlight_genes: Dict[str, str] = {}
        self.fig_width: int = 15
        self.fig_height: int = 10
        self.show_legend: bool = True
        
    def parse_chr_layout(self, layout_file: str):
        """Parse chromosome layout file
        Format: GenomeName: Chr1 Chr2 Chr3
        or: GenomeName: R,G,B: Chr1 Chr2 Chr3
        """
        self.chr_layout = {}
        self.genome_colors = {}
        
        with open(layout_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split(':')
                if len(parts) == 2:
                    genome_name = parts[0].strip()
                    chrs = parts[1].strip().split()
                    self.chr_layout[genome_name] = chrs
                elif len(parts) == 3:
                    genome_name = parts[0].strip()
                    color_rgb = parts[1].strip().split(',')
                    if len(color_rgb) == 3:
                        r, g, b = int(color_rgb[0]), int(color_rgb[1]), int(color_rgb[2])
                        self.genome_colors[genome_name] = f'#{r:02x}{g:02x}{b:02x}'
                    chrs = parts[2].strip().split()
                    self.chr_layout[genome_name] = chrs
    
    def parse_gene_pairs(self, pairs_file: str):
        """Parse gene pairs file
        Format: Gene1 Gene2 [Color]
        """
        self.gene_pairs = []
        with open(pairs_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    color = '#FF0000'
                    if len(parts) > 2:
                        color_str = parts[2]
                        if color_str.startswith('#'):
                            color = color_str
                        else:
                            try:
                                rgb = color_str.split(',')
                                color = f'#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}'
                            except:
                                color = '#FF0000'
                    self.gene_pairs.append((parts[0], parts[1], color))
    
    def parse_highlight_regions(self, regions_file: str):
        """Parse highlight regions file
        Format: Chr Start End [R,G,B]
        """
        self.highlight_regions = []
        with open(regions_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    color = '#FFFF00'
                    if len(parts) > 3:
                        try:
                            rgb = parts[3].split(',')
                            color = f'#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}'
                        except:
                            pass
                    self.highlight_regions.append((
                        parts[0], int(parts[1]), int(parts[2]), color
                    ))
    
    def parse_highlight_genes(self, genes_file: str):
        """Parse highlight genes file
        Format: GeneName [R,G,B]
        """
        self.highlight_genes = {}
        with open(genes_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 1:
                    color = '#0000FF'
                    if len(parts) > 1:
                        try:
                            rgb = parts[1].split(',')
                            color = f'#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}'
                        except:
                            pass
                    self.highlight_genes[parts[0]] = color
    
    def plot(self, output_file: str = None, dpi: int = 300) -> plt.Figure:
        """Generate multiple species synteny plot"""
        num_genomes = len(self.chr_layout)
        
        fig, ax = plt.subplots(figsize=(self.fig_width, self.fig_height))
        
        # Calculate positions for each genome
        genome_positions = {}
        y_step = 0.8 / num_genomes
        
        for i, (genome, chrs) in enumerate(self.chr_layout.items()):
            y_pos = 0.1 + i * y_step
            chr_positions = self._calculate_genome_chr_positions(chrs, y_pos)
            genome_positions[genome] = chr_positions
            
            # Draw chromosomes
            color = self.genome_colors.get(genome, '#999999')
            self._draw_genome_chromosomes(ax, chr_positions, genome, color)
        
        # Draw gene pair links
        self._draw_gene_pair_links(ax, genome_positions)
        
        # Draw highlight regions
        self._draw_highlight_regions(ax, genome_positions)
        
        # Add legend if requested
        if self.show_legend:
            self._add_legend(ax, genome_positions)
        
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        plt.tight_layout()
        
        if output_file:
            fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
        
        return fig
    
    def _calculate_genome_chr_positions(self, chrs: List[str], y_pos: float) -> Dict[str, Dict]:
        """Calculate chromosome positions for a genome"""
        positions = {}
        valid_chrs = [c for c in chrs if any(g.chr == c for g in self.gene_info.values())]
        
        if not valid_chrs:
            return positions
            
        total_length = sum(self.get_chr_length(c) for c in valid_chrs)
        
        current_x = 0.1
        gap = 0.02
        
        for chr_name in valid_chrs:
            chr_len = self.get_chr_length(chr_name)
            width = (chr_len / total_length) * 0.75
            
            positions[chr_name] = {
                'start': current_x,
                'end': current_x + width,
                'y': y_pos,
                'length': chr_len
            }
            current_x += width + gap
        
        return positions
    
    def _draw_genome_chromosomes(self, ax, chr_positions: Dict[str, Dict], 
                                  genome_name: str, color: str):
        """Draw chromosomes for a genome"""
        for chr_name, pos in chr_positions.items():
            start = pos['start']
            end = pos['end']
            y = pos['y']
            
            # Draw chromosome bar
            rect = patches.FancyBboxPatch(
                (start, y - 0.02), end - start, 0.04,
                boxstyle="round,pad=0.003",
                facecolor=color,
                edgecolor='black',
                linewidth=1,
                alpha=0.7
            )
            ax.add_patch(rect)
            
            # Add chromosome label
            ax.text((start + end) / 2, y - 0.04, chr_name,
                   ha='center', va='top', fontsize=7)
        
        # Add genome label
        if chr_positions:
            first_pos = list(chr_positions.values())[0]
            ax.text(0.05, first_pos['y'], genome_name,
                   ha='right', va='center', fontsize=10, fontweight='bold')
    
    def _draw_gene_pair_links(self, ax, genome_positions: Dict[str, Dict[str, Dict]]):
        """Draw gene pair links between genomes"""
        for from_gene_name, to_gene_name, color in self.gene_pairs:
            from_gene = self.gene_info.get(from_gene_name)
            to_gene = self.gene_info.get(to_gene_name)
            
            if not from_gene or not to_gene:
                continue
            
            # Find which genome each chromosome belongs to
            from_genome = None
            to_genome = None
            
            for genome, chrs in self.chr_layout.items():
                if from_gene.chr in chrs:
                    from_genome = genome
                if to_gene.chr in chrs:
                    to_genome = genome
            
            if not from_genome or not to_genome or from_genome == to_genome:
                continue
            
            # Get positions
            from_positions = genome_positions.get(from_genome, {})
            to_positions = genome_positions.get(to_genome, {})
            
            if from_gene.chr not in from_positions or to_gene.chr not in to_positions:
                continue
            
            from_pos = from_positions[from_gene.chr]
            to_pos = to_positions[to_gene.chr]
            
            from_x = from_pos['start'] + (from_gene.start / from_pos['length']) * (from_pos['end'] - from_pos['start'])
            to_x = to_pos['start'] + (to_gene.start / to_pos['length']) * (to_pos['end'] - to_pos['start'])
            
            from_y = from_pos['y'] + 0.02
            to_y = to_pos['y'] - 0.02
            
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
                                     edgecolor=color, alpha=0.3, lw=0.5)
            ax.add_patch(patch)
    
    def _draw_highlight_regions(self, ax, genome_positions: Dict[str, Dict[str, Dict]]):
        """Draw highlight regions"""
        for chr_name, start, end, color in self.highlight_regions:
            # Find which genome this chromosome belongs to
            for genome, chrs in self.chr_layout.items():
                if chr_name in chrs:
                    positions = genome_positions.get(genome, {})
                    if chr_name in positions:
                        pos = positions[chr_name]
                        x_start = pos['start'] + (start / pos['length']) * (pos['end'] - pos['start'])
                        x_end = pos['start'] + (end / pos['length']) * (pos['end'] - pos['start'])
                        
                        rect = patches.Rectangle(
                            (x_start, pos['y'] - 0.03), x_end - x_start, 0.06,
                            facecolor=color, alpha=0.3, edgecolor='none'
                        )
                        ax.add_patch(rect)
                    break
    
    def _add_legend(self, ax, genome_positions: Dict[str, Dict[str, Dict]]):
        """Add legend to the plot"""
        legend_x = 0.95
        legend_y = 0.95
        
        for i, (genome, color) in enumerate(self.genome_colors.items()):
            y = legend_y - i * 0.04
            rect = patches.Rectangle(
                (legend_x - 0.03, y - 0.01), 0.02, 0.02,
                facecolor=color, edgecolor='black', linewidth=0.5
            )
            ax.add_patch(rect)
            ax.text(legend_x, y, genome, va='center', fontsize=8)
