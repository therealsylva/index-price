#!/usr/bin/env python3
"""Optional review of the actual corrected hourly CSVs around November 5."""
import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'market-history/2026-11-06'
WAT = timezone(timedelta(hours=1))


def render():
    fig, axes = plt.subplots(3, 1, figsize=(14, 11), facecolor='#10151e')
    for ax, symbol in zip(axes, ['RMD', 'BAR', 'BRUNO']):
        with (DIRECTORY / 'admin' / (symbol + '.csv')).open() as f:
            rows = [r for r in csv.DictReader(f) if '2026-11-03T00:00:00Z' <= r['openTime'] < '2026-11-06T06:00:00Z']
        ax.set_facecolor('#10151e')
        for i, row in enumerate(rows):
            o, h, low, c = [int(row[k])/1e6 for k in ('openMicros', 'highMicros', 'lowMicros', 'closeMicros')]
            color = '#33c9a4' if c >= o else '#ed6376'
            ax.vlines(i, low, h, color=color, lw=.9)
            ax.add_patch(Rectangle((i-.33, min(o, c)), .66, max(abs(c-o), .01), color=color, lw=0))
        for field, color in [('lowerMicros', '#7e5266'), ('upperMicros', '#7e5266'), ('referenceMicros', '#7589ab')]:
            ax.step(range(len(rows)), [int(r[field])/1e6 for r in rows], where='post', color=color, ls='--', lw=.7)
        for at, label, color in [('2026-11-04T00:00:00Z', 'Nov 4 publication', '#e8bc6a'),
                                 ('2026-11-04T23:00:00Z', 'Nov 5: continuous join', '#33c9a4')]:
            i = next(i for i, r in enumerate(rows) if r['openTime'] == at)
            ax.axvline(i-.5, color=color, ls=':', lw=1)
            ax.text(i+.5, .97, label, transform=ax.get_xaxis_transform(), color=color, va='top', fontsize=9)
        ticks = list(range(0, len(rows), 12))
        ax.set_xticks(ticks, [datetime.fromisoformat(rows[i]['openTime'].replace('Z','+00:00')).astimezone(WAT).strftime('%d %b %H:%M') for i in ticks])
        ax.tick_params(colors='#9eacc0', length=0, pad=7)
        ax.grid(axis='y', color='#293344', lw=.6)
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.yaxis.tick_right()
        ax.set_title(symbol+' / 1H', loc='left', color='#edf2fa', fontsize=14, pad=12)
        ax.set_xlim(-1, len(rows))
    fig.suptitle('Corrected CSV / publication timeline and continuous join', x=.055, y=.98, ha='left', color='#edf2fa', fontsize=19)
    fig.text(.055,.94,'Actual hourly OHLC from the replacement CSVs · Dotted green line marks the former November 5 reset · Times in Nigeria', color='#a8b5c8', fontsize=10)
    fig.text(.055,.025,'Generated scenario. A genuine repricing can remain at Nov 4 when a newly published hard band excludes the preceding market price.', color='#a8b5c8', fontsize=9)
    fig.subplots_adjust(top=.89, bottom=.08, left=.055, right=.93, hspace=.38)
    fig.savefig(DIRECTORY / 'preview.png', dpi=130, facecolor=fig.get_facecolor())


if __name__ == '__main__':
    render()
