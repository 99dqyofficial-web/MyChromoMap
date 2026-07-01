"""
Micro Synteny Plotter
Converted from TBtools-II MicroSyntenicAdvance.java
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import matplotlib.lines as mlines
import numpy as np
from typing import List, Dict, Tuple, Optional
from .synteny_plotter import SyntenyPlotter, GeneInfo, CollinearityBlock


class MicroSyntenyPlotter(SyntenyPlotter):
    """Micro synteny plotter for detailed gene structure comparison"""
    
    def __init__(self):
        super().__init__()
        self.region1: Optional[Tuple[str, int, int]] = None
        self.region2: Optional[Tuple[str, int, int]] = None
        self.gff_file2: Optional[str] = None
        self.gene_info2: Dict[str, GeneInfo] = {}
        self.highlight_region1: Optional[Tuple[int, int]] = None
        self.highlight_region2: Optional[Tuple[int, int]] = None
        self.fig_width: int = 14
        self.fig_height: int = 8
        self.show_gene_names: bool = True
        self.gene_color_plus: str = '#4E79A7'
        self.gene_color_minus: str = '#F28E2B'
        self.link_color_plus: str = '#FF6666'
        self.link_color_minus: str = '#6666FF'
        
    def set_regions(self, region1: Tuple[str, int, int], region2: Tuple[str, int, int]):
        """Set regions to compare
        Args:
            region1: (chr_name, start, end) for first region
            region2: (chr_name, start, end) for second region
        """
        self.region1 = region1
        self.region2 = region2
    
    def parse_second_gff(self, gff_file: str):
        """Parse second GFF file for comparison"""
        self.gene_info2 = {}
        with open(gff_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 4:
                    gene = GeneInfo(
                        chr=parts[0],
                        name=parts[1],
                        start=int(parts[2]),
                        end=int(parts[3])
                    )
                    if len(parts) > 4:
                        gene.strand = parts[4] == '+'
                    self.gene_info2[gene.name] = gene
    
    def set_highlight_regions(self, region1: Tuple[int, int] = None, 
                               region2: Tuple[int, int] = None):
        """Set highlight regions"""
        self.highlight_region1 = region1
        self.highlight_region2 = region2
    
    def plot(self, output_file: str = None, dpi: int = 300) -> plt.Figure:
        """Generate micro synteny plot"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(self.fig_width, self.fig_height),
                                        gridspec_kw={'height_ratios': [1, 1]})
        
        # Draw region 1
        if self.region1:
            self._draw_region_genes(ax1, self.region1, self.gene_info, 
                                   'Region 1', self.highlight_region1)
        
        # Draw region 2
        if self.region2:
            gene_info = self.gene_info2 if self.gene_info2 else self.gene_info
            self._draw_region_genes(ax2, self.region2, gene_info, 
                                   'Region 2', self.highlight_region2)
        
        # Draw collinearity links
        self._draw_micro_links(ax1, ax2)
        
        # Add legend
        self._add_legend(fig)
        
        plt.tight_layout()
        
        if output_file:
            fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
        
        return fig
    
    def _draw_region_genes(self, ax, region: Tuple[str, int, int], 
                           gene_info: Dict[str, GeneInfo], title: str,
                           highlight: Tuple[int, int] = None):
        """Draw genes in a region"""
        chr_name, start, end = region
        
        # Filter genes in region
        genes = []
        for gene in gene_info.values():
            if gene.chr == chr_name:
                # Check overlap
                if gene.end >= start and gene.start <= end:
                    genes.append(gene)
        
        genes.sort(key=lambda g: g.start)
        
        if not genes:
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_title(f'{title} - {chr_name}:{start}-{end}', fontsize=10, fontweight='bold')
            ax.axis('off')
            return
        
        # Draw highlight region if specified
        if highlight:
            hl_start, hl_end = highlight
            x_start = max(0, (hl_start - start) / (end - start))
            x_end = min(1, (hl_end - start) / (end - start))
            rect = patches.Rectangle(
                (x_start, 0), x_end - x_start, 1,
                facecolor='#FFFF00', alpha=0.2, edgecolor='none'
            )
            ax.add_patch(rect)
        
        # Draw genes
        for i, gene in enumerate(genes):
            # Calculate position
            x_start = max(0, (gene.start - start) / (end - start))
            x_end = min(1, (gene.end - start) / (end - start))
            
            # Determine color based on strand
            color = self.gene_color_plus if gene.strand else self.gene_color_minus
            
            # Draw gene body
            y_center = 0.5
            gene_height = 0.15
            
            rect = patches.FancyBboxPatch(
                (x_start, y_center - gene_height/2), 
                x_end - x_start, gene_height,
                boxstyle="round,pad=0.005",
                facecolor=color,
                edgecolor='black',
                linewidth=0.8,
                alpha=0.8
            )
            ax.add_patch(rect)
            
            # Draw arrow indicating strand
            if gene.strand:
                # Right arrow
                arrow_x = x_end
                ax.annotate('', xy=(arrow_x, y_center), 
                           xytext=(arrow_x - 0.01, y_center),
                           arrowprops=dict(arrowstyle='->', color='black', lw=1))
            else:
                # Left arrow
                arrow_x = x_start
                ax.annotate('', xy=(arrow_x, y_center), 
                           xytext=(arrow_x + 0.01, y_center),
                           arrowprops=dict(arrowstyle='->', color='black', lw=1))
            
            # Add gene name
            if self.show_gene_names:
                ax.text((x_start + x_end) / 2, y_center + gene_height/2 + 0.02, 
                       gene.name,
                       ha='center', va='bottom', fontsize=6, rotation=45)
        
        # Set axis
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(0, 1)
        ax.set_title(f'{title} - {chr_name}:{start}-{end}', fontsize=10, fontweight='bold')
        ax.axis('off')
    
    def _draw_micro_links(self, ax1, ax2):
        """Draw micro synteny links between regions"""
        if not self.region1 or not self.region2:
            return
        
        chr1, start1, end1 = self.region1
        chr2, start2, end2 = self.region2
        
        for block in self.collinearity_blocks:
            for pair in block.gene_pairs:
                from_gene = self.gene_info.get(pair.from_gene)
                to_gene = self.gene_info.get(pair.to_gene) or self.gene_info2.get(pair.to_gene)
                
                if not from_gene or not to_gene:
                    continue
                
                # Check if genes are in regions
                if from_gene.chr != chr1 or to_gene.chr != chr2:
                    continue
                
                if not (from_gene.end >= start1 and from_gene.start <= end1):
                    continue
                if not (to_gene.end >= start2 and to_gene.start <= end2):
                    continue
                
                # Calculate positions
                from_x = (from_gene.start - start1) / (end1 - start1)
                to_x = (to_gene.start - start2) / (end2 - start2)
                
                # Determine color based on strand
                color = self.link_color_plus if block.strand else self.link_color_minus
                
                # Draw link lines
                # Line from gene 1 down
                ax1.plot([from_x, from_x], [0.35, 0.25], color=color, lw=1, alpha=0.6)
                
                # Line from gene 2 up
                ax2.plot([to_x, to_x], [0.75, 0.65], color=color, lw=1, alpha=0.6)
                
                # Draw connecting line between subplots
                # Using a simple approach with figure coordinates
                fig = ax1.figure
                
                # Transform to figure coordinates
                from_pos = ax1.transData.transform((from_x, 0.25))
                to_pos = ax2.transData.transform((to_x, 0.75))
                
                from_fig = fig.transFigure.inverted().transform(from_pos)
                to_fig = fig.transFigure.inverted().transform(to_pos)
                
                line = mlines.Line2D(
                    [from_fig[0], to_fig[0]], 
                    [from_fig[1], to_fig[1]],
                    transform=fig.transFigure,
                    color=color, lw=0.8, alpha=0.4
                )
                fig.lines.append(line)
    
    def _add_legend(self, fig):
        """Add legend to the plot"""
        # Create custom legend handles
        plus_gene = patches.Patch(color=self.gene_color_plus, label='Plus strand gene')
        minus_gene = patches.Patch(color=self.gene_color_minus, label='Minus strand gene')
        plus_link = mlines.Line2D([], [], color=self.link_color_plus, 
                                  label='Plus strand collinearity')
        minus_link = mlines.Line2D([], [], color=self.link_color_minus, 
                                   label='Minus strand collinearity')
        
        fig.legend(handles=[plus_gene, minus_gene, plus_link, minus_link],
                  loc='lower center', ncol=4, fontsize=8,
                  bbox_to_anchor=(0.5, 0.02))
