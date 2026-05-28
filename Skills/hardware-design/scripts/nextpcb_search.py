import requests
import json
import argparse
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner

def search_for_part(description, show_all, no_sort):
    """
    Replicates the part search request with a rich CLI, adding a second 
    stage to fetch stock information, with options to filter and sort by stock.

    Args:
        description (str): The search term for the electronic part.
        show_all (bool): If True, parts with zero stock will be included.
        no_sort (bool): If True, results will not be sorted by stock.
    """
    console = Console()
    spinner = Spinner("dots", text=" Searching for parts...")

    with Live(spinner, console=console, screen=False, vertical_overflow="visible") as live:
        try:
            # Stage 1: Initial search for basic part data
            live.update(Spinner("dots", text=f" Searching for '{description}'..."))
            initial_url = "https://www.eda.cn/api/chiplet/products/queryPage"
            initial_payload = {"desc": description, "pageNum": 1, "pageSize": 24}
            headers = {"Content-Type": "application/json"}

            response = requests.post(initial_url, headers=headers, json=initial_payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            results = data.get("result", [])

            if not results:
                console.print(f"[bold yellow]No parts found matching the description: '{description}'.[/bold yellow]")
                return

            # Stage 2: Prepare and execute search for supply chain data
            live.update(Spinner("dots", text=f" Found {len(results)} parts, fetching stock & price..."))
            bom_list = []
            for item in results:
                part_info = item.get("queryPartVO", {}).get("part", {})
                if part_info and 'mpn' in part_info and 'manufacturer_id' in part_info:
                    bom_list.append({
                        "id": part_info['manufacturer_id'], "mpn": part_info['mpn'],
                        "customerSupply": "0", "location": "SW1,SW2", "qty": 1
                    })
            
            stock_data = []
            if bom_list:
                stock_url = "https://smtapi.nextpcb.com/nextpcb/pcba/bom/inquiry"
                stock_payload = {"bomNumber": len(bom_list), "list": bom_list}
                stock_params = {
                    "appid": "j1LWf238", "timestamp": "1681810983",
                    "signature": "8e02b899be91b77dc140dfc2388dde95"
                }
                stock_response = requests.post(stock_url, headers=headers, params=stock_params, json=stock_payload, timeout=30)
                stock_response.raise_for_status()
                stock_data = stock_response.json().get("result", [])
            
            # Merge, filter, and sort data
            live.update(Spinner("dots", text=" Processing results..."))
            stock_map = {item.get("mpn"): item.get("stockQty") or 0 for item in stock_data}
            price_map = {item.get("mpn"): item.get("price") or 0.0 for item in stock_data}

            for item in results:
                part_info = item.get("queryPartVO", {}).get("part", {})
                if part_info and 'mpn' in part_info:
                    part_info['stock'] = stock_map.get(part_info['mpn'], 0)
                    part_info['price'] = price_map.get(part_info['mpn'], 0.0)

            if not show_all:
                results = [item for item in results if item.get("queryPartVO", {}).get("part", {}).get('stock', 0) > 0]

            if not no_sort:
                results.sort(key=lambda item: item.get("queryPartVO", {}).get("part", {}).get('stock', 0), reverse=True)
            
        except requests.exceptions.RequestException as e:
            live.stop()
            console.print(f"[bold red]An error occurred during the request:[/bold red] {e}")
            return
        except json.JSONDecodeError:
            live.stop()
            console.print("[bold red]Failed to decode the JSON response from the server.[/bold red]")
            return

    # Create and display the results table
    table = Table(title=f"Search Results for '{description}'", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("MPN (Clickable)", style="cyan", no_wrap=True)
    table.add_column("Manufacturer", style="green")
    table.add_column("Category", style="yellow", no_wrap=True)
    table.add_column("Package", style="magenta", no_wrap=True)
    table.add_column("Stock", justify="right", style="bold blue")
    table.add_column("Price (USD)", justify="right", style="bold green")
    table.add_column("Datasheet", style="dim cyan")

    for index, item in enumerate(results):
        part_info = item.get("queryPartVO", {}).get("part", {})
        if part_info:
            mpn = part_info.get('mpn', 'N/A')
            mpn_link = f"[link=https://www.google.com/search?q={mpn}]{mpn}[/link]"
            
            manufacturer = part_info.get('manufacturer', 'N/A')
            category = part_info.get('category', 'N/A')
            package = part_info.get('package') or 'N/A'
            stock = part_info.get('stock', 0)
            price = part_info.get('price', 0.0)
            stock_str = f"{stock:,}"
            price_str = f"${price:.4f}" if price else "N/A"

            datasheet_url = part_info.get('datasheet', '')
            if datasheet_url and not datasheet_url.startswith('http'):
                datasheet_url = 'https:' + datasheet_url
            datasheet_link = f"[link={datasheet_url}]Link[/link]" if datasheet_url else "N/A"

            table.add_row(
                str(index + 1),
                mpn_link,
                manufacturer,
                category,
                package,
                stock_str,
                price_str,
                datasheet_link
            )

    console.print(table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search for electronic parts. By default, hides parts with no stock and sorts by stock quantity."
    )
    parser.add_argument(
        "query", 
        type=str, 
        help="The search description for the part (e.g., '0201 100k Ohm resistor')."
    )
    parser.add_argument(
        "--show-all", 
        action="store_true", 
        help="Show all parts, including those with no stock."
    )
    parser.add_argument(
        "--no-sort", 
        action="store_true", 
        help="Do not sort the results by stock quantity."
    )
    
    args = parser.parse_args()

    search_for_part(args.query, args.show_all, args.no_sort)


