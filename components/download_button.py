"""
download_button.py — Reusable CSV download button component.

Usage:
    from components.download_button import make_download_button
    # Add to layout:
    make_download_button("my-chart-id", tooltip="Download emissions data")

Callbacks are registered via pattern-matching in app.py.
CSV output includes source/license header block for data provenance.
"""

from datetime import date

import dash_bootstrap_components as dbc
from dash import dcc, html


def make_download_button(data_key: str, tooltip: str = "Download as CSV") -> html.Div:
    """Return a download icon button + dcc.Download component.

    Parameters
    ----------
    data_key : str
        Unique key identifying the dataset (e.g., "emissions", "energy_mix").
        Used in pattern-matching callback IDs.
    tooltip : str
        Tooltip text shown on hover.
    """
    return html.Div(
        [
            dbc.Button(
                html.I(className="bi bi-download"),
                id={"type": "download-btn", "index": data_key},
                size="sm",
                outline=True,
                color="secondary",
                className="download-btn",
                title=tooltip,
            ),
            dcc.Download(id={"type": "download-csv", "index": data_key}),
            # Hidden store for the data key (used by callback)
            dcc.Store(
                id={"type": "download-data-key", "index": data_key},
                data=data_key,
            ),
        ],
        className="d-inline-block ms-2",
        style={"verticalAlign": "middle"},
    )


def csv_with_header(df, filename: str, source: str, license_info: str = "CC-BY 4.0") -> dict:
    """Convert a DataFrame to CSV with source/license header block.

    Returns a dict suitable for dcc.send_string().
    """
    header_lines = [
        f"# Source: {source}",
        f"# License: {license_info}",
        f"# Downloaded from: Energy Transition Dashboard",
        f"# Date: {date.today().isoformat()}",
        "#",
    ]
    header = "\n".join(header_lines) + "\n"
    csv_body = df.to_csv(index=False)
    return dcc.send_string(header + csv_body, filename)
