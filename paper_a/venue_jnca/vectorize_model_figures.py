"""Trace the saved image-model outputs into real vector paths.

Dependency: vtracer==0.6.12. Export PDF with rsvg-convert (librsvg).
Original supplied PNGs are retained; manuscript uses these PDF exports.
"""
from pathlib import Path
import subprocess
import vtracer
from vector_labels import correct_labels

ROOT = Path(__file__).resolve().parent
NAMES = ('system_architecture', 'decision_counterexample', 'protocol_sequence')
for name in NAMES:
    vtracer.convert_image_to_svg_py(
        str(ROOT / 'figure_sources' / f'{name}_model.png'),
        str(ROOT / f'{name}.svg'),
        colormode='color', hierarchical='stacked', mode='spline',
        filter_speckle=4, color_precision=6, layer_difference=32,
        corner_threshold=60, length_threshold=3.0, max_iterations=10,
        splice_threshold=45, path_precision=3,
    )
    correct_labels(ROOT / f'{name}.svg', name)
    subprocess.run([
        'rsvg-convert', '--format=pdf', '--output', str(ROOT / f'{name}.pdf'),
        str(ROOT / f'{name}.svg'),
    ], check=True)
    print(f'Exported {name}.svg and {name}.pdf', flush=True)
