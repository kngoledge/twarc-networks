import time
import json
import networkx
import itertools
import click

from twarc import ensure_flattened
from networkx import nx_pydot


@click.command()
@click.option('--min_subgraph_size', type=int, default=None, help='remove any subgraphs with a size smaller than this number')
@click.option('--max_subgraph_size', type=int, default=None, help='remove any subgraphs with a size larger than this number')
@click.option('--retweets', is_flag=True, default=False, help='include retweets')
@click.option('--users', is_flag=True, default=False, help='show user relations instead of tweet relations')
@click.option('--hashtags', is_flag=True, default=False, help='show hashtag relations instead of tweet relations')
@click.argument('infile', type=click.File('r'))
@click.argument('outfile', type=click.File('w'))


def networks(min_subgraph_size, max_subgraph_size, retweets, users, hashtags, infile, outfile):
    """
    Create networks from Twitter API V2 JSON.
    """

    G = networkx.DiGraph()

    def add(from_user, from_id, to_user, to_id, type):
        "adds a relation to the graph"

        if (users or hashtags) and to_user:
            G.add_node(from_user, screen_name=from_user)
            G.add_node(to_user, screen_name=to_user)

            if G.has_edge(from_user, to_user):
                weight = G[from_user][to_user]['weight'] + 1
            else:
                weight = 1
            G.add_edge(from_user, to_user, type=type, weight=weight)

        elif not users and to_id:
            G.add_node(from_id, screen_name=from_user, type=type)
            if to_user:
                G.add_node(to_id, screen_name=to_user)
            else:
                G.add_node(to_id)
            G.add_edge(from_id, to_id, type=type)

    def to_json(g):
        j = {"nodes": [], "links": []}
        for node_id, node_attrs in g.nodes(True):
            j["nodes"].append({
                "id": node_id,
                "type": node_attrs.get("type"),
                "screen_name": node_attrs.get("screen_name")
            })
        for source, target, attrs in g.edges(data=True):
            j["links"].append({
                "source": source,
                "target": target,
                "type": attrs.get("type")
            })
        return j

    count = 0
    for line in infile:
        count += 1
        line = line.strip()

        # ignore empty lines
        if line:
            try:
                data = json.loads(line)
                for tweet in ensure_flattened(data):
                    # View more on data dictionary here: https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet
                    from_user_name = tweet['author']['username']
                    from_user_id = tweet['author_id']
                    to_user_id = None
                    to_user_name = None

                    # standardize raw created at date to dd/MM/yyyy HH:mm:ss
                    created_at_date = time.strftime(
                        "%d/%m/%Y %H:%M:%S",
                        time.strptime(tweet['created_at'], "%a %b %d %H:%M:%S +0000 %Y"),
                    )

                    # create user-centric network
                    if users:
                        for u in tweet["entities"].get("mentions", []):
                            add(from_user_name, from_user_id, u['username'], u['id'], 'mention', created_at_date)

                    # create hashtag colocation network
                    elif hashtags:
                        hashtags = tweet['entities'].get('hashtags', [])
                        hashtag_pairs = list(itertools.combinations(hashtags, 2)) # list of all possible hashtag pairs
                        for u in hashtag_pairs:
                            # source hashtag: u[0]['text']
                            # target hashtag: u[1]['text']
                            add('#' + u[0]['tag'], None, '#' + u[1]['tag'], None, 'hashtag')

                    # default to retweet/quote/reply network
                    else:
                        for referenced_tweet in tweet['referenced_tweets']:
                            to_user_name = referenced_tweet['author']['username']
                            to_user_id = referenced_tweet['author_id']
                            tweet_response_type = referenced_tweet['type'] # retweet, reply, etc.
                            add(from_user_name, from_user_id, to_user_name, to_user_id, tweet_response_type)
            except Exception as e:
                click.echo(f"Unexpected JSON data on line {count}", err=True)
                break
            except json.decoder.JSONDecodeError as e:
                click.echo(f"Invalid JSON on line {count}", err=True)
                break

    # enforce min and max limits
    if min_subgraph_size or max_subgraph_size:
        g_copy = G.copy()
        for g in networkx.connected_component_subgraphs(G):
            if min_subgraph_size and len(g) < min_subgraph_size:
                g_copy.remove_nodes_from(g.nodes())
            elif max_subgraph_size and len(g) > max_subgraph_size:
                g_copy.remove_nodes_from(g.nodes())
        G = g_copy

    # write to outfile
    if outfile.name.endswith(".gexf"):
        networkx.write_gexf(G, outfile)
    elif outfile.name.endswith(".gml"):
        networkx.write_gml(G, outfile)
    elif outfile.name.endswith(".dot"):
        nx_pydot.write_dot(G, outfile)
    elif outfile.name.endswith(".json"):
        json.dump(to_json(G), open(outfile, "w"), indent=2)
    elif outfile.name.endswith(".html"):
        graph_data = json.dumps(to_json(G), indent=2)
        html = """<!DOCTYPE html>
<meta charset="utf-8">
<script src="https://platform.twitter.com/widgets.js"></script>
<script src="https://d3js.org/d3.v4.min.js"></script>
<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<style>
.links line {
  stroke: #999;
  stroke-opacity: 0.8;
  stroke-width: 2px;
}
line.reply {
  stroke: #999;
}
line.retweet {
  stroke-dasharray: 5;
}
line.quote {
  stroke-dasharray: 5;
}
.nodes circle {
  stroke: red;
  fill: red;
  stroke-width: 1.5px;
}
circle.retweet {
  fill: white;
  stroke: #999;
}
circle.reply {
  fill: #999;
  stroke: #999;
}
circle.quote {
  fill: yellow;
  stroke: yellow;
}
#graph {
  width: 99vw;
  height: 99vh;
}
#tweet {
  position: absolute;
  left: 100px;
  top: 150px;
}
</style>
<svg id="graph"></svg>
<div id="tweet"></div>
<script>
var width = $(window).width();
var height = $(window).height();
var svg = d3.select("svg")
    .attr("height", height)
    .attr("width", width);
var color = d3.scaleOrdinal(d3.schemeCategory20c);
var simulation = d3.forceSimulation()
    .velocityDecay(0.6)
    .force("link", d3.forceLink().id(function(d) { return d.id; }))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter(width / 2, height / 2));
var graph = %s;
var link = svg.append("g")
    .attr("class", "links")
  .selectAll("line")
  .data(graph.links)
  .enter().append("line")
    .attr("class", function(d) { return d.type; });
var node = svg.append("g")
    .attr("class", "nodes")
  .selectAll("circle")
  .data(graph.nodes)
  .enter().append("circle")
    .attr("r", 5)
    .attr("class", function(d) { return d.type; })
    .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));
node.append("title")
    .text(function(d) { return d.id; });
node.on("click", function(d) {
  $("#tweet").empty();
  var rect = this.getBoundingClientRect();
  var paneHeight = d.type == "retweet" ? 50 : 200;
  var paneWidth = d.type == "retweet" ? 75 : 500;
  var left = rect.x - paneWidth / 2;
  if (rect.y > height / 2) {
    var top = rect.y - paneHeight;
  } else {
    var top = rect.y + 10;
  }
  var tweet = $("#tweet");
  tweet.css({left: left, top: top});
  if (d.type == "retweet") {
    twttr.widgets.createFollowButton(d.screen_name, tweet[0], {size: "large"});
  } else {
    twttr.widgets.createTweet(d.id, tweet[0], {conversation: "none"});
  }
  d3.event.stopPropagation();
});
svg.on("click", function(d) {
  $("#tweet").empty();
});
simulation
    .nodes(graph.nodes)
    .on("tick", ticked);
simulation.force("link")
    .links(graph.links);
function ticked() {
  link
      .attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });
  node
      .attr("cx", function(d) { return d.x; })
      .attr("cy", function(d) { return d.y; });
}
function dragstarted(d) {
  if (!d3.event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}
function dragged(d) {
  d.fx = d3.event.x;
  d.fy = d3.event.y;
}
function dragended(d) {
  if (!d3.event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}
</script>
""" % graph_data
    open(outfile, "w").write(html)
