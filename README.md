![repo label](./images/repo_label.png)

This repository contains tools that were built during the [MEIE project](https://shekn.itch.io/meie-mass-effect-for-infinity-engine). This project is a very simple prototype of a classic isometric RPG built for the GemRB engine. The game uses Mass Effect 2 assets and recreates the opening sequence of that game.

All tools are divided into two types.

The first type is [tools](legendary_extension/README.md) for extracting resources from Mass Effect games. They primarily use Legendary Explorer but automate the process with Python to make extraction more efficient.

The second type is tools for building graphic resources for the GemRB engine. The key component is the [Python module](bam_io/README.md) for reading and writing BAM V2 files.
