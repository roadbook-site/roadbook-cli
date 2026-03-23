from ..utils.output import print_table, print_info

def search_books(args):
    keyword = args.keyword
    print_info(f"Searching for '{keyword}' in remote registry...")
    
    # Mock results
    print_table(
        ["ID", "Name", "Description"],
        [
            ["rb-amazon-v1", "Amazon Checkout", "Search and buy on Amazon"],
            ["rb-google-search", "Google Search", "Simple Google Search"],
            ["rb-github-login", "GitHub Login", "Login to GitHub"]
        ]
    )
    print_info("[Info] This is a mock search result.")
    print_info("[Action] Use 'roadbook show <id>' to inspect details, then 'roadbook run --guide <id>' to start guidance.")
