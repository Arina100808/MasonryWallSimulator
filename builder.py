import argparse
from models.stretcher_wall import StretcherBondWall
from models.english_wall import EnglishBondWall
from models.wild_wall import WildBondWall

def parse_arguments():
    parser = argparse.ArgumentParser(description="Brick Wall Builder CLI")

    # Main parameters with defaults
    parser.add_argument('--bond', type=str, default='stretcher',
                        choices=['stretcher', 'english', 'wild'],
                        help='Type of bond: stretcher, english, wild (default: stretcher)')

    parser.add_argument('--width', type=float, default=2300.0, help='Wall width in mm (default: 2300)')
    parser.add_argument('--height', type=float, default=2000.0, help='Wall height in mm (default: 2000)')
    parser.add_argument('--brick-length', type=float, default=210.0, help='Brick length in mm (default: 210)')
    parser.add_argument('--brick-width', type=float, default=100.0, help='Brick width in mm (default: 100)')
    parser.add_argument('--brick-height', type=float, default=50.0, help='Brick height in mm (default: 50)')
    parser.add_argument('--head-joint', type=float, default=10.0, help='Head joint thickness in mm (default: 10)')
    parser.add_argument('--bed-joint', type=float, default=12.5, help='Bed joint thickness in mm (default: 12.5)')

    # Stride (optimization) parameters
    parser.add_argument('--stride-width', type=float, default=None, help='Stride width for optimized build')
    parser.add_argument('--stride-height', type=float, default=None, help='Stride height for optimized build')

    # Visualization & debugging
    parser.add_argument('--scale', type=float, default=0.4, help='Visualization scale factor (default: 0.3)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    return parser.parse_args()


def main():
    args = parse_arguments()

    bond_classes = {
        'stretcher': StretcherBondWall,
        'english': EnglishBondWall,
        'wild': WildBondWall
    }

    WallClass = bond_classes[args.bond]

    wall = WallClass(
        height=args.height,
        width=args.width,
        brick_length=args.brick_length,
        brick_width=args.brick_width,
        brick_height=args.brick_height,
        head_joint=args.head_joint,
        bed_joint=args.bed_joint,
        bond=args.bond)

    wall.visualize_plan(
        scale=args.scale,
        stride_width=args.stride_width,
        stride_height=args.stride_height,
        debug=args.debug)


if __name__ == '__main__':
    main()
