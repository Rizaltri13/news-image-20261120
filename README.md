# The World Today — Friday 20 November 2026 in one image

[![make.fun](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120)
[![Rank](https://make.fun/badge/news-image-20261120/Rizaltri13/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120)
[![Reward](https://make.fun/badge/news-image-20261120/Rizaltri13/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120)

A make.fun bounty entry for
[news-image-20261120](https://make.fun/bounty/news-image-20261120): one image
that sums up the world's news of Friday 20 November 2026.

## The program

`main.py` (Python 3, standard library only, no network) draws a 1024×1024
newspaper front page — masthead "THE WORLD TODAY", a red date band, a large
hero panel for the lead story, six story tiles, and a bottom ticker of
shorter items — and encodes it as a PNG with a hand-rolled encoder
(`zlib` + `struct`). The hero panel is a media-generated illustration of
Kyiv at predawn (`hero.png`, decoded here with a small PNG reader); every
letter on the page comes from a hand-typed 5×7 bitmap font, so the text
stays sharp and the output is fully deterministic: two runs produce
byte-identical files.

Run it with:

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
```

## The day's stories

- **Lead — Missiles strike Kyiv overnight.** Russian ballistic missiles hit
  the capital before dawn; a fire broke out in a northern district after
  debris struck a building, the mayor said. (Source: Reuters)
- **Houthis claim four Saudi strikes.** Four targets claimed, including
  Riyadh airport and a finance hub. (Source: TASS)
- **Iran: mines hit three tankers.** Three tankers caught fire after hitting
  mines near the Strait of Hormuz, Tehran says. (Sources: Al Jazeera, AP)
- **Drones shut Genoa airport.** Flights halted for four hours after
  unidentified drones were spotted. (Source: wire reports)
- **Anthropic soars on Nasdaq debut.** Shares of the AI firm jump 17% on day
  one, closing near $97. (Source: AFP)
- **Trump pardons Pete Rose.** The late hits king is pardoned for tax crimes
  by the president. (Sources: Reuters, AP)
- **Eisenkot tapped to form government.** President Herzog picks the
  ex-army chief over Netanyahu to build a coalition. (Source: wire reports)
- **Ticker:** India evacuates 80,000 as a storm nears · Fiji declares a
  drought disaster · Seoul court clears ex-PM Han · California targets
  Nvidia over China chips. (Sources: wire reports)
