from superagi.tools.google_serp_search import GoogleSerpTool

def test_search_run():
    tool = GoogleSerpTool(api_key='4ff36b0914cedf280222c47528cb1fdb7f19c1fc')
    result = tool.search_run('Apple')
    assert 'snippets' in result
    assert 'links' in result
    # Add more assertions here based on what you expect the output to be