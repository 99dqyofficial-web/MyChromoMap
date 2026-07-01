"""
Test script for synteny visualization module
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from synteny import DualSyntenyPlotter, MultipleSpeciesSynteny, MicroSyntenyPlotter

def create_test_data():
    """Create test data files"""
    # Create test GFF file
    gff_content = """Chr01	Gene1	1000	2000	+
Chr01	Gene2	3000	4000	-
Chr01	Gene3	5000	6000	+
Chr01	Gene4	7000	8000	+
Chr01	Gene5	9000	10000	-
Chr02	Gene6	1000	2000	+
Chr02	Gene7	3000	4000	+
Chr02	Gene8	5000	6000	-
Chr02	Gene9	7000	8000	+
Chr02	Gene10	9000	10000	+
Chr03	Gene11	1000	2000	+
Chr03	Gene12	3000	4000	-
Chr03	Gene13	5000	6000	+
Chr03	Gene14	7000	8000	+
Chr03	Gene15	9000	10000	-
Chr04	Gene16	1000	2000	+
Chr04	Gene17	3000	4000	+
Chr04	Gene18	5000	6000	-
Chr04	Gene19	7000	8000	+
Chr04	Gene20	9000	10000	+
"""
    
    # Create test collinearity file
    collinearity_content = """## Alignment 1: score=1000 e_value=1e-50 N=5 Chr01&Chr02 plus
0	Gene1	Gene6	1e-50
1	Gene2	Gene7	1e-45
2	Gene3	Gene8	1e-40
3	Gene4	Gene9	1e-35
4	Gene5	Gene10	1e-30
## Alignment 2: score=800 e_value=1e-40 N=5 Chr03&Chr04 minus
0	Gene11	Gene16	1e-40
1	Gene12	Gene17	1e-35
2	Gene13	Gene18	1e-30
3	Gene14	Gene19	1e-25
4	Gene15	Gene20	1e-20
"""
    
    # Create layout file for multiple synteny
    layout_content = """Genome_A: Chr01 Chr02
Genome_B: Chr03 Chr04
"""
    
    # Create gene pairs file
    pairs_content = """Gene1	Gene11	255,0,0
Gene2	Gene12	255,0,0
Gene3	Gene13	255,0,0
Gene4	Gene14	255,0,0
Gene5	Gene15	255,0,0
Gene6	Gene16	0,0,255
Gene7	Gene17	0,0,255
Gene8	Gene18	0,0,255
Gene9	Gene19	0,0,255
Gene10	Gene20	0,0,255
"""
    
    # Write test files
    with open('test_gff.txt', 'w') as f:
        f.write(gff_content)
    
    with open('test_collinearity.txt', 'w') as f:
        f.write(collinearity_content)
    
    with open('test_layout.txt', 'w') as f:
        f.write(layout_content)
    
    with open('test_pairs.txt', 'w') as f:
        f.write(pairs_content)
    
    print("Test data files created successfully!")
    return {
        'gff': 'test_gff.txt',
        'collinearity': 'test_collinearity.txt',
        'layout': 'test_layout.txt',
        'pairs': 'test_pairs.txt'
    }


def test_dual_synteny(files):
    """Test dual synteny plotter"""
    print("\nTesting Dual Synteny Plotter...")
    
    plotter = DualSyntenyPlotter()
    plotter.parse_gff(files['gff'])
    plotter.parse_collinearity(files['collinearity'])
    plotter.set_chromosomes(['Chr01', 'Chr02'], ['Chr03', 'Chr04'])
    plotter.min_genes_in_block = 3  # Lower threshold for test
    
    fig = plotter.plot('test_dual_synteny.png', dpi=150)
    print("Dual synteny plot saved to test_dual_synteny.png")
    plt.close(fig)


def test_multiple_synteny(files):
    """Test multiple species synteny plotter"""
    print("\nTesting Multiple Species Synteny Plotter...")
    
    plotter = MultipleSpeciesSynteny()
    plotter.parse_gff(files['gff'])
    plotter.parse_chr_layout(files['layout'])
    plotter.parse_gene_pairs(files['pairs'])
    
    fig = plotter.plot('test_multiple_synteny.png', dpi=150)
    print("Multiple synteny plot saved to test_multiple_synteny.png")
    plt.close(fig)


def test_micro_synteny(files):
    """Test micro synteny plotter"""
    print("\nTesting Micro Synteny Plotter...")
    
    plotter = MicroSyntenyPlotter()
    plotter.parse_gff(files['gff'])
    plotter.parse_collinearity(files['collinearity'])
    plotter.set_regions(('Chr01', 0, 11000), ('Chr02', 0, 11000))
    plotter.show_gene_names = True
    
    fig = plotter.plot('test_micro_synteny.png', dpi=150)
    print("Micro synteny plot saved to test_micro_synteny.png")
    plt.close(fig)


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    
    print("Testing Synteny Visualization Module")
    print("=" * 50)
    
    # Create test data
    files = create_test_data()
    
    # Test each plotter
    test_dual_synteny(files)
    test_multiple_synteny(files)
    test_micro_synteny(files)
    
    # Clean up test files
    for f in files.values():
        if os.path.exists(f):
            os.remove(f)
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("Generated test images:")
    print("  - test_dual_synteny.png")
    print("  - test_multiple_synteny.png")
    print("  - test_micro_synteny.png")
