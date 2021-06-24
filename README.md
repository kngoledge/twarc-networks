# twarc-networks

This module extends [twarc](https://github.com/docnow/twarc) to allow you to build a reply, quote, retweet network from a file of tweets and write it out as a gexf, dot, json or  html file. You will need to have `networkx` installed and `pydotplus` if you want to use `dot`. The html presentation uses D3 to display the network graph in your browser.

## Install

First you need to install twarc and this plugin:
```
pip install twarc
pip install twarc-networks
```
To create a static D3 visualization use the subcommand `networks` that is supplied by `twarc-networks`:
```
twarc2 networks tweets.jsonl network.html
```
Optionally you can consolidate tweets by user, allowing you to see central accounts:
```
twarc2 networks --users tweets.jsonl network.html
```
Additionally, you can create a network of hashtags, allowing you to view their colocation:
```
twarc2 networks --hashtags tweets.jsonl tweets.html
```
And if you want to use the network graph in a program like Gephi, you can generate a GEXF file with the following:
```
twarc2 networks --users tweets.jsonl tweets.gexf
twarc2 networks --hashtags tweets.jsonl tweets.gexf
```
## Testing

To run the tests you will need run:
```
python setup.py test
```
