#!/usr/bin/env python3
"""Optional matplotlib review sheet; core CSV generator is standard-library only."""
import csv
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import MaxNLocator
from project_market_history import WAT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'market-history/2026-11-05'


def ema(values, period):
    result = [values[0]]
    for value in values[1:]:
        result.append(result[-1] + 2 / (period + 1) * (value - result[-1]))
    return result


def render():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'svg.hashsalt': 'market-structure-v2'})
    fig = plt.figure(figsize=(16, 11), facecolor='#10141c')
    grid = fig.add_gridspec(4, 2, height_ratios=[4, 1, 4, 1], hspace=.24, wspace=.18)
    for n, symbol in enumerate(['BAR', 'RMD', 'MBP', 'BAR-RMD']):
        with (OUT / 'admin' / (symbol + '.csv')).open() as f:
            hourly = list(csv.DictReader(f))
        # Four-hour candles, using all synchronized hourly observations.
        candles = []
        for i in range(0, len(hourly), 4):
            group = hourly[i:i+4]
            candles.append(dict(time=group[0]['openTime'],
                o=int(group[0]['openMicros'])/1e6, c=int(group[-1]['closeMicros'])/1e6,
                h=max(int(r['highMicros']) for r in group)/1e6,
                l=min(int(r['lowMicros']) for r in group)/1e6,
                volume=sum(float(r['volumeUsd']) for r in group)))
        ax = fig.add_subplot(grid[(n//2)*2, n%2])
        vol = fig.add_subplot(grid[(n//2)*2+1, n%2], sharex=ax)
        for panel in [ax, vol]:
            panel.set_facecolor('#10141c');panel.tick_params(colors='#9ba9bd', length=0)
            panel.grid(axis='y', color='#26303f', linewidth=.45)
            for spine in panel.spines.values():spine.set_visible(False)
            panel.yaxis.tick_right()
        for x, r in enumerate(candles):
            color = '#2cc7a0' if r['c'] >= r['o'] else '#ed6376'
            ax.vlines(x, r['l'], r['h'], color=color, linewidth=.65)
            ax.add_patch(Rectangle((x-.33, min(r['o'], r['c'])), .66,
                                  max(abs(r['c']-r['o']), .02), color=color, linewidth=0))
            vol.bar(x, r['volume']/1000, color=color, width=.75, alpha=.65)
        closes = [r['c'] for r in candles]
        ax.plot(ema(closes, 20), color='#e8bc6a', linewidth=1, label='EMA 20')
        ax.plot(ema(closes, 50), color='#8faafc', linewidth=1, label='EMA 50')
        for field, color, label in [('referenceMicros','#7c8da7','Reference'),
                                    ('lowerMicros','#714654','Lower band'),('upperMicros','#714654','Upper band')]:
            ax.axhline(int(hourly[0][field])/1e6, color=color, linestyle='--', linewidth=.7, label=label)
        ax.set_title(symbol.replace('-', '/')+'  /  4H', loc='left', color='#e7edf7', fontsize=13, pad=12)
        ax.legend(loc='upper left', ncol=3, fontsize=7, facecolor='#10141c',
                  edgecolor='none', labelcolor='#a8b5c8')
        ax.tick_params(labelbottom=False)
        vol.yaxis.set_major_locator(MaxNLocator(2));vol.set_ylabel('USD k', color='#9ba9bd', fontsize=8)
        ticks = list(range(0, len(candles), 48))
        vol.set_xticks(ticks, [datetime.fromisoformat(candles[x]['time'].replace('Z','+00:00')).astimezone(WAT).strftime('%d %b') for x in ticks])
        ax.set_xlim(-2, len(candles)+1)
    fig.suptitle('BLACKBOOK / Market structure review', x=.055, y=.98, ha='left', color='#edf2fa', fontsize=21)
    fig.text(.055,.944,'5 November–30 December 2026 · Generated scenario · Pinned Nov 4 candidate references · USD notional volume', color='#9ba9bd', fontsize=10)
    fig.subplots_adjust(top=.90, bottom=.06, left=.045, right=.95)
    fig.savefig(OUT/'preview.png', dpi=125, facecolor=fig.get_facecolor())


if __name__ == '__main__':
    render()
