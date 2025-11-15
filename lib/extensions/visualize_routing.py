# Authors: see git history
#
# Copyright (c) 2025 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from inkex import Group, PathElement

from ..i18n import _
from ..svg import PIXELS_PER_MM, get_correction_transform
from ..svg.tags import INKSCAPE_LABEL
from .base import InkstitchExtension


class VisualizeRouting(InkstitchExtension):
    """Visualize jump stitches and routing paths.

    Creates a visual overlay showing all jump stitches in the design,
    color-coded by length to identify problematic jumps.
    """

    def __init__(self, *args, **kwargs):
        InkstitchExtension.__init__(self, *args, **kwargs)
        self.arg_parser.add_argument("--short_threshold_mm", type=float, default=5.0,
                                     help="Threshold for short jumps (mm)")
        self.arg_parser.add_argument("--long_threshold_mm", type=float, default=15.0,
                                     help="Threshold for long jumps (mm)")

    def effect(self):
        if not self.get_elements():
            return

        # Get stitch groups
        stitch_groups = self.elements_to_stitch_groups(self.elements)

        if not stitch_groups:
            self.errormsg(_("No stitchable elements found"))
            return

        # Create visualization layer
        viz_layer = self._create_visualization_layer()

        # Visualize jumps
        jump_count = self._visualize_jumps(stitch_groups, viz_layer)

        self.msg(_(f"Created jump visualization with {jump_count} jumps.\n\n"
                   f"Color coding:\n"
                   f"  Green: Short jumps (<{self.options.short_threshold_mm}mm)\n"
                   f"  Yellow: Medium jumps ({self.options.short_threshold_mm}-{self.options.long_threshold_mm}mm)\n"
                   f"  Red: Long jumps (>{self.options.long_threshold_mm}mm)"))

    def _create_visualization_layer(self):
        """Create a new layer for visualization."""
        svg_root = self.document.getroot()

        layer = Group()
        layer.set(INKSCAPE_LABEL, "Jump Stitch Visualization")
        layer.set('inkscape:groupmode', 'layer')
        layer.set('inkstitch:ignore_layer', 'true')

        svg_root.append(layer)
        return layer

    def _visualize_jumps(self, stitch_groups, layer):
        """Create visual representation of all jumps."""
        short_threshold = self.options.short_threshold_mm * PIXELS_PER_MM
        long_threshold = self.options.long_threshold_mm * PIXELS_PER_MM

        jump_count = 0
        total_length = 0

        prev_group = None
        for group in stitch_groups:
            if prev_group and group.stitches and prev_group.stitches:
                start = prev_group.stitches[-1]
                end = group.stitches[0]
                jump_length = (end - start).length()

                # Determine color based on length
                if jump_length < short_threshold:
                    color = "#00ff00"  # Green - OK
                    width = 0.5
                elif jump_length < long_threshold:
                    color = "#ffff00"  # Yellow - Medium
                    width = 1.0
                else:
                    color = "#ff0000"  # Red - Long/problematic
                    width = 1.5

                # Create jump line
                jump_line = PathElement()
                jump_line.set('d', f"M {start.x},{start.y} L {end.x},{end.y}")
                jump_line.set('style', f'fill:none;stroke:{color};stroke-width:{width};opacity:0.7')
                jump_line.set(INKSCAPE_LABEL, f"Jump {jump_count+1}: {jump_length/PIXELS_PER_MM:.1f}mm")

                layer.append(jump_line)

                jump_count += 1
                total_length += jump_length

                # Add length label for long jumps
                if jump_length > long_threshold:
                    self._add_length_label(layer, start, end, jump_length)

            prev_group = group

        return jump_count

    def _add_length_label(self, layer, start, end, length):
        """Add a text label showing jump length."""
        from inkex import TextElement, Tspan

        # Calculate midpoint
        mid_x = (start.x + end.x) / 2
        mid_y = (start.y + end.y) / 2

        # Create text element
        text = TextElement()
        text.set('x', str(mid_x))
        text.set('y', str(mid_y))
        text.set('style', 'font-size:3px;fill:#ff0000;font-family:sans-serif')

        tspan = Tspan()
        tspan.text = f"{length/PIXELS_PER_MM:.1f}mm"
        text.append(tspan)

        layer.append(text)
