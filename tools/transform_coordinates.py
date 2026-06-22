from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from pyproj import CRS, Transformer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform CSV coordinates and always write a new output file."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-epsg", required=True, type=int)
    parser.add_argument("--target-epsg", required=True, type=int)
    parser.add_argument("--x-column", default="X")
    parser.add_argument("--y-column", default="Y")
    parser.add_argument("--z-column", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input does not exist: {input_path}")
    if output_path.exists():
        raise FileExistsError(
            f"Output already exists and will not be overwritten: {output_path}"
        )
    if input_path == output_path:
        raise ValueError("Input and output paths must be different.")

    source_crs = CRS.from_epsg(args.source_epsg)
    target_crs = CRS.from_epsg(args.target_epsg)
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)

    df = pd.read_csv(input_path)
    required = {args.x_column, args.y_column}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing coordinate columns: {sorted(missing)}")

    x_values = df[args.x_column].astype(float).to_numpy()
    y_values = df[args.y_column].astype(float).to_numpy()

    if args.z_column:
        if args.z_column not in df.columns:
            raise ValueError(f"Missing Z column: {args.z_column}")
        z_values = df[args.z_column].astype(float).to_numpy()
        x_out, y_out, z_out = transformer.transform(x_values, y_values, z_values)
        df[f"{args.x_column}_TRANSFORMED"] = x_out
        df[f"{args.y_column}_TRANSFORMED"] = y_out
        df[f"{args.z_column}_TRANSFORMED"] = z_out
    else:
        x_out, y_out = transformer.transform(x_values, y_values)
        df[f"{args.x_column}_TRANSFORMED"] = x_out
        df[f"{args.y_column}_TRANSFORMED"] = y_out

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    metadata = {
        "input": str(input_path),
        "output": str(output_path),
        "source_crs": source_crs.to_string(),
        "target_crs": target_crs.to_string(),
        "always_xy": True,
        "row_count": int(len(df)),
        "warning": (
            "EPSG transformation only. This does not replace validation of local "
            "datum/transformation parameters, geoid handling, or control points."
        ),
    }
    metadata_path = output_path.with_suffix(output_path.suffix + ".metadata.json")
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
