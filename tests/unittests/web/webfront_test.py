from nav.web.webfront.utils import split_tools, Tool


def test_tools_should_be_split_in_3_columns():
    icon = ''
    description = ''
    tools = [
        Tool('one', '/one', icon, description),
        Tool('two', '/two', icon, description),
        Tool('three', '/three', icon, description),
        Tool('four', '/four', icon, description),
    ]
    split = split_tools(tools, parts=3)
    assert len(split) == 3
