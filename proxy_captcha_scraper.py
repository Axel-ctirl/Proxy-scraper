#!/usr/bin/env python3
"""
GRASS Proxy & Captcha Key Scraper & Tester
A comprehensive tool to scrape, test, and validate proxies and captcha keys
"""

import asyncio
import aiohttp
import requests
import time
import random
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Union, Sequence
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from concurrent.futures import ThreadPoolExecutor
import threading
from urllib.parse import urlparse, urljoin, quote
import re
import urllib.parse

console = Console()

class ProxyCaptchaScraper:
    def __init__(self):
        self.working_proxies = []
        self.failed_proxies = []
        self.working_captcha_keys = []
        self.failed_captcha_keys = []
        self.test_results = {}
        self.last_used_sources = {"proxies": [], "captcha": []}
        self._last_used_sources_file = self.get_downloads_folder() / "grass_last_used_sources.json"
        # New: persistent set of all used sources
        self._all_used_sources_file = self.get_downloads_folder() / "grass_all_used_sources.json"
        self.all_used_sources = {"proxies": set(), "captcha": set()}
        self._load_last_used_sources()
        self._load_all_used_sources()

        # Proxy sources - expanded list
        self.proxy_sources = [
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
            "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
            "https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list",
            "https://raw.githubusercontent.com/a2u/free-proxy/master/proxy.txt",
            "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
            "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt",
            "https://raw.githubusercontent.com/almroot/proxylist/master/list.txt",
            "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
            "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/https.txt",
            "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
            "https://raw.githubusercontent.com/prxchk/proxy-list/main/https.txt",
            "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/http.txt",
            "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/https.txt"
        ]

        # Captcha key scraping sources
        self.captcha_sources = [
            "https://raw.githubusercontent.com/2captcha/2captcha-python/master/examples/keys.txt",
            "https://raw.githubusercontent.com/anti-captcha/anti-captcha-python/master/examples/keys.txt",
            "https://raw.githubusercontent.com/rucaptcha/rucaptcha-python/master/examples/keys.txt",
            "https://raw.githubusercontent.com/azcaptcha/azcaptcha-python/master/examples/keys.txt",
            "https://raw.githubusercontent.com/deathbycaptcha/deathbycaptcha-python/master/examples/keys.txt",
            "https://api.anti-captcha.com/getBalance",
            "https://2captcha.com/res.php",
            "https://rucaptcha.com/res.php",
            "https://azcaptcha.com/api/",
            "https://deathbycaptcha.com/api/"
        ]

        # Captcha key patterns to look for in scraped content
        self.captcha_patterns = [
            r'[a-zA-Z0-9]{32}',  # 32 character alphanumeric keys
            r'[a-zA-Z0-9]{40}',  # 40 character alphanumeric keys
            r'[a-zA-Z0-9]{64}',  # 64 character alphanumeric keys
            r'[a-zA-Z0-9]{20,}', # 20+ character alphanumeric keys
        ]

        # Test URLs for proxy validation
        self.test_urls = [
            "http://httpbin.org/ip",
            "http://ip-api.com/json",
            "https://api.ipify.org?format=json",
            "http://ipinfo.io/json"
        ]

        # Captcha test endpoints
        self.captcha_test_endpoints = [
            "https://api.anti-captcha.com/getBalance",
            "https://2captcha.com/res.php",
            "https://rucaptcha.com/res.php"
        ]

        # Search engines and discovery sources
        self.search_sources = [
            "https://github.com/search?q=",
            "https://raw.githubusercontent.com/",
            "https://gist.githubusercontent.com/",
            "https://pastebin.com/raw/",
            "https://rentry.co/",
            "https://ghostbin.co/",
            "https://hastebin.com/raw/",
            "https://paste.ee/r/",
            "https://pastebin.com/",
            "https://github.com/topics/",
            "https://github.com/search?type=repositories&q="
        ]

        # Common search terms for finding proxy and captcha sources
        self.proxy_search_terms = [
            "proxy list",
            "free proxies",
            "http proxies",
            "https proxies",
            "socks5 proxies",
            "proxy.txt",
            "proxies.txt",
            "proxy-list",
            "public proxies",
            "working proxies",
            "proxy servers",
            "anonymous proxies"
        ]

        self.captcha_search_terms = [
            "captcha api key",
            "2captcha key",
            "anti-captcha key",
            "rucaptcha key",
            "captcha service",
            "captcha solver",
            "captcha api",
            "captcha keys",
            "captcha token",
            "captcha balance"
        ]

    def get_downloads_folder(self) -> Path:
        """Get the Downloads folder path for the current user"""
        downloads = Path.home() / "Downloads"
        if not downloads.exists():
            # Fallback to current directory if Downloads doesn't exist
            downloads = Path.cwd()
        return downloads

    def _load_last_used_sources(self):
        """Load last used sources from file if it exists."""
        try:
            if self._last_used_sources_file.exists():
                with open(self._last_used_sources_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.last_used_sources = data
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load last used sources: {e}[/yellow]")

    def _save_last_used_sources(self):
        """Save last used sources to file."""
        try:
            with open(self._last_used_sources_file, 'w') as f:
                json.dump(self.last_used_sources, f, indent=2)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save last used sources: {e}[/yellow]")

    def _load_all_used_sources(self):
        """Load all used sources from file if it exists."""
        try:
            if self._all_used_sources_file.exists():
                with open(self._all_used_sources_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Convert lists to sets for internal use
                        self.all_used_sources = {k: set(v) for k, v in data.items()}
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load all used sources: {e}[/yellow]")

    def _save_all_used_sources(self):
        """Save all used sources to file."""
        try:
            with open(self._all_used_sources_file, 'w') as f:
                # Convert sets to lists for JSON serialization
                json.dump({k: list(v) for k, v in self.all_used_sources.items()}, f, indent=2)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save all used sources: {e}[/yellow]")

    def get_rotated_sources(self, source_type: str, count: int = 5) -> List[str]:
        """Get a rotated list of sources, avoiding any previously used ones. Persists usage between runs."""
        if source_type == "proxies":
            all_sources = self.proxy_sources
            used_sources = self.all_used_sources["proxies"]
        else:  # captcha
            all_sources = self.captcha_sources
            used_sources = self.all_used_sources["captcha"]
        # Only select sources never used before
        available_sources = [s for s in all_sources if s not in used_sources]
        if len(available_sources) < count:
            # All sources have been used, reset and notify user
            console.print(f"[yellow]All {source_type} sources have been used. Resetting used list for fresh rotation.[/yellow]")
            used_sources.clear()
            available_sources = all_sources.copy()
        # Select random sources
        selected_sources = random.sample(available_sources, min(count, len(available_sources)))
        # Update used sources
        used_sources.update(selected_sources)
        self._save_all_used_sources()
        return selected_sources

    def create_header(self) -> Panel:
        header_text = Text("🌱 GRASS Proxy & Captcha Scraper & Tester 🌱", style="bold green")
        subtitle = Text("Scrape, Test, and Validate Proxies & Captcha Keys", style="italic blue")
        return Panel(
            Align.center(header_text + Text("\n") + subtitle),
            style="green",
            border_style="bright_green"
        )

    def create_menu(self) -> Table:
        menu = Table(title="📋 Main Menu", show_header=True, header_style="bold magenta")
        menu.add_column("Option", style="cyan", no_wrap=True)
        menu.add_column("Description", style="white")
        menu.add_row("1", "🔍 Scrape Proxies")
        menu.add_row("2", "🔑 Scrape Captcha Keys")
        menu.add_row("3", "⚡ Test Proxies")
        menu.add_row("4", "🔐 Test Captcha Keys")
        menu.add_row("5", "📊 View Results")
        menu.add_row("6", "💾 Save Results")
        menu.add_row("7", "📁 Load from Files")
        menu.add_row("8", "💾 Save to Downloads")
        menu.add_row("9", "🔍 Auto-Discover Sources")
        menu.add_row("10", "❌ Exit")
        return menu

    async def scrape_proxies(self) -> List[str]:
        console.print("\n[bold green]🔍 Scraping proxies from multiple sources...[/bold green]")

        all_proxies = set()
        
        # Get rotated sources (different each time)
        sources_to_use = self.get_rotated_sources("proxies", count=8)
        console.print(f"[blue]Using {len(sources_to_use)} different sources this time[/blue]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Scraping proxies...", total=len(sources_to_use))

            async with aiohttp.ClientSession() as session:
                for source in sources_to_use:
                    try:
                        timeout = aiohttp.ClientTimeout(total=10)
                        async with session.get(source, timeout=timeout) as response:
                            if response.status == 200:
                                content = await response.text()
                                # Extract IP:PORT format
                                proxies = re.findall(r'(?:\d{1,3}\.){3}\d{1,3}:\d+', content)
                                all_proxies.update(proxies)
                                console.print(f"[green]✓[/green] {source}: {len(proxies)} proxies found")
                            else:
                                console.print(f"[red]✗[/red] {source}: HTTP {response.status}")
                    except Exception as e:
                        console.print(f"[red]✗[/red] {source}: {str(e)}")

                    progress.advance(task)
                    await asyncio.sleep(0.5) # Be nice to servers

        proxies_list = list(all_proxies)
        console.print(f"\n[bold green]✅ Total unique proxies found: {len(proxies_list)}[/bold green]")
        return proxies_list

    async def scrape_captcha_keys(self) -> List[str]:
        console.print("\n[bold green]🔑 Scraping captcha keys from multiple sources...[/bold green]")

        all_keys = set()
        
        # Get rotated sources (different each time)
        sources_to_use = self.get_rotated_sources("captcha", count=6)
        console.print(f"[blue]Using {len(sources_to_use)} different sources this time[/blue]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Scraping captcha keys...", total=len(sources_to_use))

            async with aiohttp.ClientSession() as session:
                for source in sources_to_use:
                    try:
                        timeout = aiohttp.ClientTimeout(total=10)
                        async with session.get(source, timeout=timeout) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Try different patterns to find captcha keys
                                keys_found = []
                                for pattern in self.captcha_patterns:
                                    matches = re.findall(pattern, content)
                                    keys_found.extend(matches)
                                
                                # Filter out duplicates and invalid keys
                                valid_keys = []
                                for key in keys_found:
                                    if len(key) >= 20 and key not in valid_keys:
                                        valid_keys.append(key)
                                
                                all_keys.update(valid_keys)
                                console.print(f"[green]✓[/green] {source}: {len(valid_keys)} keys found")
                            else:
                                console.print(f"[red]✗[/red] {source}: HTTP {response.status}")
                    except Exception as e:
                        console.print(f"[red]✗[/red] {source}: {str(e)}")

                    progress.advance(task)
                    await asyncio.sleep(0.5) # Be nice to servers

        keys_list = list(all_keys)
        console.print(f"\n[bold green]✅ Total unique captcha keys found: {len(keys_list)}[/bold green]")
        return keys_list

    async def test_proxy(self, proxy: str, session: aiohttp.ClientSession) -> Tuple[bool, Dict]:
        try:
            proxy_url = f"http://{proxy}"
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(
                "http://httpbin.org/ip",
                proxy=proxy_url,
                timeout=timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return True, {
                        "proxy": proxy,
                        "ip": data.get("origin", "Unknown"),
                        "response_time": response.headers.get("X-Response-Time", "Unknown")
                    }
        except Exception as e:
            pass
        return False, {"proxy": proxy, "error": "Failed"}

    async def test_proxies(self, proxies: List[str], max_workers: int = 50) -> List[Dict]:
        console.print(f"\n[bold blue]⚡ Testing {len(proxies)} proxies...[/bold blue]")

        working_proxies = []
        semaphore = asyncio.Semaphore(max_workers)

        async def test_with_semaphore(proxy: str, session: aiohttp.ClientSession):
            async with semaphore:
                return await self.test_proxy(proxy, session)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Testing proxies...", total=len(proxies))

            async with aiohttp.ClientSession() as session:
                tasks = [test_with_semaphore(proxy, session) for proxy in proxies]

                for coro in asyncio.as_completed(tasks):
                    is_working, result = await coro
                    if is_working:
                        working_proxies.append(result)
                        console.print(f"[green]✓[/green] {result['proxy']} - {result['ip']}")
                    else:
                        console.print(f"[red]✗[/red] {result['proxy']}")

                    progress.advance(task)

        console.print(f"\n[bold green]✅ Working proxies: {len(working_proxies)}/{len(proxies)}[/bold green]")
        return working_proxies

    def scrape_captcha_keys_from_file(self, file_path: str) -> List[str]:
        keys = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and len(line) >= 20:  # Basic validation
                        keys.append(line)
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
        return keys

    async def test_captcha_key(self, key: str, session: aiohttp.ClientSession) -> Tuple[bool, Dict]:
        test_urls = [
            f"https://api.anti-captcha.com/getBalance?clientKey={key}",
            f"https://2captcha.com/res.php?key={key}&action=getbalance",
            f"https://rucaptcha.com/res.php?key={key}&action=getbalance"
        ]
        timeout = aiohttp.ClientTimeout(total=10)
        for url in test_urls:
            try:
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        text = await response.text()
                        if "OK" in text or "balance" in text.lower() or len(text) > 5:
                            return True, {
                                "key": key,
                                "service": urlparse(url).netloc,
                                "response": text[:100]
                            }
            except Exception:
                continue
        return False, {"key": key, "error": "Invalid or expired"}

    async def test_captcha_keys(self, keys: List[str], max_workers: int = 10) -> List[Dict]:
        console.print(f"\n[bold blue]🔐 Testing {len(keys)} captcha keys...[/bold blue]")

        working_keys = []
        semaphore = asyncio.Semaphore(max_workers)

        async def test_with_semaphore(key: str, session: aiohttp.ClientSession):
            async with semaphore:
                return await self.test_captcha_key(key, session)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Testing captcha keys...", total=len(keys))

            async with aiohttp.ClientSession() as session:
                tasks = [test_with_semaphore(key, session) for key in keys]

                for coro in asyncio.as_completed(tasks):
                    is_working, result = await coro
                    if is_working:
                        working_keys.append(result)
                        console.print(f"[green]✓[/green] {result['key'][:20]} - {result['service']}")
                    else:
                        console.print(f"[red]✗[/red] {result['key']}")

                    progress.advance(task)

        console.print(f"\n[bold green]✅ Working captcha keys: {len(working_keys)}/{len(keys)}[/bold green]")
        return working_keys

    async def search_online_sources(self, search_type: str = "proxies") -> List[str]:
        """Automatically search online for new proxy or captcha sources"""
        console.print(f"\n[bold blue]🔍 Auto-searching online for {search_type} sources...[/bold blue]")
        
        discovered_sources = set()
        
        if search_type == "proxies":
            # Use only the most effective search terms to speed up discovery
            search_terms = ["proxy list", "free proxies", "proxies.txt", "proxy.txt"]
        else:
            # Use only the most effective search terms for captcha
            search_terms = ["captcha api key", "2captcha key", "anti-captcha key"]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching online sources...", total=len(search_terms))

            async with aiohttp.ClientSession() as session:
                for term in search_terms:
                    try:
                        # Search GitHub repositories with shorter timeout
                        github_search_url = f"https://github.com/search?q={quote(term)}&type=repositories"
                        timeout = aiohttp.ClientTimeout(total=8)  # Reduced from 15 to 8 seconds
                        
                        async with session.get(github_search_url, timeout=timeout) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Extract repository URLs - simplified patterns
                                repo_patterns = [
                                    r'href="/([^/]+/[^/]+)"',
                                    r'https://github\.com/([^/]+/[^/]+)'
                                ]
                                
                                for pattern in repo_patterns:
                                    matches = re.findall(pattern, content)
                                    # Limit to first 5 matches per pattern to speed up
                                    for match in matches[:5]:
                                        if isinstance(match, tuple):
                                            match = '/'.join(match)
                                        
                                        # Convert to raw GitHub URLs - reduced options
                                        if 'raw.githubusercontent.com' not in match:
                                            potential_sources = [
                                                f"https://raw.githubusercontent.com/{match}/master/proxies.txt",
                                                f"https://raw.githubusercontent.com/{match}/main/proxies.txt",
                                                f"https://raw.githubusercontent.com/{match}/master/proxy.txt",
                                                f"https://raw.githubusercontent.com/{match}/main/proxy.txt"
                                            ]
                                        else:
                                            potential_sources = [f"https://{match}"]
                                        
                                        discovered_sources.update(potential_sources)
                        
                        # Skip paste service searches to speed up (they're slower)
                        
                    except Exception as e:
                        console.print(f"[yellow]⚠[/yellow] Search term '{term}': {str(e)}")
                    
                    progress.advance(task)
                    await asyncio.sleep(0.5)  # Reduced from 1 second to 0.5 seconds

        discovered_list = list(discovered_sources)
        # Limit total discovered sources to prevent excessive validation
        discovered_list = discovered_list[:20]  # Limit to 20 sources max
        console.print(f"\n[bold green]✅ Discovered {len(discovered_list)} potential {search_type} sources[/bold green]")
        return discovered_list

    async def validate_discovered_sources(self, sources: List[str], source_type: str) -> List[str]:
        """Validate discovered sources by checking if they return valid content"""
        console.print(f"\n[bold blue]🔍 Validating discovered {source_type} sources...[/bold blue]")
        
        valid_sources = []
        
        # Limit sources to validate to speed up the process
        sources_to_validate = sources[:15]  # Only validate first 15 sources
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Validating sources...", total=len(sources_to_validate))

            async with aiohttp.ClientSession() as session:
                # Use semaphore to limit concurrent requests
                semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
                
                async def validate_single_source(source: str) -> Tuple[str, bool]:
                    async with semaphore:
                        try:
                            timeout = aiohttp.ClientTimeout(total=5)  # Reduced from 10 to 5 seconds
                            async with session.get(source, timeout=timeout) as response:
                                if response.status == 200:
                                    content = await response.text()
                                    
                                    # Check if content contains relevant data
                                    if source_type == "proxies":
                                        # Look for IP:PORT patterns
                                        proxy_matches = re.findall(r'(?:\d{1,3}\.){3}\d{1,3}:\d+', content)
                                        if len(proxy_matches) > 0:
                                            return source, True
                                    else:  # captcha
                                        # Look for potential captcha keys
                                        key_matches = []
                                        for pattern in self.captcha_patterns:
                                            matches = re.findall(pattern, content)
                                            key_matches.extend(matches)
                                        
                                        if len(key_matches) > 0:
                                            return source, True
                                
                        except Exception:
                            pass
                        return source, False
                
                # Validate sources in parallel
                tasks = [validate_single_source(source) for source in sources_to_validate]
                
                for coro in asyncio.as_completed(tasks):
                    source, is_valid = await coro
                    if is_valid:
                        valid_sources.append(source)
                        console.print(f"[green]✓[/green] {source}")
                    else:
                        console.print(f"[red]✗[/red] {source}")
                    
                    progress.advance(task)

        console.print(f"\n[bold green]✅ Validated {len(valid_sources)} working {source_type} sources[/bold green]")
        return valid_sources

    def save_discovered_sources(self, source_type: str):
        """Save discovered sources to a file for future use"""
        downloads_folder = self.get_downloads_folder()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if source_type == "proxies":
            filename = f"grass_discovered_proxy_sources_{timestamp}.json"
            sources = self.proxy_sources
        else:
            filename = f"grass_discovered_captcha_sources_{timestamp}.json"
            sources = self.captcha_sources
        
        filepath = downloads_folder / filename
        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "source_type": source_type,
                    "total_sources": len(sources),
                    "sources": sources
                }, f, indent=2)
            console.print(f"[green]✅ Discovered {source_type} sources saved to: {filepath}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving discovered sources: {e}[/red]")

    def load_discovered_sources(self, filepath: str) -> bool:
        """Load previously discovered sources from a file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            source_type = data.get("source_type", "")
            sources = data.get("sources", [])
            
            if source_type == "proxies":
                self.proxy_sources.extend(sources)
                console.print(f"[green]✅ Loaded {len(sources)} proxy sources from {filepath}[/green]")
            elif source_type == "captcha":
                self.captcha_sources.extend(sources)
                console.print(f"[green]✅ Loaded {len(sources)} captcha sources from {filepath}[/green]")
            
            return True
        except Exception as e:
            console.print(f"[red]Error loading discovered sources: {e}[/red]")
            return False

    async def auto_discover_and_add_sources(self, source_type: str = "proxies", fast_mode: bool = True) -> List[str]:
        """Automatically discover, validate, and add new sources"""
        console.print(f"\n[bold magenta]🚀 Auto-discovering new {source_type} sources...[/bold magenta]")
        
        if fast_mode:
            console.print("[yellow]⚡ Fast mode enabled - limited sources for speed[/yellow]")
        
        # Search for new sources
        discovered_sources = await self.search_online_sources(source_type)
        
        if not discovered_sources:
            console.print(f"[yellow]No new {source_type} sources discovered[/yellow]")
            return []
        
        # Validate discovered sources
        valid_sources = await self.validate_discovered_sources(discovered_sources, source_type)
        
        if valid_sources:
            # Add new sources to the main list
            if source_type == "proxies":
                self.proxy_sources.extend(valid_sources)
                console.print(f"[green]✅ Added {len(valid_sources)} new proxy sources[/green]")
            else:
                self.captcha_sources.extend(valid_sources)
                console.print(f"[green]✅ Added {len(valid_sources)} new captcha sources[/green]")
            
            # Ask if user wants to save discovered sources
            save_sources = Confirm.ask(f"\nSave discovered {source_type} sources to Downloads folder?")
            if save_sources:
                self.save_discovered_sources(source_type)
        
        return valid_sources

    def save_results(self, filename: Optional[str] = None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"grass_scraper_results_{timestamp}.json"
        results = {
            "timestamp": datetime.now().isoformat(),
            "working_proxies": self.working_proxies,
            "working_captcha_keys": self.working_captcha_keys,
            "failed_proxies": self.failed_proxies,
            "failed_captcha_keys": self.failed_captcha_keys,
            "test_results": self.test_results
        }

        try:
            downloads_folder = self.get_downloads_folder()
            with open(downloads_folder / filename, 'w') as f:
                json.dump(results, f, indent=2)
            console.print(f"[green]✅ Results saved to: {downloads_folder / filename}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving results: {e}[/red]")

    def save_proxies_to_downloads(self, proxies: Sequence[Union[str, Dict]], format_type: str = "txt"):
        """Save proxies to Downloads folder in specified format"""
        downloads_folder = self.get_downloads_folder()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "txt":
            filename = f"grass_proxies_{timestamp}.txt"
            filepath = downloads_folder / filename
            try:
                with open(filepath, 'w') as f:
                    for proxy in proxies:
                        if isinstance(proxy, dict) and 'proxy' in proxy:
                            f.write(f"{proxy['proxy']}\n")
                        elif isinstance(proxy, str):
                            f.write(f"{proxy}\n")
                console.print(f"[green]✅ Proxies saved to: {filepath}[/green]")
            except Exception as e:
                console.print(f"[red]Error saving proxies: {e}[/red]")
        
        elif format_type == "json":
            filename = f"grass_proxies_{timestamp}.json"
            filepath = downloads_folder / filename
            try:
                with open(filepath, 'w') as f:
                    json.dump(list(proxies), f, indent=2)
                console.print(f"[green]✅ Proxies saved to: {filepath}[/green]")
            except Exception as e:
                console.print(f"[red]Error saving proxies: {e}[/red]")

    def save_captcha_keys_to_downloads(self, keys: Sequence[Union[str, Dict]], format_type: str = "txt"):
        """Save captcha keys to Downloads folder in specified format"""
        downloads_folder = self.get_downloads_folder()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "txt":
            filename = f"grass_captcha_keys_{timestamp}.txt"
            filepath = downloads_folder / filename
            try:
                with open(filepath, 'w') as f:
                    for key in keys:
                        if isinstance(key, dict) and 'key' in key:
                            f.write(f"{key['key']}\n")
                        elif isinstance(key, str):
                            f.write(f"{key}\n")
                console.print(f"[green]✅ Captcha keys saved to: {filepath}[/green]")
            except Exception as e:
                console.print(f"[red]Error saving captcha keys: {e}[/red]")
        
        elif format_type == "json":
            filename = f"grass_captcha_keys_{timestamp}.json"
            filepath = downloads_folder / filename
            try:
                with open(filepath, 'w') as f:
                    json.dump(list(keys), f, indent=2)
                console.print(f"[green]✅ Captcha keys saved to: {filepath}[/green]")
            except Exception as e:
                console.print(f"[red]Error saving captcha keys: {e}[/red]")

    def load_from_files(self):
        console.print("\n[bold blue]📁 Loading from files...[/bold blue]")

        # List .txt files in current directory
        txt_files = [f for f in os.listdir(".") if f.endswith(".txt")]

        if not txt_files:
            console.print("[yellow]No .txt files found in current directory[/yellow]")
            return

        console.print(f"\n[bold]Available .txt files:[/bold]")
        for i, file in enumerate(txt_files, 1):
            console.print(f"{i}. {file}")

        try:
            choices = [str(i) for i in range(1, len(txt_files) + 1)]
            choice = Prompt.ask("\nSelect file number", choices=choices)
            selected_file = txt_files[int(choice) - 1]

            file_type = Prompt.ask("File type", choices=["proxies", "captcha_keys"])

            if file_type == "proxies":
                proxies = []
                with open(selected_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and ':' in line:
                            proxies.append(line)
                console.print(f"[green]Loaded {len(proxies)} proxies from {selected_file}[/green]")
                return proxies
            else:
                keys = self.scrape_captcha_keys_from_file(selected_file)
                console.print(f"[green]Loaded {len(keys)} captcha keys from {selected_file}[/green]")
                return keys

        except Exception as e:
            console.print(f"[red]Error loading file: {e}[/red]")
            return []

    def show_results(self):
        console.print("\n[bold blue]📊 Current Results:[/bold blue]")

        results_table = Table(title="Test Results Summary")
        results_table.add_column("Category", style="cyan")
        results_table.add_column("Count", style="green")
        results_table.add_column("Details", style="white")

        results_table.add_row(
            "Working Proxies", str(len(self.working_proxies)),
            f"Last tested: {len(self.working_proxies)} proxies"
        )

        results_table.add_row(
            "Working Captcha Keys", str(len(self.working_captcha_keys)),
            f"Last tested: {len(self.working_captcha_keys)} keys"
        )

        results_table.add_row(
            "Failed Proxies", str(len(self.failed_proxies)),
            "Failed validation"
        )

        results_table.add_row(
            "Failed Captcha Keys", str(len(self.failed_captcha_keys)),
            "Invalid or expired"
        )

        console.print(results_table)

    async def run(self):
        while True:
            console.clear()
            console.print(self.create_header())
            console.print(self.create_menu())

            try:
                choices = [str(i) for i in range(1, 11)]
                choice = Prompt.ask("\n[bold cyan]Select an option[/bold cyan]", choices=choices)

                if choice == "1":  # Scrape Proxies
                    console.print("\n[bold blue]🔍 Proxy Scraping Options:[/bold blue]")
                    console.print("1. Use existing sources")
                    console.print("2. Auto-discover new sources first (fast)")
                    console.print("3. Use existing + auto-discover (fast)")
                    proxy_choice = Prompt.ask("Select option", choices=["1", "2", "3"])
                    
                    if proxy_choice == "2":
                        # Auto-discover first, then scrape
                        discovered = await self.auto_discover_and_add_sources("proxies", fast_mode=True)
                        if discovered:
                            console.print("[green]✅ New sources discovered and added![/green]")
                    
                    elif proxy_choice == "3":
                        # Auto-discover and add to existing sources
                        discovered = await self.auto_discover_and_add_sources("proxies", fast_mode=True)
                        if discovered:
                            console.print("[green]✅ New sources added to existing list![/green]")
                    
                    # Now scrape with all available sources
                    proxies = await self.scrape_proxies()
                    if proxies:
                        test_now = Confirm.ask("\nTest proxies now?")
                        if test_now:
                            self.working_proxies = await self.test_proxies(proxies)
                        else:
                            console.print(f"[yellow]Proxies saved for later testing[/yellow]")

                elif choice == "2":  # Scrape Captcha Keys
                    console.print("\n[bold blue]🔑 Captcha Key Sources:[/bold blue]")
                    console.print("1. Scrape from internet")
                    console.print("2. Load from file")
                    console.print("3. Enter manually")
                    console.print("4. Auto-discover sources first (fast)")
                    key_choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"])

                    if key_choice == "1":
                        keys = await self.scrape_captcha_keys()
                        if keys:
                            test_now = Confirm.ask("\nTest captcha keys now?")
                            if test_now:
                                self.working_captcha_keys = await self.test_captcha_keys(keys)
                            else:
                                console.print(f"[yellow]Captcha keys saved for later testing[/yellow]")
                    elif key_choice == "2":
                        keys = self.load_from_files()
                        if keys:
                            test_now = Confirm.ask("\nTest captcha keys now?")
                            if test_now:
                                self.working_captcha_keys = await self.test_captcha_keys(keys)
                            else:
                                console.print(f"[yellow]Captcha keys saved for later testing[/yellow]")
                    elif key_choice == "3":
                        key_input = Prompt.ask("Enter captcha keys (comma-separated)")
                        keys = [k.strip() for k in key_input.split(",") if k.strip()]
                        if keys:
                            test_now = Confirm.ask("\nTest captcha keys now?")
                            if test_now:
                                self.working_captcha_keys = await self.test_captcha_keys(keys)
                            else:
                                console.print(f"[yellow]Captcha keys saved for later testing[/yellow]")
                    elif key_choice == "4":
                        # Auto-discover first, then scrape
                        discovered = await self.auto_discover_and_add_sources("captcha", fast_mode=True)
                        if discovered:
                            console.print("[green]✅ New captcha sources discovered and added![/green]")
                            keys = await self.scrape_captcha_keys()
                            if keys:
                                test_now = Confirm.ask("\nTest captcha keys now?")
                                if test_now:
                                    self.working_captcha_keys = await self.test_captcha_keys(keys)
                                else:
                                    console.print(f"[yellow]Captcha keys saved for later testing[/yellow]")

                elif choice == "3":  # Test Proxies
                    if not self.working_proxies:
                        console.print("[yellow]No proxies to test. Scrape some first![/yellow]")
                    else:
                        max_workers = Prompt.ask("Max concurrent tests", default="50")
                        self.working_proxies = await self.test_proxies(
                            [p['proxy'] if isinstance(p, dict) else p for p in self.working_proxies],
                            int(max_workers)
                        )

                elif choice == "4":  # Test Captcha Keys
                    if not self.working_captcha_keys:
                        console.print("[yellow]No captcha keys to test. Load some first![/yellow]")
                    else:
                        max_workers = Prompt.ask("Max concurrent tests", default="10")
                        self.working_captcha_keys = await self.test_captcha_keys(
                            [k['key'] if isinstance(k, dict) else k for k in self.working_captcha_keys],
                            int(max_workers)
                        )

                elif choice == "5":  # View Results
                    self.show_results()

                elif choice == "6":  # Save Results
                    filename = Prompt.ask("Filename (optional)")
                    self.save_results(filename)

                elif choice == "7":  # Load from Files
                    self.load_from_files()

                elif choice == "8":  # Save to Downloads
                    save_type = Prompt.ask("Save type", choices=["proxies", "captcha_keys"])
                    if save_type == "proxies":
                        proxies_to_save = self.working_proxies + self.failed_proxies
                        self.save_proxies_to_downloads(proxies_to_save)
                    else:
                        keys_to_save = self.working_captcha_keys + self.failed_captcha_keys
                        self.save_captcha_keys_to_downloads(keys_to_save)

                elif choice == "9":  # Auto-Discover Sources
                    source_type = Prompt.ask("Source type to discover", choices=["proxies", "captcha_keys"])
                    fast_mode = Confirm.ask("Enable fast mode (limited sources for speed)?")
                    discovered_sources = await self.auto_discover_and_add_sources(source_type, fast_mode)
                    if discovered_sources:
                        console.print(f"[green]✅ Added {len(discovered_sources)} new {source_type} sources from discovery[/green]")
                    else:
                        console.print(f"[yellow]No new {source_type} sources discovered or added[/yellow]")

                elif choice == "10":  # Exit
                    console.print("\n[bold green]🌱 Thanks for using GRASS Scraper! 🌱[/bold green]")
                    self._save_last_used_sources()
                    break

                if choice != "10":
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                console.print("\n[bold red]Interrupted by user[/bold red]")
                self._save_last_used_sources()
                break
            except Exception as e:
                console.print(f"\n[bold red]Error: {e}[/bold red]")
                input("Press Enter to continue...")

def main():
    try:
        scraper = ProxyCaptchaScraper()
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        console.print("\n[bold red]Goodbye![/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]")
        console.print_exception()

if __name__ == "__main__":
    main() 