"""
Synteny visualization module for ChromoMap
Converted from TBtools-II Java source code
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
import numpy as np
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import math


@dataclass
class GenePair:
    """Represents a gene pair in collinearity block"""
    from_gene: str
    to_gene: str
    evalue: float = 0.0


@dataclass
class CollinearityBlock:
    """Represents a collinearity block from MCScanX"""
    id: int = 0
    score: float = 0.0
    evalue: float = 0.0
    num_genes: int = 0
    from_chr: str = ""
    to_chr: str = ""
    strand: bool = True  # True for plus, False for minus
    gene_pairs: List[GenePair] = field(default_factory=list)


@dataclass
class GeneInfo:
    """Represents gene information from GFF"""
    chr: str = ""
    name: str = ""
    start: int = 0
    end: int = 0
    strand: bool = True


class SyntenyPlotter:
    """Base class for synteny visualization"""
    
    def __init__(self):
        self.gene_info: Dict[str, GeneInfo] = {}
        self.collinearity_blocks: List[CollinearityBlock] = []
        
    def parse_gff(self, gff_file: str) -> Dict[str, GeneInfo]:
        """Parse simplified GFF file (chr, gene, start, end)"""
        gene_info = {}
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
                    gene_info[gene.name] = gene
        self.gene_info = gene_info
        return gene_info
    
    def parse_collinearity(self, collinearity_file: str) -> List[CollinearityBlock]:
        """Parse MCScanX collinearity file"""
        blocks = []
        current_block = None
        block_pattern = re.compile(
            r'## Alignment (\d+): score=(.*?) e_value=(.*?) N=(\d+) (.*)&(.*) (plus|minus)$'
        )
        
        with open(collinearity_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('## Alignment'):
                    match = block_pattern.match(line)
                    if match:
                        current_block = CollinearityBlock(
                            id=int(match.group(1)),
                            score=float(match.group(2)),
                            evalue=float(match.group(3)),
                            num_genes=int(match.group(4)),
                            from_chr=match.group(5),
                            to_chr=match.group(6),
                            strand=match.group(7) == 'plus'
                        )
                        blocks.append(current_block)
                elif current_block and not line.startswith('#'):
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        pair = GenePair(
                            from_gene=parts[1],
                            to_gene=parts[2],
                            evalue=float(parts[3]) if len(parts) > 3 else 0.0
                        )
                        current_block.gene_pairs.append(pair)
        
        self.collinearity_blocks = blocks
        return blocks
    
    def get_chr_length(self, chr_name: str) -> int:
        """Get chromosome length from gene info"""
        max_pos = 0
        for gene in self.gene_info.values():
            if gene.chr == chr_name:
                max_pos = max(max_pos, gene.end)
        return max_pos
    
    def get_chr_genes(self, chr_name: str) -> List[GeneInfo]:
        """Get all genes on a chromosome"""
        return [g for g in self.gene_info.values() if g.chr == chr_name]


class DualSyntenyPlotter(SyntenyPlotter):
    """Dual synteny plotter (two genomes comparison)"""
    
    def __init__(self):
        super().__init__()
        self.up_chrs: List[str] = []
        self.down_chrs: List[str] = []
        self.fig_width: int = 2500
        self.fig_height: int = 600
        self.min_genes_in_block: int = 30
        self.link_color: str = '#FF0000'
        self.highlight_genes: Dict[str, str] = {}
        
    def parse_ctl_file(self, ctl_file: str):
        """Parse control file for dual synteny"""
        with open(ctl_file, 'r') as f:
            lines = f.readlines()
            
        if len(lines) >= 1:
            self.fig_width = int(lines[0].split()[0])
        if len(lines) >= 2:
            self.fig_height = int(lines[1].split()[0])
        if len(lines) >= 3:
            self.up_chrs = lines[2].split()[0].split(',')
        if len(lines) >= 4:
            self.down_chrs = lines[3].split()[0].split(',')
    
    def plot(self, output_file: str = None) -> plt.Figure:
        """Generate dual synteny plot"""
        # Calculate chromosome positions
        up_chr_positions = self._calculate_chr_positions(self.up_chrs)
        down_chr_positions = self._calculate_chr_positions(self.down_chrs)
        
        fig, ax = plt.subplots(figsize=(self.fig_width/100, self.fig_height/100))
        
        # Draw chromosomes
        self._draw_chromosomes(ax, up_chr_positions, y_pos=0.7, label='Up')
        self._draw_chromosomes(ax, down_chr_positions, y_pos=0.3, label='Down')
        
        # Draw collinearity links
        self._draw_collinearity_links(ax, up_chr_positions, down_chr_positions)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        plt.tight_layout()
        
        if output_file:
            fig.savefig(output_file, dpi=300, bbox_inches='tight')
        
        return fig
    
    def _calculate_chr_positions(self, chrs: List[str]) -> Dict[str, Tuple[float, float]]:
        """Calculate chromosome positions (normalized)"""
        positions = {}
        total_length = sum(self.get_chr_length(c) for c in chrs)
        
        current_x = 0.05  # Start with some padding
        for chr_name in chrs:
            chr_len = self.get_chr_length(chr_name)
            width = (chr_len / total_length) * 0.9  # Use 90% of figure width
            positions[chr_name] = (current_x, current_x + width)
            current_x += width + 0.01  # Small gap between chromosomes
        
        return positions
    
    def _draw_chromosomes(self, ax, chr_positions: Dict[str, Tuple[float, float]], 
                          y_pos: float, label: str):
        """Draw chromosome bars"""
        for chr_name, (start, end) in chr_positions.items():
            # Draw chromosome bar
            rect = patches.FancyBboxPatch(
                (start, y_pos - 0.02), end - start, 0.04,
                boxstyle="round,pad=0.005",
                facecolor='#E0E0E0',
                edgecolor='black',
                linewidth=1
            )
            ax.add_patch(rect)
            
            # Add chromosome label
            ax.text((start + end) / 2, y_pos + 0.05, chr_name,
                   ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    def _draw_collinearity_links(self, ax, up_positions: Dict[str, Tuple[float, float]],
                                  down_positions: Dict[str, Tuple[float, float]]):
        """Draw collinearity links between genes"""
        for block in self.collinearity_blocks:
            if block.num_genes < self.min_genes_in_block:
                continue
                
            for pair in block.gene_pairs:
                from_gene = self.gene_info.get(pair.from_gene)
                to_gene = self.gene_info.get(pair.to_gene)
                
                if not from_gene or not to_gene:
                    continue
                
                # Check if genes are in displayed chromosomes
                if from_gene.chr not in up_positions or to_gene.chr not in down_positions:
                    continue
                
                # Calculate positions
                up_start, up_end = up_positions[from_gene.chr]
                down_start, down_end = down_positions[to_gene.chr]
                
                up_chr_len = self.get_chr_length(from_gene.chr)
                down_chr_len = self.get_chr_length(to_gene.chr)
                
                from_x = up_start + (from_gene.start / up_chr_len) * (up_end - up_start)
                to_x = down_start + (to_gene.start / down_chr_len) * (down_end - down_start)
                
                # Draw curved link
                from_y = 0.68
                to_y = 0.32
                
                # Determine color based on strand
                color = self.link_color if block.strand else '#0000FF'
                
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


class MultipleSpeciesSynteny(SyntenyPlotter):
    """Multiple species synteny plotter"""
    
    def __init__(self):
        super().__init__()
        self.chr_layout: Dict[str, List[str]] = {}
        self.genome_colors: Dict[str, str] = {}
        self.gene_pairs: List[Tuple[str, str, str]] = []  # (from, to, color)
        self.highlight_regions: List[Tuple[str, int, int, str]] = []
        self.fig_width: int = 1200
        self.fig_height: int = 600
        
    def parse_chr_layout(self, layout_file: str):
        """Parse chromosome layout file"""
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
                        self.genome_colors[genome_name] = f'#{int(color_rgb[0]):02x}{int(color_rgb[1]):02x}{int(color_rgb[2]):02x}'
                    chrs = parts[2].strip().split()
                    self.chr_layout[genome_name] = chrs
    
    def parse_gene_pairs(self, pairs_file: str):
        """Parse gene pairs file"""
        self.gene_pairs = []
        with open(pairs_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    color = parts[2] if len(parts) > 2 else '#FF0000'
                    self.gene_pairs.append((parts[0], parts[1], color))
    
    def plot(self, output_file: str = None) -> plt.Figure:
        """Generate multiple species synteny plot"""
        num_genomes = len(self.chr_layout)
        
        fig, ax = plt.subplots(figsize=(self.fig_width/100, self.fig_height/100))
        
        # Calculate positions for each genome
        genome_positions = {}
        y_step = 0.8 / num_genomes
        
        for i, (genome, chrs) in enumerate(self.chr_layout.items()):
            y_pos = 0.1 + i * y_step
            chr_positions = self._calculate_genome_chr_positions(chrs, y_pos)
            genome_positions[genome] = chr_positions
            
            # Draw chromosomes
            color = self.genome_colors.get(genome, '#333333')
            self._draw_genome_chromosomes(ax, chr_positions, y_pos, genome, color)
        
        # Draw gene pair links
        self._draw_gene_pair_links(ax, genome_positions)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        plt.tight_layout()
        
        if output_file:
            fig.savefig(output_file, dpi=300, bbox_inches='tight')
        
        return fig
    
    def _calculate_genome_chr_positions(self, chrs: List[str], y_pos: float) -> Dict[str, Tuple[float, float, float]]:
        """Calculate chromosome positions for a genome"""
        positions = {}
        total_length = sum(self.get_chr_length(c) for c in chrs if c in self.gene_info)
        
        current_x = 0.1
        for chr_name in chrs:
            if chr_name not in self.gene_info:
                continue
            chr_len = self.get_chr_length(chr_name)
            width = (chr_len / total_length) * 0.8
            positions[chr_name] = (current_x, current_x + width, y_pos)
            current_x += width + 0.02
        
        return positions
    
    def _draw_genome_chromosomes(self, ax, chr_positions: Dict[str, Tuple[float, float, float]], 
                                  y_pos: float, genome_name: str, color: str):
        """Draw chromosomes for a genome"""
        for chr_name, (start, end, y) in chr_positions.items():
            rect = patches.FancyBboxPatch(
                (start, y - 0.01), end - start, 0.02,
                boxstyle="round,pad=0.002",
                facecolor=color,
                edgecolor='black',
                linewidth=0.5,
                alpha=0.7
            )
            ax.add_patch(rect)
            
            ax.text((start + end) / 2, y + 0.02, chr_name,
                   ha='center', va='bottom', fontsize=6)
        
        # Add genome label
        if chr_positions:
            first_chr = list(chr_positions.values())[0]
            ax.text(0.05, first_chr[2], genome_name,
                   ha='right', va='center', fontsize=8, fontweight='bold')
    
    def _draw_gene_pair_links(self, ax, genome_positions: Dict):
        """Draw gene pair links"""
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
            
            if not from_genome or not to_genome:
                continue
            
            # Get positions
            from_positions = genome_positions.get(from_genome, {})
            to_positions = genome_positions.get(to_genome, {})
            
            if from_gene.chr not in from_positions or to_gene.chr not in to_positions:
                continue
            
            from_start, from_end, from_y = from_positions[from_gene.chr]
            to_start, to_end, to_y = to_positions[to_gene.chr]
            
            from_chr_len = self.get_chr_length(from_gene.chr)
            to_chr_len = self.get_chr_length(to_gene.chr)
            
            from_x = from_start + (from_gene.start / from_chr_len) * (from_end - from_start)
            to_x = to_start + (to_gene.start / to_chr_len) * (to_end - to_start)
            
            # Draw curved link
            verts = [
                (from_x, from_y),
                (from_x, (from_y + to_y) / 2),
                (to_x, (from_y + to_y) / 2),
                (to_x, to_y)
            ]
            codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
            path = Path(verts, codes)
            
            # Parse color
            try:
                if color.startswith('#'):
                    edge_color = color
                else:
                    rgb = color.split(',')
                    edge_color = f'#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}'
            except:
                edge_color = '#FF0000'
            
            patch = patches.PathPatch(path, facecolor='none',
                                     edgecolor=edge_color, alpha=0.3, lw=0.5)
            ax.add_patch(patch)


class MicroSyntenyPlotter(SyntenyPlotter):
    """Micro synteny plotter (detailed gene structure view)"""
    
    def __init__(self):
        super().__init__()
        self.region1: Tuple[str, int, int] = None  # (chr, start, end)
        self.region2: Tuple[str, int, int] = None
        self.gff_file2: str = None
        self.gene_info2: Dict[str, GeneInfo] = {}
        
    def set_regions(self, region1: Tuple[str, int, int], region2: Tuple[str, int, int]):
        """Set regions to compare"""
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
    
    def plot(self, output_file: str = None) -> plt.Figure:
        """Generate micro synteny plot"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Draw region 1
        if self.region1:
            self._draw_region_genes(ax1, self.region1, self.gene_info, 'Region 1')
        
        # Draw region 2
        if self.region2:
            gene_info = self.gene_info2 if self.gene_info2 else self.gene_info
            self._draw_region_genes(ax2, self.region2, gene_info, 'Region 2')
        
        # Draw collinearity links
        self._draw_micro_links(ax1, ax2)
        
        plt.tight_layout()
        
        if output_file:
            fig.savefig(output_file, dpi=300, bbox_inches='tight')
        
        return fig
    
    def _draw_region_genes(self, ax, region: Tuple[str, int, int], 
                           gene_info: Dict[str, GeneInfo], title: str):
        """Draw genes in a region"""
        chr_name, start, end = region
        
        # Filter genes in region
        genes = []
        for gene in gene_info.values():
            if gene.chr == chr_name and gene.start >= start and gene.end <= end:
                genes.append(gene)
        
        genes.sort(key=lambda g: g.start)
        
        # Draw genes
        for i, gene in enumerate(genes):
            y = 0.5
            x_start = (gene.start - start) / (end - start)
            x_end = (gene.end - start) / (end - start)
            
            color = '#4E79A7' if gene.strand else '#F28E2B'
            
            rect = patches.FancyBboxPatch(
                (x_start, y - 0.1), x_end - x_start, 0.2,
                boxstyle="round,pad=0.01",
                facecolor=color,
                edgecolor='black',
                linewidth=0.5
            )
            ax.add_patch(rect)
            
            # Gene name
            ax.text((x_start + x_end) / 2, y + 0.15, gene.name,
                   ha='center', va='bottom', fontsize=6, rotation=45)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.axis('off')
    
    def _draw_micro_links(self, ax1, ax2):
        """Draw micro synteny links"""
        for block in self.collinearity_blocks:
            for pair in block.gene_pairs:
                from_gene = self.gene_info.get(pair.from_gene)
                to_gene = self.gene_info.get(pair.to_gene) or self.gene_info2.get(pair.to_gene)
                
                if not from_gene or not to_gene:
                    continue
                
                if not self.region1 or not self.region2:
                    continue
                
                # Check if genes are in regions
                chr1, start1, end1 = self.region1
                chr2, start2, end2 = self.region2
                
                if from_gene.chr != chr1 or to_gene.chr != chr2:
                    continue
                
                if not (start1 <= from_gene.start <= end1) or not (start2 <= to_gene.start <= end2):
                    continue
                
                # Calculate positions
                from_x = (from_gene.start - start1) / (end1 - start1)
                to_x = (to_gene.start - start2) / (end2 - start2)
                
                # Draw link
                color = '#FF0000' if block.strand else '#0000FF'
                
                ax1.plot([from_x, from_x], [0.4, 0.3], color=color, lw=0.5, alpha=0.5)
                ax2.plot([to_x, to_x], [0.7, 0.6], color=color, lw=0.5, alpha=0.5)
                
                # Connect with line between subplots
                # This is simplified - in real implementation would use ConnectionPatch
