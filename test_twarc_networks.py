from click.testing import CliRunner
from twarc_networks import networks
import pathlib


runner = CliRunner()
test_data = pathlib.Path("test-data")


def process(fname):
    """
    Creates gexf output file using networks and checks for validness
    """
    input_file = test_data / f"{fname}.jsonl"
    output_file = test_data / f"{fname}.gexf"
    if output_file.is_file():
        output_file.unlink()
    result = runner.invoke(networks, [str(input_file), str(output_file)])
    assert output_file.is_file()

def test_tweets1():
    process("tweets1")

def test_tweets2():
    process("tweets2")
